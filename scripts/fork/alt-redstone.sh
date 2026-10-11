#!/usr/bin/env bash
# Alternative crisis (docs/analysis/FORK-PRESENTATION.md §2): the 2-of-3 Safe that owns RedStone's ProxyAdmin
# installs new code behind the strUSD fundamental feed, with no timelock. ~$20M of RockawayX lending (Tori, USDC Yield)
# is priced by it. Run on a fork with no time jump: after a 48 h warp RedStone's push feeds are stale and revert.
#
#   scripts/fork/alt-redstone.sh          then: riskdep watch --vault $VAULT_TORI
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"
require_fork

price() { cast call "$STRUSD_ORACLE" "price()(uint256)" --rpc-url "$R" | num; }
caption "RedStone's strUSD feed rewritten by a 2-of-3 Safe, in one transaction"
before="$(price)" || fail "the strUSD oracle reverts: is this fork past a time jump? Start a fresh one"
impl="$(deploy src/FixedAnswerFeed.sol:FixedAnswerFeed "$REDSTONE_SAFE" 70000000 8)"
[[ -n "$impl" ]] || fail "FixedAnswerFeed did not deploy (forge build in scripts/fork/)"
send_as "$REDSTONE_SAFE" "$REDSTONE_PROXY_ADMIN" "upgrade(address,address)" "$STRUSD_FEED" "$impl"
mine
after="$(price)"
python3 - "$before" "$after" <<'EOF' || fail "the oracle did not move"
import sys
b, a = int(sys.argv[1]), int(sys.argv[2])
print(f"\033[36m  strUSD/USDC oracle {b / 1e24:.4f} → {a / 1e24:.4f} ({a / b - 1:+.1%}): every strUSD borrower whose LTV "
      f"was above {0.86 * a / b:.0%} is now past the 86 % LLTV and liquidatable\033[0m")
sys.exit(0 if a < b else 1)
EOF
say "riskdep: Admin.Upgraded (critical) on the feed, the oracle move, liquidations and bad debt in the Tori vault"
