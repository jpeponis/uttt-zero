. "$env:USERPROFILE\.codex\codex-functions.ps1"
Set-Location "C:\Users\John Peponis\Desktop\uttt-zero"
$d = "docs\reviews\M1_account"
$t0 = Get-Date
$head = (git rev-parse --short HEAD).Trim()
"START $($t0.ToString('s')) pid=$PID (M1: prompt points at the brief; stdin redirected from an empty file) at $head" | Set-Content "$d\status.txt"
$prompt = "Your complete brief is the file docs/reviews/M1_account/brief.md in this repository, whose working tree is at commit $head. Read it first and follow it exactly; it is the whole task. Deliver the review as your final message."
codex-sp exec -s read-only --json -o "$d\REVIEW.md" $prompt 1> "$d\events.jsonl" 2> "$d\stderr.txt"
"EXIT $LASTEXITCODE $((Get-Date).ToString('s')) elapsed=$([int]((Get-Date)-$t0).TotalSeconds)s" | Add-Content "$d\status.txt"
