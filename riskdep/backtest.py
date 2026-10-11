"""Backtest: a past incident replayed, the tool's prediction against what happened on-chain (plan 2026-10-11-backtest,
D161–D164; `IMPROVEMENT.md` 2.3, `NEXT_STEP.md` B9).

For an episode of `registry.json` `backtest.episodes`: the markets' `Liquidate` events give what happened; the block
`backtest.lead_blocks` before the first one gives the state before it (every borrower found by its `Borrow` events,
its position, the market totals, the oracle price); the oracle's lowest price over the liquidation blocks is the
shock. `market_risk.value` at that price, the model behind vault incidents and the shock engine's Blue market, predicts
which positions become liquidatable, their debt, and the liquidation incentive; the events give the same, realised.

Reads at a past block need an archive RPC (`keys.ini`), and wide log ranges the Etherscan key: `--record` reads them
once and saves every response under `fixtures/replay/backtest-<episode>/`, keyed by the public URLs, so the test and
any later run replay offline with no key.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from eth_abi import decode
from eth_utils import keccak

from . import borrower as B
from . import market_risk as MR
from . import sources as S
from .abi import MORPHO_BLUE
from .discover import REGISTRY
from .vault import _call, _uint

BT = REGISTRY["backtest"]
LIQUIDATE = "0x" + keccak(text="Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)").hex()
BORROW = "0x" + keccak(text="Borrow(bytes32,address,address,address,uint256,uint256)").hex()


@dataclass
class MarketBacktest:
    market_id: str
    label: str
    loan_symbol: str
    oracle_fall: float  # the oracle's lowest price over the liquidation blocks, against the price before
    borrowers: int
    predicted_positions: int
    predicted_debt: float  # debt of the positions liquidatable at the lowest price, loan units
    predicted_bonus: float  # that debt × (LIF − 1): the incentive if every one of them is liquidated in full
    predicted_bad_debt: float
    realised_positions: int  # borrowers liquidated
    realised_events: int
    realised_repaid: float
    realised_bonus: float  # seized collateral at the oracle price of its block, minus the debt repaid
    realised_bad_debt: float
    missed: list[str] = field(default_factory=list)  # liquidated, not predicted
    extra: list[str] = field(default_factory=list)  # predicted, not liquidated


@dataclass
class Backtest:
    episode: str
    title: str
    before_block: int
    blocks: tuple[int, int]  # first and last liquidation
    markets: list[MarketBacktest]
    notes: list[str]

    def lines(self) -> list[str]:
        out = [
            f"BACKTEST  {self.title}  ·  state at block {self.before_block:,}, liquidations in blocks "
            f"{self.blocks[0]:,}–{self.blocks[1]:,}"
        ]
        out.append(
            f"    {'market':<26} {'oracle':>7} {'positions':>15} {'debt liquidatable / repaid':>34} "
            f"{'incentive':>24} {'bad debt':>17}"
        )
        for m in self.markets:
            u = m.loan_symbol
            out.append(
                f"    {m.label.split(' (')[0][:26]:<26} {-m.oracle_fall:>+7.2%} {m.predicted_positions:>6} / {m.realised_positions:<6} "
                f"{m.predicted_debt:>15,.0f} / {m.realised_repaid:<15,.0f} {m.predicted_bonus:>11,.0f} / "
                f"{m.realised_bonus:<10,.0f} {m.predicted_bad_debt:>7,.0f} / {m.realised_bad_debt:<7,.0f} {u}"
            )
            if m.missed or m.extra:
                out.append(
                    f"      {len(m.missed)} liquidated but not predicted, {len(m.extra)} predicted but not liquidated"
                )
        out.append("    (each pair: predicted / realised)")
        out += [f"  note: {n}" for n in self.notes]
        return out

    def to_json(self) -> dict:
        return asdict(self)


# --- pure


def decode_liquidation(log: dict) -> tuple[int, str, int, int, int]:
    """(block, borrower, repaid assets, seized collateral, bad debt assets) of one `Liquidate` log."""
    repaid, _, seized, bad, _ = decode(["uint256"] * 5, bytes.fromhex(log["data"][2:]))
    return log["block"], "0x" + log["topics"][3][26:], repaid, seized, bad


def compare(
    info: MR.MarketInfo,
    loan_unit: int,
    positions: dict[str, tuple[int, int]],
    totals: tuple[int, int],
    price_before: int,
    prices: dict[int, int],
    events: list[tuple[int, str, int, int, int]],
) -> MarketBacktest:
    """D162–D163, pure: the prediction at the lowest oracle price of the episode, against the events."""
    low = min(prices.values())
    tba, tbs = totals
    pred = [
        u
        for u, (coll, bs) in positions.items()
        if bs and (coll * low // 10**36) * info.lltv <= bs * (tba + 1) // (tbs + 10**6)
    ]
    r = MR.value({u: positions[u] for u in pred}, totals, low, info)
    debt = sum(positions[u][1] * (tba + 1) // (tbs + 10**6) for u in pred)
    liquidated = {e[1] for e in events}
    bonus = sum(seized * prices.get(b, low) // 10**36 - repaid for b, _, repaid, seized, _ in events)
    return MarketBacktest(
        info.id,
        info.label,
        info.loan_symbol,
        1 - low / price_before if price_before else 0.0,
        sum(1 for _, bs in positions.values() if bs),
        len(pred),
        debt / loan_unit,
        debt * (info.lif - 1) / loan_unit,
        r.unrealised_bad_debt / loan_unit,
        len(liquidated),
        len(events),
        sum(e[2] for e in events) / loan_unit,
        bonus / loan_unit,
        sum(e[4] for e in events) / loan_unit,
        sorted(liquidated - set(pred)),
        sorted(set(pred) - liquidated),
    )


# --- I/O


def run(f: S.Fetcher, name: str) -> Backtest:
    """Replay one episode. Raises KeyError for an unknown episode; `sources.CacheMiss` offline without a recording."""
    ep = BT["episodes"][name]
    lo, hi = ep["window"]
    events = {
        mid: [decode_liquidation(x) for x in S.etherscan_logs(f, MORPHO_BLUE, LIQUIDATE, mid, lo, hi)]
        for mid in ep["markets"]
    }
    blocks = sorted({e[0] for evs in events.values() for e in evs})
    if not blocks:
        raise ValueError(f"no liquidation in blocks {lo}–{hi} of {name}")
    before = blocks[0] - BT["lead_blocks"]
    markets = B.discover_markets(f, ep["markets"], before)
    out = []
    for mid, m in markets.items():
        borrowers = sorted(
            {"0x" + x["topics"][2][26:] for x in S.etherscan_logs(f, MORPHO_BLUE, BORROW, mid, 0, before)}
        )
        info = MR.MarketInfo(mid, m.lltv, m.loan_decimals, m.loan_symbol, m.label)
        tr = MR.Tracker({mid: info})
        tr._read(f, [(mid, u) for u in borrowers], before)
        p0 = _uint(S.rpc_batch(f, [_call(m.oracle, "price()")], before)[0])
        ev_blocks = sorted({e[0] for e in events[mid]})
        prices = {b: _uint(S.rpc_batch(f, [_call(m.oracle, "price()")], b)[0]) for b in ev_blocks}
        out.append(
            compare(
                info,
                10**m.loan_decimals,
                tr.positions.get(mid, {}),
                tr.totals.get(mid, (0, 0)),
                p0,
                prices,
                events[mid],
            )
        )
    notes = [
        ep["source"],
        "the prediction is the liquidation model alone, at the oracle's lowest price of the episode: the shock "
        "engine's squeeze needs the Pendle pool's curve at that date, which the quote API does not serve",
        "a liquidator may repay part of a position: realised repaid debt ≤ the debt that became liquidatable",
    ]
    return Backtest(name, ep["title"], before, (blocks[0], blocks[-1]), out, notes)
