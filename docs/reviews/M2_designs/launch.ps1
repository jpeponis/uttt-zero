. "$env:USERPROFILE\.codex\codex-functions.ps1"
Set-Location "C:\Users\John Peponis\Desktop\uttt-zero"
$d = "docs\reviews\M2_designs"
$t0 = Get-Date
"START $($t0.ToString('s')) pid=$PID (M2: prompt points at the brief; stdin redirected from an empty file)" | Set-Content "$d\status.txt"
$prompt = "Your complete brief is the file docs/reviews/M2_designs/brief.md in this repository. Read it first and follow it exactly; it is the whole task. Deliver the review as your final message."
codex-sp exec -s read-only --json -o "$d\REVIEW.md" $prompt 1> "$d\events.jsonl" 2> "$d\stderr.txt"
"EXIT $LASTEXITCODE $((Get-Date).ToString('s')) elapsed=$([int]((Get-Date)-$t0).TotalSeconds)s" | Add-Content "$d\status.txt"
