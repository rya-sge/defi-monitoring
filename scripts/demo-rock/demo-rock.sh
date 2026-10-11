#!/usr/bin/env bash
# The RockawayX demo in one command: a mainnet fork, riskdep watching two RockawayX vaults, two crises caused by the
# roles that could really cause them, and every warn/critical alert posted to the Telegram channel as it happens.
# Reuses scripts/fork/ as it is (lib.sh, alt-redstone.sh, alt-pst-mint.sh; its fork start is copied here): nothing there is modified.
#
#   scripts/demo-rock/demo-rock.sh                  the full demo (≈ 5 min), pausing 4 s between steps
#   scripts/demo-rock/demo-rock.sh --manual         wait for Enter between steps (presenting live)
#   scripts/demo-rock/demo-rock.sh --no-telegram    the same, nothing sent to Telegram (rehearsal)
#   scripts/demo-rock/demo-rock.sh --block N        fork at block N (default 26165572, where the facts were checked)
#
# Needs Foundry, uv and network access (fork upstream, Morpho API); Telegram needs keys.ini [alerts].
set -euo pipefail
HERE="$(cd "$(dirname "$0")/../fork" && pwd)"  # lib.sh and the alt-*.sh scripts expect HERE = scripts/fork
# shellcheck source=../fork/lib.sh
source "$HERE/lib.sh"

BLOCK=26165572
TELEGRAM=1
export PAUSE="${PAUSE:-4}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manual) unset PAUSE ;;
    --no-telegram) TELEGRAM="" ;;
    --block) BLOCK="$2"; shift ;;
    *) sed -n 2,11p "$0"; exit 2 ;;
  esac
  shift
done

OUT="$ROOT/out/demo-rock"
mkdir -p "$OUT"
rm -f "$OUT"/watch-*.cursor "$OUT"/watch-*.jsonl "$OUT"/*.log "$OUT"/notify.state.json  # a fresh fork: no resume
LOG_TORI="$OUT/watch-tori.log" LOG_HUMA="$OUT/watch-huma.log"
PIDS=()
ANVIL_PID=""  # this demo's own anvil: scripts/fork/start-fork.sh --stop (out/anvil.pid) cannot kill it
cleanup() {
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || true; done
  [[ -n "$ANVIL_PID" ]] && kill "$ANVIL_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Copied from scripts/fork/start-fork.sh, with the archive endpoint of keys.ini [alchemy] as a second choice and more
# retries: two watches read through the fork, and a keyless upstream answers 429 until anvil gives up.
upstream() {
  local url
  url="$(python3 - "$ROOT/keys.ini" <<'PY'
import configparser, sys
cp = configparser.ConfigParser()
cp.read(sys.argv[1])
print(cp.get("rpc", "url", fallback="").strip() or cp.get("alchemy", "alchemy_ethereum_endpoint", fallback="").strip())
PY
)"
  if [[ -n "$url" ]]; then echo "$url"; return; fi
  for u in $FORK_UPSTREAMS; do
    if timeout 15 cast block-number --rpc-url "$u" >/dev/null 2>&1; then echo "$u"; return; fi
  done
  fail "no upstream answered; set keys.ini [rpc] url or [alchemy] alchemy_ethereum_endpoint"
}
start_fork() {
  cast chain-id --rpc-url "$R" >/dev/null 2>&1 && fail "something already answers on $R (another demo?); stop it first"
  anvil --fork-url "$(upstream)" --fork-block-number "$BLOCK" --chain-id 1 --port "${R##*:}" --auto-impersonate \
    --retries 20 --fork-retry-backoff 1000 >"$OUT/anvil.log" 2>&1 &
  ANVIL_PID=$!
  for _ in $(seq 1 60); do cast chain-id --rpc-url "$R" >/dev/null 2>&1 && break; sleep 1; done
  require_fork
  say "fork at block $(cast block-number --rpc-url "$R")"
}

offline() { (cd "$ROOT" && env -u RISKDEP_RPC_URL -u RISKDEP_FORK uv run python -m riskdep "$@"); }  # recordings
post() {  # post <json with name and headline>: one scenario message to the channel
  [[ -n "$TELEGRAM" ]] && offline notify --post "$1" | sed 's/^/  /' || true
}

# what a watch prints, as it prints it: warn and critical only, marked with the vault
show_watch() {
  local log="$1" name="$2"
  tail --pid="$$" -n0 -F "$log" 2>/dev/null | stdbuf -oL grep -E --line-buffered '^(CRITICAL|WARN) ' \
    | while IFS= read -r line; do
        case "$line" in
          CRITICAL*) printf '\033[1;31m  riskdep ▸ %s ▸ %s\033[0m\n' "$name" "$line" ;;
          *) printf '\033[33m  riskdep ▸ %s ▸ %s\033[0m\n' "$name" "$line" ;;
        esac
      done
}

start_watch() {  # start_watch <vault> <log> <name>
  (cd "$ROOT" && exec uv run python -m riskdep watch --vault "$1" --step 1 --poll 2 --out "$OUT" >"$2" 2>&1) &
  PIDS+=($!)
  local pid=$!
  for _ in $(seq 1 240); do
    grep -q 'cross-check Morpho API' "$2" && break
    kill -0 "$pid" 2>/dev/null || { cat "$2" >&2; fail "riskdep watch stopped on $3"; }
    sleep 1
  done
  show_watch "$2" "$3" &
  PIDS+=($!)
  say "watching $3"
}

caption "riskdep — RockawayX vaults under attack, on a mainnet fork"
say "building the demo contracts and forking Ethereum mainnet at block $BLOCK…"
(cd "$HERE" && forge build >/dev/null 2>&1) || fail "forge build failed in scripts/fork/"
start_fork

say "starting riskdep watch on two RockawayX vaults (one block per batch, polling every 2 s)…"
start_watch "$VAULT_TORI" "$LOG_TORI" "RockawayX Tori Ecosystem"
start_watch "$VAULT_HUMA" "$LOG_HUMA" "Huma USDC Main"

if [[ -n "$TELEGRAM" ]]; then
  # after the watches' start-up: the channel gets the crisis, not the standing findings (notify starts at the files' end)
  (cd "$ROOT" && exec uv run python -m riskdep notify --out "$OUT" >"$OUT/notify.log" 2>&1) &
  PIDS+=($!)
  printf '{"name": "riskdep demo", "headline": "RockawayX vaults on a local mainnet fork at block %s. Watching RockawayX Tori Ecosystem and Huma USDC Main. The crises that follow are simulated on the fork, by the roles that could cause them on mainnet."}\n' "$BLOCK" >"$OUT/intro.json"
  post "$OUT/intro.json"
  say "alerts at warn and above now go to the Telegram channel"
fi
pause

caption "Act 1 — before anything happens: what would a strUSD markdown cost the book?"
say "riskdep analyze --book examples/rockawayx-ethereum.json --shock token=strUSD:0.32   (offline, recorded vaults)"
offline analyze --book examples/rockawayx-ethereum.json --shock token=strUSD:0.32 --out "$OUT/predict-strusd" \
  | grep -E '^  strUSD|^    (vault|RockawayX Tori|RockawayX USDC Yield|book)' | cut -c1-150 || true
post "$OUT/predict-strusd/book-incident.json"
pause

caption "Act 2 — RedStone's 2-of-3 Safe rewrites the strUSD feed, no timelock"
"$HERE/alt-redstone.sh"
WATCH_LOG="$LOG_TORI" sync_watch
pause

caption "Act 3 — unbacked PST minted through a Chainlink CCIP pool; the oracle does not see it"
"$HERE/alt-pst-mint.sh"
WATCH_LOG="$LOG_HUMA" sync_watch
sleep "${NOTIFY_DRAIN:-8}"  # the last alerts leave the queue (3 s apart)
pause

caption "End — what riskdep said"
for pair in "RockawayX Tori Ecosystem:$LOG_TORI" "Huma USDC Main:$LOG_HUMA"; do
  name="${pair%%:*}" log="${pair#*:}"
  printf '  %-26s \033[1;31m%s critical\033[0m  \033[33m%s warn\033[0m\n' "$name" \
    "$(grep -cE '^CRITICAL ' "$log" || true)" "$(grep -cE '^WARN ' "$log" || true)"
done
[[ -n "$TELEGRAM" ]] && say "telegram: $(grep -oE '[0-9]+ message\(s\) sent' "$OUT/notify.log" | awk '{s+=$1} END {print s+0}') alert message(s) sent; log: out/demo-rock/notify.log"
say "watch logs: out/demo-rock/watch-tori.log, watch-huma.log · alerts as JSON: out/demo-rock/watch-*.jsonl"
