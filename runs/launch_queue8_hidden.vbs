' Runs launch_queue8_run.cmd (queue8.sh -> uttt.train2 deep10_c1_300_lr150 -> eval_run.sh) with NO console window
' (style 0): a visible console can be closed by hand, and closing it ends every process attached to it (that is how
' the D1 relaunch of 2026-09-04 19:00 died). Watch: python tools/run_status.py runs/deep10_c1_300_lr150; events:
' bash runs/watch_train.sh deep10_c1_300_lr150 queue8. Stop for real: end the "bash queue8.sh" wrapper first (it would
' otherwise resume the trainer after 60 s), then uttt.train2.
Set sh = CreateObject("WScript.Shell")
sh.Run """C:\Users\John Peponis\Desktop\uttt-zero\runs\launch_queue8_run.cmd""", 0, False
