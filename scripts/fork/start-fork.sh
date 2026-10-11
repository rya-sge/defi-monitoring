#!/usr/bin/env bash
# Start a local mainnet fork for the crisis demo (docs/analysis/FORK-PRESENTATION.md §3) and check it.
#
#   scripts/fork/start-fork.sh [BLOCK]          fork at BLOCK (default: head - 5 of the upstream), in the background
#   scripts/fork/start-fork.sh --load STATE     restart from a state saved with --dump (no upstream needed)
#   scripts/fork/start-fork.sh --stop           stop the anvil this script started
#
# Upstream: keys.ini [rpc] url if set (read, never printed), else the first keyless archive endpoint of FORK_UPSTREAMS
# that answers. Anvil's log and pid go to out/ (git-ignored).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
# shellcheck source=addresses.env
source "$HERE/addresses.env"
OUT="$ROOT/out"
mkdir -p "$OUT"
PID="$OUT/anvil.pid"
PORT="${FORK_RPC##*:}"

stop() {
  if [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null; then kill "$(cat "$PID")"; echo "anvil stopped"; fi
  rm -f "$PID"
}

upstream() {
  local url
  url="$(python3 - "$ROOT/keys.ini" <<'EOF'
import configparser, sys
cp = configparser.ConfigParser()
cp.read(sys.argv[1])
print(cp.get("rpc", "url", fallback="").strip())
EOF
)"
  if [[ -n "$url" ]]; then echo "$url"; return; fi
  for u in $FORK_UPSTREAMS; do
    if timeout 15 cast block-number --rpc-url "$u" >/dev/null 2>&1; then echo "$u"; return; fi
  done
  echo "no upstream answered; set keys.ini [rpc] url" >&2
  exit 1
}

wait_up() {
  for _ in $(seq 1 60); do
    if cast chain-id --rpc-url "$FORK_RPC" >/dev/null 2>&1; then return; fi
    sleep 1
  done
  echo "anvil did not start; see $OUT/anvil.log" >&2
  exit 1
}

check() {
  [[ "$(cast chain-id --rpc-url "$FORK_RPC")" == 1 ]] || { echo "not chain 1" >&2; exit 1; }
  local assets nav
  assets="$(cast call "$VAULT" "totalAssets()(uint256)" --rpc-url "$FORK_RPC" | cut -d' ' -f1)"
  nav="$(cast call "$FEED" "latestRoundData()(uint80,int256,uint256,uint256,uint80)" --rpc-url "$FORK_RPC" | sed -n 2p | cut -d' ' -f1)"
  [[ "$assets" != 0 ]] || { echo "the vault is empty on this fork" >&2; exit 1; }
  echo "fork at block $(cast block-number --rpc-url "$FORK_RPC"): vault holds $(python3 -c "print(f'{$assets/1e18:,.0f}')") EURCV, mGLOeuro NAV $(python3 -c "print(f'{$nav/1e8:,.0f}')") EUR"
  [[ "$nav" == "$NAV_START" ]] || echo "note: the NAV is not 100,000 EUR any more; re-read the facts (FORK-PRESENTATION.md §1)"
  cat <<EOF

export RISKDEP_RPC_URL=$FORK_RPC
export RISKDEP_FORK=1
EOF
}

case "${1:-}" in
  --stop) stop; exit 0 ;;
  --load)
    stop
    anvil --load-state "$2" --chain-id 1 --port "$PORT" --auto-impersonate >"$OUT/anvil.log" 2>&1 &
    echo $! >"$PID"
    wait_up; check; exit 0 ;;
esac

stop
UP="$(upstream)"
BLOCK="${1:-$(( $(cast block-number --rpc-url "$UP") - 5 ))}"
echo "forking mainnet at block $BLOCK"
anvil --fork-url "$UP" --fork-block-number "$BLOCK" --chain-id 1 --port "$PORT" --auto-impersonate \
  --dump-state "$OUT/fork-$BLOCK.json" >"$OUT/anvil.log" 2>&1 &
echo $! >"$PID"
wait_up
check
echo "(on --stop, the state is saved to out/fork-$BLOCK.json; --load it to retake without the upstream)"
