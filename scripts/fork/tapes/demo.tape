# vhs tape (https://github.com/charmbracelet/vhs): the whole demo in one take, through scripts/fork/demo.sh.
# Run from the repository root:  vhs scripts/fork/tapes/demo.tape   → out/video/demo.mp4 (git-ignored)
# Without vhs, `scripts/fork/demo.sh --record` records the same with asciinema.
Output out/video/demo.mp4
Require cast
Require uv
Set Shell "bash"
Set FontSize 16
Set Width 1800
Set Height 1000
Set Padding 24
Set TypingSpeed 35ms
Set Theme "Builtin Dark"

Hide
Type "clear"
Enter
Show
Type "scripts/fork/demo.sh"
Sleep 600ms
Enter
Sleep 300s
