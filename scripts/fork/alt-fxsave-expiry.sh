#!/usr/bin/env bash
# Alternative crisis (docs/analysis/FORK-PRESENTATION.md §2): PT-fxSAVE-29OCT2026 reaches maturity. Its oracle is a
# Pendle linear discount: it rises to exactly 1.0 by time alone, whatever the PT pool says, and from then on the
# collateral is the underlying fxSAVE. $1M of the RockawayX f(x) vault is lent against it.
#
#   scripts/fork/alt-fxsave-expiry.sh       then: riskdep watch --vault $VAULT_FX
# The time jump makes RedStone's push feeds stale on this fork: run alt-redstone.sh before, not after.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"
require_fork

price() { cast call "$PT_FXSAVE_ORACLE" "price()(uint256)" --rpc-url "$R" | num; }
caption "PT-fxSAVE reaches maturity: its linear oracle goes to 1.0"
p0="$(price)"
now="$(cast block --rpc-url "$R" -f timestamp)"
[[ "$now" -lt "$PT_FXSAVE_EXPIRY" ]] || fail "this fork is already past the expiry"
cast rpc evm_increaseTime "$((PT_FXSAVE_EXPIRY - now + 3600))" --rpc-url "$R" >/dev/null
mine
p1="$(price)"
python3 - "$p0" "$p1" <<'EOF' || fail "the oracle is not at 1.0 after expiry"
import sys
p0, p1 = int(sys.argv[1]), int(sys.argv[2])
print(f"\033[36m  PT-fxSAVE oracle {p0 / 1e24:.6f} → {p1 / 1e24:.6f} USDC per PT, by time alone; the PT now redeems "
      "1:1 for fxSAVE through its SY\033[0m")
sys.exit(0 if p1 == 10**24 else 1)
EOF
