# vhs tape: the watch's side of the crisis, replayed offline from fixtures/replay/fork-belem/ (no fork needed).
# Run from the repository root:  vhs scripts/fork/tapes/watch-replay.tape   → out/video/watch-replay.mp4
Output out/video/watch-replay.mp4
Set Shell "bash"
Set FontSize 16
Set Width 1600
Set Height 900
Set Padding 24
Set TypingSpeed 35ms
Set Theme "Builtin Dark"

Hide
Type "clear"
Enter
Show
Type "uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --replay --record-as fork-belem --level warn"
Sleep 600ms
Enter
Sleep 30s
