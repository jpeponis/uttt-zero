' Runs launch_queue7_run.cmd (queue7.sh -> uttt.train2 -> eval_run.sh) with NO console window (style 0), so a
' stray black window cannot be closed by hand - the 2026-09-04 19:00 restart died exactly that way (a console
' close / Ctrl-C reaches every process attached to the console: exit code 0xC000013A).
' Watch it with: python tools/run_status.py runs/deep10_c1_300_s1
' Stop it for real: end the "bash queue7.sh" wrapper first (else it resumes the trainer), then uttt.train2.
Set sh = CreateObject("WScript.Shell")
sh.Run """C:\Users\John Peponis\Desktop\uttt-zero\runs\launch_queue7_run.cmd""", 0, False
