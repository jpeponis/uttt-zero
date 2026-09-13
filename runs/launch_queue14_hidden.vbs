' K1 (PLAN7 §5): runs launch_queue14_run.cmd (queue14.sh -> uttt.train2 --rule draw -> eval_run_k1.sh) with NO console
' window (style 0), so a stray black window cannot be closed by hand (the 2026-09-04 19:00 restart died that way: a
' console close / Ctrl-C reaches every process attached to the console, exit code 0xC000013A).
' NOT TO BE RUN BEFORE THE OWNER APPROVES K1. Watch it with: python tools/run_status.py runs/deep8_c1_300_e8_draw
' Stop it for real: end the "bash queue14.sh" wrapper first (else it resumes the trainer), then uttt.train2.
Set sh = CreateObject("WScript.Shell")
sh.Run """C:\Users\John Peponis\Desktop\uttt-zero\runs\launch_queue14_run.cmd""", 0, False
