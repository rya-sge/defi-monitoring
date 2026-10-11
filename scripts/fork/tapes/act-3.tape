# vhs tape (https://github.com/charmbracelet/vhs) for act 3 of the fork crisis (docs/analysis/FORK-PRESENTATION.md §6).
# Run from the repository root, with the fork started and the acts before this one played:
#   vhs scripts/fork/tapes/act-3.tape        → out/video/act-3.mp4 (git-ignored)
Output out/video/act-3.mp4
Require cast
Set Shell "bash"
Set FontSize 20
Set Width 1600
Set Height 900
Set Padding 24
Set TypingSpeed 35ms
Set Theme "Builtin Dark"

Hide
Type "export PAUSE=6 RISKDEP_RPC_URL=http://127.0.0.1:8545 RISKDEP_FORK=1 && clear"
Enter
Show
Type "scripts/fork/crisis-belem.sh --act 3"
Sleep 600ms
Enter
Sleep 25s
