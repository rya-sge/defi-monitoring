#!/usr/bin/env bash
# The crisis of the Belem RWA EURCV vault, played on a local mainnet fork (docs/analysis/FORK-PRESENTATION.md §2).
# Start the fork first (scripts/fork/start-fork.sh), and `riskdep watch --vault $VAULT` in another pane.
#
#   scripts/fork/crisis-belem.sh              every act, in order, pausing between them
#   scripts/fork/crisis-belem.sh --act N      act N alone (acts build on each other: run them in order on a fresh fork)
#   scripts/fork/crisis-belem.sh --retake N   revert the fork to just before act N, then play it again
#   PAUSE=8 scripts/fork/crisis-belem.sh      sleep 8 s between steps instead of waiting for Enter (vhs takes)
#
# Every act ends with a check on-chain: if the chain did not move as planned, the script stops instead of filming
# riskdep reacting to nothing. Every action uses a role the protocols grant (issuer, curator, timelock); no exploit.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$HERE/lib.sh"
SNAP="$ROOT/out/fork-snapshots"
mkdir -p "$SNAP"
MP="($EURCV,$MGLOEURO,$ORACLE,$IRM,$LLTV)"

# --- reads
position() { cast call "$MORPHO" "position(bytes32,address)(uint256,uint128,uint128)" "$MARKET" "$BORROWER" --rpc-url "$R"; }
market() { cast call "$MORPHO" "market(bytes32)(uint128,uint128,uint128,uint128,uint128,uint128)" "$MARKET" --rpc-url "$R" | num | tr '\n' ' '; }
nav() { cast call "$FEED" "latestRoundData()(uint80,int256,uint256,uint256,uint80)" --rpc-url "$R" | sed -n 2p | num; }
ltv() {  # the borrower's LTV at the oracle price, from Morpho Blue's own storage
  local p m
  p=($(position | num)); m=($(market))
  python3 -c "d=${p[1]}*${m[2]}//max(${m[3]},1); c=${p[2]}; px=$(cast call "$ORACLE" 'price()(uint256)' --rpc-url "$R" | num); print(f'{d/(c*px/1e36):.4f}' if c else 'no collateral')"
}
assets() { cast call "$VAULT" "totalAssets()(uint256)" --rpc-url "$R" | num; }
eur() { python3 -c "print(f'{$1/1e18:,.0f}')"; }

snapshot() { cast rpc evm_snapshot --rpc-url "$R" | tr -d '"' >"$SNAP/act-$1"; }
retake() {
  [[ -f "$SNAP/act-$1" ]] || fail "no snapshot before act $1: play the acts in order first"
  cast rpc evm_revert "$(cat "$SNAP/act-$1")" --rpc-url "$R" >/dev/null
  say "fork reverted to just before act $1"
}

# --- the acts
act0() {
  caption "Act 0 — Belem RWA EURCV: one market, one borrower, an oracle one wallet can move"
  say "vault $VAULT holds $(eur "$(assets)") EURCV; 86 % lent against mGLOeuro at 77 % LLTV"
  say "mGLOeuro NAV: $(python3 -c "print(f'{$(nav)/1e8:,.0f}')") EUR, written by the EOA $FEED_ADMIN alone, inside a fixed band 90,000–110,000"
  say "the only borrower $BORROWER sits at LTV $(ltv)"
  [[ -n "${DEMO:-}" ]] || say "in the other panes: riskdep graph --vault $VAULT   and   riskdep watch --vault $VAULT --step 1"
  [[ "$(nav)" == "$NAV_START" ]] || fail "the NAV is not 100,000 EUR: re-read the facts (FORK-PRESENTATION.md §1)"
}

act1() {
  caption "Act 1 — before anything happens: what would a markdown cost?"
  riskdep analyze --vault "$VAULT" --shock token=mGLOeuro:0.10 --live || true
  pause
  riskdep analyze --vault "$VAULT" --shock token=mGLOeuro:0.30 --live || true
  cp "$ROOT/out/vault-incident-${VAULT,,}.json" "$ROOT/out/fork-prediction-30.json"  # act 7 compares against it
}

act2() {
  caption "Act 2 — the issuer marks the NAV down 10 %: one transaction, no delay"
  send_as "$FEED_ADMIN" "$FEED" "setRoundData(int256)" "$NAV_MARKDOWN"
  mine
  say "NAV now $(python3 -c "print(f'{$(nav)/1e8:,.0f}')") EUR; borrower LTV $(ltv) against a 0.77 LLTV"
  python3 -c "import sys; sys.exit(0 if float('$(ltv)') > 0.77 else 1)" || fail "the borrower is not liquidatable"
}

act3() {
  caption "Act 3 — a liquidator steps in"
  local bal
  bal="$(cast to-uint256 10000000000000000000000000)"  # 10M EURCV, written into the token's balance slot
  cast rpc anvil_setStorageAt "$EURCV" "$(cast index address "$LIQUIDATOR" "$EURCV_BALANCE_SLOT")" "$bal" --rpc-url "$R" >/dev/null
  send_as "$LIQUIDATOR" "$EURCV" "approve(address,uint256)" "$MORPHO" "$(cast max-uint)"
  local before after
  before="$(position | sed -n 3p | num)"
  send_as "$LIQUIDATOR" "$MORPHO" "liquidate((address,address,address,address,uint256),address,uint256,uint256,bytes)" \
    "$MP" "$BORROWER" 2000000000000000000 0 0x
  mine
  after="$(position | sed -n 3p | num)"
  say "2 mGLOeuro seized; the borrower's collateral $(python3 -c "print($before/1e18)") → $(python3 -c "print($after/1e18)"), LTV $(ltv)"
  [[ "$after" != "$before" ]] || fail "the liquidation did not seize collateral"
}

act4() {
  caption "Act 4 — depositors run: who gets out?"
  local sh m liq
  sh="$(cast call "$VAULT" "balanceOf(address)(uint256)" "$DEPOSITOR_SMALL" --rpc-url "$R" | num)"
  send_as "$DEPOSITOR_SMALL" "$VAULT" "redeem(uint256,address,address)" "$sh" "$DEPOSITOR_SMALL" "$DEPOSITOR_SMALL"
  say "the 0.5 % holder redeems everything"
  m=($(market)); liq=$(python3 -c "print(${m[0]}-${m[2]})")
  send_as "$DEPOSITOR_BIG" "$VAULT" "withdraw(uint256,address,address)" "$liq" "$DEPOSITOR_BIG" "$DEPOSITOR_BIG"
  mine
  m=($(market))
  say "the 99.5 % holder takes what is left: $(eur "$liq") EURCV; the market is now $(python3 -c "print(f'{${m[2]}/${m[0]}:.0%}')") borrowed"
  if cast call "$VAULT" "withdraw(uint256,address,address)" 1000000000000000000000 "$DEPOSITOR_BIG" "$DEPOSITOR_BIG" \
    --from "$DEPOSITOR_BIG" --rpc-url "$R" >/dev/null 2>&1; then
    fail "a further withdrawal still succeeds"
  fi
  say "a further withdrawal reverts: insufficient liquidity"
}

act5() {
  caption "Act 5 — can the curator close the exit? Not on this vault"
  local data out
  data="$(cast calldata "setReceiveAssetsGate(address)" 0x000000000000000000000000000000000000dEaD)"
  send_as "$CURATOR" "$VAULT" "submit(bytes)" "$data"
  out="$(cast call "$VAULT" "setReceiveAssetsGate(address)" 0x000000000000000000000000000000000000dEaD \
    --from "$CURATOR" --rpc-url "$R" 2>&1 || true)"
  [[ "$out" == *281df4aa* || "$out" == *Abdicated* ]] || fail "the gate setter did not revert with Abdicated: $out"
  say "setReceiveAssetsGate reverts with Abdicated: the curator gave the power up for good"
  say "riskdep's startup said so (ExitGate): what stops the exit here is liquidity, not the curator"
  cast send "$VAULT" "revoke(bytes)" "$data" --from "$CURATOR" --unlocked --rpc-url "$R" >/dev/null
}

act6() {
  caption "Act 6 — the real loss is 30 %: the oracle cannot show it without an upgrade, behind 48 h"
  local impl data salt zero
  impl="$(deploy src/MGloEuroFeedV2.sol:MGloEuroFeedV2 "$FEED_ADMIN" "$FEED_ADMIN" 1000000000000 11000000000000)"
  [[ -n "$impl" ]] || fail "MGloEuroFeedV2 did not deploy (forge build in scripts/fork/)"
  data="$(cast calldata "upgrade(address,address)" "$FEED" "$impl")"
  salt="$(cast to-uint256 1)"; zero="$(cast to-uint256 0)"
  send_as "$MIDAS_PROPOSER" "$MIDAS_TIMELOCK" "schedule(address,uint256,bytes,bytes32,bytes32,uint256)" \
    "$PROXY_ADMIN" 0 "$data" "$zero" "$salt" "$TIMELOCK_DELAY"
  mine
  say "upgrade of the feed scheduled on the Midas timelock: executable in 48 h — riskdep alerts now, not at execution"
  pause
  cast rpc evm_increaseTime "$((TIMELOCK_DELAY + 1))" --rpc-url "$R" >/dev/null
  mine 1
  say "… 48 hours later"
  send_as "$MIDAS_PROPOSER" "$MIDAS_TIMELOCK" "execute(address,uint256,bytes,bytes32,bytes32)" \
    "$PROXY_ADMIN" 0 "$data" "$zero" "$salt"
  send_as "$FEED_ADMIN" "$FEED" "setRoundData(int256)" "$NAV_LOSS"
  mine
  say "new feed code installed; NAV now $(python3 -c "print(f'{$(nav)/1e8:,.0f}')") EUR; borrower LTV $(ltv)"
  [[ "$(nav)" == "$NAV_LOSS" ]] || fail "the NAV did not reach 70,000"
}

act7() {
  caption "Act 7 — liquidating the rest realises the bad debt"
  local before c after
  before="$(assets)"
  c="$(position | sed -n 3p | num)"
  send_as "$LIQUIDATOR" "$MORPHO" "liquidate((address,address,address,address,uint256),address,uint256,uint256,bytes)" \
    "$MP" "$BORROWER" "$c" 0 0x
  mine
  after="$(assets)"
  # 18-decimal amounts overflow bash integers: compute in python
  python3 - "$before" "$after" "$ROOT/out/fork-prediction-30.json" <<'EOF2' || fail "no bad debt was realised"
import json, sys
before, after = int(sys.argv[1]), int(sys.argv[2])
lost = (before - after) / 1e18
print(f"\033[36m  vault assets {before / 1e18:,.0f} → {after / 1e18:,.0f} EURCV: {lost:,.0f} lost by the depositors\033[0m")
try:
    pred = json.load(open(sys.argv[3]))["vault_loss"]
    print(f"\033[36m  predicted in act 1 for a 30 % markdown: {pred:,.0f}; observed: {lost:,.0f}. The gap is act 3: "
          "part of the debt was liquidated at 90,000, before the full loss reached the oracle\033[0m")
except (OSError, KeyError, ValueError):
    print("\033[36m  (no act-1 prediction saved: run act 1 first)\033[0m")
sys.exit(0 if after < before else 1)
EOF2
}

ACTS=(act0 act1 act2 act3 act4 act5 act6 act7)
require_fork
case "${1:-}" in
  --act) snapshot "$2"; "${ACTS[$2]}" ;;
  --retake) retake "$2"; snapshot "$2"; "${ACTS[$2]}" ;;
  "")
    for i in "${!ACTS[@]}"; do
      snapshot "$i"
      "${ACTS[$i]}"
      [[ $i -lt $((${#ACTS[@]} - 1)) ]] && pause
    done ;;
  *) sed -n 2,12p "$0"; exit 2 ;;
esac
