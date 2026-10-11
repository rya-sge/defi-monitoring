# Helpers shared by the fork-demo scripts (sourced, not run). Needs `HERE` set to scripts/fork/.
# shellcheck shell=bash
ROOT="$(cd "$HERE/../.." && pwd)"
# shellcheck source=addresses.env
source "$HERE/addresses.env"
R="$FORK_RPC"
export RISKDEP_RPC_URL="$R" RISKDEP_FORK=1

caption() { printf '\n\033[1;37;44m %s \033[0m\n' "$*"; }
say() { printf '\033[36m  %s\033[0m\n' "$*"; }
pause() { if [[ -n "${PAUSE:-}" ]]; then sleep "$PAUSE"; else read -r -p "  [Enter] " _; fi; }
fail() { printf '\033[1;31m  check failed: %s\033[0m\n' "$*" >&2; exit 1; }
fund() { cast rpc anvil_setBalance "$1" 0x56BC75E2D63100000 --rpc-url "$R" >/dev/null; }
# send a transaction as any address (anvil --auto-impersonate), funding it with gas first
send_as() { local who="$1"; shift; fund "$who"; cast send "$@" --from "$who" --unlocked --rpc-url "$R" >/dev/null; }
mine() { cast rpc anvil_mine "0x${1:-3}" --rpc-url "$R" >/dev/null; }  # past the watch's 2 confirmations
num() { cut -d' ' -f1; }
riskdep() { (cd "$ROOT" && uv run python -m riskdep "$@"); }
deploy() {  # deploy <contract path:name> <from> <constructor args…>: prints the address
  local what="$1" from="$2"; shift 2
  (cd "$HERE" && forge create "$what" --rpc-url "$R" --unlocked --from "$from" --broadcast --constructor-args "$@" 2>/dev/null) \
    | awk '/Deployed to/ {print $3}'
}
require_fork() { cast chain-id --rpc-url "$R" >/dev/null 2>&1 || fail "no fork at $R: run scripts/fork/start-fork.sh"; }
