#!/usr/bin/env bash
# Alternative crisis (docs/analysis/FORK-PRESENTATION.md §2): unbacked PST minted on Ethereum through a Chainlink CCIP
# token pool, as a compromised lane or pool owner would. The oracle is Chainlink's exchange-rate feed of the Huma pool:
# it does not see the mint, so the price stays where it was while the supply grows. $34.7M of RockawayX lending
# (Confidential RWA USDC, Huma USDC Main) is against PST.
#
#   scripts/fork/alt-pst-mint.sh [AMOUNT]   AMOUNT in PST (6 decimals), default 10,000,000; then:
#   riskdep watch --vault $VAULT_HUMA       Admin.Mint (critical) above watch.mint_share_critical of the supply
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"
require_fork

amount="${1:-10000000}"
supply() { cast call "$PST" "totalSupply()(uint256)" --rpc-url "$R" | num; }
oracle() { cast call "$PST_ORACLE" "price()(uint256)" --rpc-url "$R" | num; }
caption "Unbacked PST minted through a CCIP pool: the oracle does not see it"
s0="$(supply)"; o0="$(oracle)"
send_as "$PST_CCIP_POOL" "$PST" "mint(address,uint256)" 0x2222222222222222222222222222222222222222 "$((amount * 1000000))"
mine
s1="$(supply)"; o1="$(oracle)"
python3 - "$s0" "$s1" "$o0" "$o1" <<'EOF' || fail "no PST was minted"
import sys
s0, s1, o0, o1 = map(int, sys.argv[1:])
print(f"\033[36m  PST supply {s0 / 1e6:,.0f} → {s1 / 1e6:,.0f} (+{s1 / s0 - 1:.1%}); oracle {o0 / 1e36:.6f} → "
      f"{o1 / 1e36:.6f}: unchanged, so the new PST can be posted as collateral at full price\033[0m")
sys.exit(0 if s1 > s0 else 1)
EOF
