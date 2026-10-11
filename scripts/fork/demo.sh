#!/usr/bin/env bash
# The whole fork demo in one command and one terminal (docs/analysis/FORK-PRESENTATION.md): builds the demo contracts,
# starts a mainnet fork, starts `riskdep watch` on the Belem vault in the background, plays the crisis act by act and
# prints, under each act, what riskdep saw. Stops everything at the end.
#
#   scripts/fork/demo.sh                    the full demo (≈ 4 min), pausing 4 s between steps
#   scripts/fork/demo.sh --manual           wait for Enter between steps (presenting live)
#   scripts/fork/demo.sh --fast             skip act 1 (the two predictions, ≈ 1.5 min)
#   scripts/fork/demo.sh --short            the 1.5–2 min cut: prediction (offline), markdown, timelocked upgrade,
#                                           bad debt; the prediction plays while riskdep starts up
#   scripts/fork/demo.sh --record           the same, recorded with asciinema to out/video/demo.cast
#   scripts/fork/demo.sh --block N          fork at block N (default 26165572, where the facts were checked)
#   scripts/fork/demo.sh --stop             stop a running demo from another terminal: the demo, its watch, the fork
#
# Ctrl-C stops it too, and cleans up the same way (Ctrl-Z only suspends it: then use --stop). One demo at a time: a second one refuses to start.
# Needs Foundry and uv; --record needs asciinema (sudo apt install asciinema).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"

BLOCK=26165572
ACTS=(0 1 2 3 4 5 6 7)
RECORD=""
STOP=""
PAUSE_SET="${PAUSE:-}"
export PAUSE="${PAUSE:-4}"
ARGS=("$@")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manual) unset PAUSE ;;
    --fast) ACTS=(0 2 3 4 5 6 7) ;;
    --short) ACTS=(0 1 2 6 7); export SHORT=1 PAUSE="${PAUSE_SET:-2}" ;;
    --record) RECORD=1 ;;
    --block) BLOCK="$2"; shift ;;
    --stop) STOP=1 ;;
    *) sed -n 2,12p "$0"; exit 2 ;;
  esac
  shift
done

PIDS="$ROOT/out/demo"
mkdir -p "$PIDS"

# --stop: the demo (its trap stops the rest), then whatever outlived it: the watch and its python, the printer, the fork
if [[ -n "$STOP" ]]; then
  for f in demo watch; do
    if [[ -f "$PIDS/$f.pid" ]]; then
      p="$(cat "$PIDS/$f.pid")"
      pkill -TERM -P "$p" 2>/dev/null || true; pkill -CONT -P "$p" 2>/dev/null || true
      kill -TERM "$p" 2>/dev/null && say "stopped the $f (pid $p)"
      kill -CONT "$p" 2>/dev/null || true  # a suspended process (Ctrl-Z) acts on SIGTERM only once resumed
      rm -f "$PIDS/$f.pid"
    fi
  done
  # demos started without a pid file (or by an older version): found by their command line, never this --stop itself
  for p in $(pgrep -f "fork/demo.sh" || true); do
    [[ "$p" == "$$" ]] && continue
    { tr '\0' ' ' <"/proc/$p/cmdline"; } 2>/dev/null | grep -q -- "--stop" && continue
    kill -TERM "$p" 2>/dev/null && say "stopped a demo (pid $p)"
    kill -CONT "$p" 2>/dev/null || true
  done
  sleep 1
  pkill -TERM -f "riskdep watch .*--out $PIDS" 2>/dev/null && say "stopped a demo watch" || true
  pkill -CONT -f "riskdep watch .*--out $PIDS" 2>/dev/null || true
  pkill -f "tail --pid=[0-9]+ -n0 -F $PIDS/watch.log" 2>/dev/null || true
  "$HERE/start-fork.sh" --stop 2>/dev/null | sed 's/^/  /' || true
  if cast chain-id --rpc-url "$R" >/dev/null 2>&1; then
    say "something still answers on $R (an anvil not started by these scripts?): stop it by hand"
  else
    say "all stopped"
  fi
  exit 0
fi

# one demo at a time: two would share the fork's port and out/demo/
if [[ -f "$PIDS/demo.pid" ]] && kill -0 "$(cat "$PIDS/demo.pid")" 2>/dev/null; then
  fail "a demo is already running (pid $(cat "$PIDS/demo.pid")): scripts/fork/demo.sh --stop"
fi
if [[ -z "$RECORD" ]] && cast chain-id --rpc-url "$R" >/dev/null 2>&1 && [[ ! -f "$ROOT/out/anvil.pid" ]]; then
  fail "something already answers on $R and was not started by these scripts: stop it first"
fi

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
export WATCH_LOG="$LOG"  # crisis-belem.sh waits for the watch at the right moments (lib.sh sync_watch)
mkdir -p "$ROOT/out/demo"
: >"$LOG"
rm -f "$ROOT"/out/demo/watch-*.cursor "$ROOT"/out/demo/watch-*.jsonl  # each demo starts on a fresh fork: no resume
WATCH_PID="" TAIL_PID=""
echo $$ >"$PIDS/demo.pid"
cleanup() {
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  if [[ -n "$WATCH_PID" ]]; then
    pkill -TERM -P "$WATCH_PID" 2>/dev/null || true  # uv's python child, not only uv
    kill "$WATCH_PID" 2>/dev/null || true
  fi
  "$HERE/start-fork.sh" --stop >/dev/null 2>&1 || true
  rm -f "$PIDS/demo.pid" "$PIDS/watch.pid"
}
trap cleanup EXIT
trap 'echo; say "interrupted: stopping the watch and the fork"; exit 130' INT TERM

# what riskdep prints, as it prints it: alerts only, marked, info kept for the lines that tell the story
show_watch() {
  tail --pid="$$" -n0 -F "$LOG" 2>/dev/null | stdbuf -oL grep -E --line-buffered '^(CRITICAL|WARN|INFO) ' \
    | stdbuf -oL grep -Ev --line-buffered '^INFO .*(Deallocate|Allocate|shares moved|Your withdraw|Your deposit)' \
    | while IFS= read -r line; do
        case "$line" in
          CRITICAL*) printf '\033[1;31m  riskdep ▸ %s\033[0m\n' "$line" ;;
          WARN*) printf '\033[33m  riskdep ▸ %s\033[0m\n' "$line" ;;
          *) printf '\033[2m  riskdep ▸ %s\033[0m\n' "$line" ;;
        esac
      done
}

caption "riskdep — a crisis on a mainnet fork"
say "building the demo contracts and forking Ethereum mainnet at block $BLOCK…"
(cd "$HERE" && forge build >/dev/null 2>&1) || fail "forge build failed in scripts/fork/"
"$HERE/start-fork.sh" "$BLOCK" | grep -E '^fork at' | sed 's/^/  /'

say "starting riskdep watch on the Belem RWA EURCV vault (one block per batch, polling every 2 s)…"
(cd "$ROOT" && exec uv run python -m riskdep watch --vault "$VAULT" --step 1 --poll 2 --out "$ROOT/out/demo" >"$LOG" 2>&1) &
WATCH_PID=$!
echo "$WATCH_PID" >"$PIDS/watch.pid"
wait_startup() {
  for _ in $(seq 1 240); do
    grep -q 'cross-check Morpho API' "$LOG" && return 0
    kill -0 "$WATCH_PID" 2>/dev/null || { cat "$LOG" >&2; fail "riskdep watch stopped"; }
    sleep 1
  done
  fail "riskdep did not finish starting up in 4 min. The fork's upstream is probably throttling it (HTTP 429 in out/anvil.log): retry in a few minutes, or set keys.ini [rpc] url"
}

if [[ -n "${SHORT:-}" ]]; then
  # the first two acts need no watch: they play while it starts up, then only its three key start-up findings show
  REST=()
  for n in "${ACTS[@]}"; do
    if [[ "$n" == 0 || "$n" == 1 ]]; then DEMO=1 "$HERE/crisis-belem.sh" --act "$n"; pause; else REST+=("$n"); fi
  done
  say "riskdep has finished reading the vault, its markets and who controls them:"
  wait_startup
  grep -E '^(WARN|INFO) .*(cannot report below|exit gates are abdicated|timelock\(s\) control)' "$LOG" \
    | cut -c1-220 | sed 's/^/  riskdep ▸ /' || true
  ACTS=("${REST[@]}")
  show_watch &
  TAIL_PID=$!
else
  show_watch &
  TAIL_PID=$!
  wait_startup
fi
sleep 1
pause

for n in "${ACTS[@]}"; do
  DEMO=1 "$HERE/crisis-belem.sh" --act "$n"
  sync_watch
  pause
done

caption "End — what riskdep said, by level"
printf '\033[1;31m  %s critical\033[0m\n' "$(grep -cE '^CRITICAL ' "$LOG" || true)"
printf '\033[33m  %s warn\033[0m\n' "$(grep -cE '^WARN ' "$LOG" || true)"
say "full log: out/demo/watch.log · alerts as JSON: out/demo/watch-${VAULT,,}.jsonl"
say "the same run, offline: uv run python -m riskdep watch --vault $VAULT --replay --record-as fork-belem"
