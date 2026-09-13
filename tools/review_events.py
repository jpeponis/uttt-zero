"""Summarise a `codex exec --json` event stream: what the reviewer ran, and what it said in its own voice.
Usage: review_events.py events.jsonl [tail=12]. Command outputs (file dumps) are counted, not printed."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
path = sys.argv[1]; tail = int(sys.argv[2]) if len(sys.argv) > 2 else 12; W = 240
types = collections.Counter(); cmds = []; said = []; out_bytes = 0
for line in open(path, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line: continue
    try: ev = json.loads(line)
    except Exception: continue
    t = ev.get("type", "?"); it = ev.get("item") or {}
    itype = it.get("type", "")
    types[f"{t}/{itype}" if itype else t] += 1
    if t != "item.completed": continue
    if itype == "command_execution":
        c = " ".join(str(it.get("command", "")).split())
        c = c.replace('"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -NoProfile -Command ', 'pwsh> ')
        cmds.append(f"{c[:W]}  [exit {it.get('exit_code', '?')}]")
        out_bytes += len(str(it.get("aggregated_output", "")))
    elif itype in ("agent_message", "reasoning", "assistant_message"):
        txt = it.get("text") or it.get("message") or ""
        if isinstance(txt, list): txt = " ".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in txt)
        txt = " ".join(str(txt).split())
        if txt: said.append(f"[{itype}] {txt[:W]}")
    else:
        said.append(f"[{itype}] " + " ".join(json.dumps(it)[:W].split()))
print("EVENT TYPES:", dict(types))
print(f"\nCOMMANDS ({len(cmds)}; {out_bytes/1024:.0f} KB of output read), last {tail}:"); print("\n".join(cmds[-tail:]))
print(f"\nREVIEWER'S OWN TEXT ({len(said)}), last {tail}:"); print("\n".join(said[-tail:]) if said else "(none yet — it is still reading)")
