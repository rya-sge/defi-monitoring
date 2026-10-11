#!/usr/bin/env bash
# The whole fork demo in one command and one terminal (docs/analysis/FORK-PRESENTATION.md): builds the demo contracts,
# starts a mainnet fork, starts `riskdep watch` on the Belem vault in the background, plays the crisis act by act and
# prints, under each act, what riskdep saw. Stops everything at the end.
#
#   scripts/fork/demo.sh                    the full demo (≈ 4 min), pausing 4 s between steps
#   scripts/fork/demo.sh --manual           wait for Enter between steps (presenting live)
#   scripts/fork/demo.sh --fast             skip act 1 (the two predictions, ≈ 1.5 min)
#   scripts/fork/demo.sh --record           the same, recorded with asciinema to out/video/demo.cast
#   scripts/fork/demo.sh --block N          fork at block N (default 26165572, where the facts were checked)
#
# Needs Foundry and uv; --record needs asciinema (sudo apt install asciinema).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"

BLOCK=26165572
ACTS=(0 1 2 3 4 5 6 7)
RECORD=""
export PAUSE="${PAUSE:-4}"
ARGS=("$@")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manual) unset PAUSE ;;
    --fast) ACTS=(0 2 3 4 5 6 7) ;;
    --record) RECORD=1 ;;
    --block) BLOCK="$2"; shift ;;
    *) sed -n 2,12p "$0"; exit 2 ;;
  esac
  shift
done

if [[ -n "$RECORD" ]]; then
  command -v asciinema >/dev/null || fail "--record needs asciinema: sudo apt install asciinema"
  mkdir -p "$ROOT/out/video"
  rest=()
  for a in "${ARGS[@]}"; do [[ "$a" == --record ]] || rest+=("$a"); done
  asciinema rec --overwrite -q -c "$0 ${rest[*]}" "$ROOT/out/video/demo.cast"
  say "recorded: out/video/demo.cast  (play: asciinema play out/video/demo.cast; gif: agg out/video/demo.cast demo.gif)"
  exit 0
fi

LOG="$ROOT/out/demo/watch.log"
mkdir -p "$ROOT/out/demo"
: >"$LOG"
WATCH_PID="" TAIL_PID=""
cleanup() {
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  [[ -n "$WATCH_PID" ]] && kill "$WATCH_PID" 2>/dev/null || true
  "$HERE/start-fork.sh" --stop >/dev/null 2>&1 || true
}
trap cleanup EXIT

# what riskdep prints, as it prints it: alerts only, marked, info kept for the lines that tell the story
show_watch() {
  tail -n0 -F "$LOG" 2>/dev/null | stdbuf -oL grep -E --line-buffered '^(CRITICAL|WARN|INFO) ' \
    | stdbuf -oL grep -Ev --line-buffered '^INFO .*(Deallocate|Allocate|shares moved|Your withdraw|Your deposit)' \
    | while IFS= read -r line; do
        case "$line" in
          CRITICAL*) printf '\033[1;31m  riskdep ▸ %s\033[0m\n' "$line" ;;
          WARN*) printf '\033[33m  riskdep ▸ %s\033[0m\n' "$line" ;;
          *) printf '\033[2m  riskdep ▸ %s\033[0m\n' "$line" ;;
        esac
      done
}

# the watch is caught up when its last batch reaches the fork's head minus its 2 confirmations
caught_up() {
  local head last
  head="$(cast block-number --rpc-url "$R")"
  last="$(grep -oE '^·[[:space:]]+#[0-9]+–[0-9]+' "$LOG" | tail -1 | grep -oE '[0-9]+$' || echo 0)"
  [[ "${last:-0}" -ge $((head - 2)) ]]
}
wait_watch() {
  for _ in $(seq 1 90); do caught_up && { sleep 1; return; }; sleep 1; done
  say "(riskdep has not caught up after 90 s; see out/demo/watch.log)"
}

caption "riskdep — a crisis on a mainnet fork"
say "building the demo contracts and forking Ethereum mainnet at block $BLOCK…"
(cd "$HERE" && forge build >/dev/null 2>&1) || fail "forge build failed in scripts/fork/"
"$HERE/start-fork.sh" "$BLOCK" | grep -E '^fork at' | sed 's/^/  /'

say "starting riskdep watch on the Belem RWA EURCV vault (one block per batch, polling every 2 s)…"
(cd "$ROOT" && exec uv run python -m riskdep watch --vault "$VAULT" --step 1 --poll 2 --out "$ROOT/out/demo" >"$LOG" 2>&1) &
WATCH_PID=$!
show_watch &
TAIL_PID=$!
for _ in $(seq 1 180); do
  grep -q 'cross-check Morpho API' "$LOG" && break
  kill -0 "$WATCH_PID" 2>/dev/null || { cat "$LOG" >&2; fail "riskdep watch stopped"; }
  sleep 1
done
sleep 1
pause

for n in "${ACTS[@]}"; do
  DEMO=1 "$HERE/crisis-belem.sh" --act "$n"
  wait_watch
  pause
done

caption "End — what riskdep said, by level"
grep -cE '^CRITICAL ' "$LOG" | xargs -I{} printf '\033[1;31m  %s critical\033[0m\n' {}
grep -cE '^WARN ' "$LOG" | xargs -I{} printf '\033[33m  %s warn\033[0m\n' {}
say "full log: out/demo/watch.log · alerts as JSON: out/demo/watch-${VAULT,,}.jsonl"
say "the same run, offline: uv run python -m riskdep watch --vault $VAULT --replay --record-as fork-belem"
