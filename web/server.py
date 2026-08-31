"""Local web UI for playing against and analysing a trained net (PLAN2 §5 step 8).

    .venv/Scripts/python.exe web/server.py runs/v2b/net_0150.pt --sims 800 --port 8765 --device cuda:1

Then open http://localhost:8765/. One game at a time (single-process, single search object). JSON API:
  GET  /api/state                    current position, legal moves, history, result
  POST /api/new    {human, sims}     new game; human = "X" | "O" | "none" (analysis only: you move both sides)
  POST /api/move   {move}            play a move (engine index 0-80); the agent replies if it is its turn
  POST /api/undo                     take back the last ply (two plies when playing the agent)
  POST /api/analyse {sims}           raw policy, WDL, search visits/Q per move, principal variation, root value
  POST /api/agent                    let the agent move now (also used for "none" mode)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT, encode  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


class Engine:
    def __init__(self, ckpt: str, device: str, sims: int) -> None:
        self.device = torch.device(device)
        self.net = load_checkpoint(ckpt, self.device)
        self.fe = FusedEvaluator(self.net, self.device)
        self.ckpt = ckpt
        self.searches: dict[int, BatchedSearch] = {}
        self.lock = threading.Lock()
        self.new_game("X", sims)

    def search_for(self, sims: int) -> BatchedSearch:
        if sims not in self.searches:
            cfg = SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0, m_considered=81, root_prior_floor=0.03,
                               cuda_graph=self.device.type == "cuda", depth_cap=min(sims, 40))
            self.searches[sims] = BatchedSearch(self.fe, 1, cfg, self.device)
        return self.searches[sims]

    def new_game(self, human: str, sims: int) -> None:
        self.game = UTTT()
        self.history: list[int] = []
        self.human = human
        self.sims = int(sims)

    def batch(self) -> BatchUTTT:
        b = BatchUTTT(1, self.device)
        for m in self.history:
            b.step(torch.tensor([m], device=self.device))
        return b

    @torch.no_grad()
    def analyse(self, sims: int | None = None) -> dict:
        g = self.game
        if g.done:
            return {"done": True}
        b = self.batch()
        sims = int(sims or self.sims)
        s = self.search_for(sims)
        r = s.search(b.cells, b.macro, b.next_board, b.player, b.done, b.winner, selfplay=False)
        obs = encode(b.cells, b.macro, b.next_board, b.player, b.done, extra=self.net.cfg.extra_planes)
        p_logits, v_logits, *_ = self.net(obs)
        from uttt.batch import INV_PERM

        legal = torch.from_numpy(g.legal_mask()).to(self.device)
        pl = p_logits.float()[0, INV_PERM.to(self.device)].masked_fill(~legal, float("-inf"))
        raw_policy = torch.softmax(pl, 0).cpu().numpy()
        wdl = torch.softmax(v_logits.float(), 1)[0].cpu().numpy()
        N = s.N[0, 0].cpu().numpy()
        Q = (s.W[0, 0] / s.N[0, 0].clamp(min=1)).cpu().numpy()
        # principal variation: most visited child chain
        pv, node = [], 0
        Nn, ch = s.N[0].cpu().numpy(), s.children[0].cpu().numpy()
        while len(pv) < 12 and Nn[node].max() > 0:
            a = int(Nn[node].argmax())
            pv.append(a)
            node = int(ch[node, a])
            if node < 0:
                break
        return {"done": False, "sims": sims, "root_value": float(r.root_value[0]), "raw_value": float(r.raw_value[0]),
                "wdl": [float(x) for x in wdl], "best": int(r.action[0]), "pv": pv,
                "moves": [{"m": int(m), "n": int(N[m]), "q": float(Q[m]), "p": float(raw_policy[m])} for m in np.flatnonzero(N > 0)],
                "policy": [float(x) for x in raw_policy]}

    def agent_move(self) -> int | None:
        if self.game.done:
            return None
        a = self.analyse()
        m = a["best"]
        self.play(m)
        return m

    def play(self, m: int) -> None:
        self.game.play(int(m))
        self.history.append(int(m))

    def undo(self, plies: int) -> None:
        h = self.history[: max(0, len(self.history) - plies)]
        self.new_game(self.human, self.sims)
        for m in h:
            self.play(m)

    def state(self) -> dict:
        g = self.game
        return {"cells": g.cells.tolist(), "macro": g.macro.tolist(), "next_board": g.next_board, "player": g.player,
                "legal": g.legal_moves(), "history": self.history, "done": g.done, "winner": g.winner, "end_reason": g.end_reason,
                "human": self.human, "sims": self.sims, "net": self.ckpt, "move_count": g.move_count}


ENGINE: Engine


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # quiet
        pass

    def _json(self, obj, code=200) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/state":
            with ENGINE.lock:
                self._json(ENGINE.state())
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        body = self._body()
        try:
            with ENGINE.lock:
                if self.path == "/api/new":
                    ENGINE.new_game(body.get("human", "X"), body.get("sims", ENGINE.sims))
                    agent = ENGINE.agent_move() if ENGINE.human == "O" else None
                    self._json({"state": ENGINE.state(), "agent": agent})
                elif self.path == "/api/move":
                    m = int(body["move"])
                    if not ENGINE.game.legal_mask()[m]:
                        return self._json({"error": "illegal move"}, 400)
                    ENGINE.play(m)
                    agent = None
                    if ENGINE.human in ("X", "O") and not ENGINE.game.done:
                        agent = ENGINE.agent_move()
                    self._json({"state": ENGINE.state(), "agent": agent})
                elif self.path == "/api/undo":
                    ENGINE.undo(2 if ENGINE.human in ("X", "O") else 1)
                    self._json({"state": ENGINE.state()})
                elif self.path == "/api/analyse":
                    self._json(ENGINE.analyse(body.get("sims")))
                elif self.path == "/api/agent":
                    self._json({"state": ENGINE.state(), "agent": ENGINE.agent_move()})
                else:
                    self._json({"error": "not found"}, 404)
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)


def main() -> None:
    global ENGINE
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", nargs="?", default="runs/v2b/net_0150.pt")
    ap.add_argument("--sims", type=int, default=800)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    ENGINE = Engine(a.checkpoint, a.device, a.sims)
    ENGINE.analyse(a.sims)  # warm up: CUDA-graph capture for the default budget (a first search at a new budget takes ~10 s)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"uttt-zero web UI: http://localhost:{a.port}/  ({a.checkpoint}, {a.sims} sims, {a.device})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
