"""The published contract: every shape `web/` consumes.

One module, because it has one reason to change — the payloads the UI reads. `openapi.json`
and the generated TypeScript follow from here, so a change in this file is a change to the
contract: regenerate `openapi.json` in the same commit.

Keep it in step with `report.to_dict` and `graph.to_dict`, which produce the data these
models describe. Nothing here fetches, computes or validates risk.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Mode = Literal["offline", "live", "refresh"]
AlertLevel = Literal["info", "warn", "critical"]
Verdict = Literal["STAY", "REDUCE", "EXIT"]
GraphNodeKind = Literal["Actor", "Pool", "Asset", "Oracle", "External", "Admin"]


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    mode: Mode
    data_as_of: str


class GraphNode(BaseModel):
    id: str
    kind: GraphNodeKind
    label: str
    details: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    rel: str
    amount: float | None = None
    unit: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    title: str
    subtitle: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class Alert(BaseModel):
    level: AlertLevel
    block: int
    tx: str | None = None
    event: str
    title: str
    detail: str = ""
    depositor_impact: float | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class AlertPage(BaseModel):
    target: str
    cursor: int = Field(description="Highest block in this page; pass it back as `since`.")
    counts: dict[str, int] = Field(description="Alerts per level in this page.")
    alerts: list[Alert]


class Target(BaseModel):
    target: str = Field(description='Watch target: a vault address, or "user-<address>".')
    alerts: int
    last_block: int | None = None


class ReportPosition(BaseModel):
    label: str
    collateral_units: float
    collateral_symbol: str
    collateral_address: str | None = None
    pt_price_usd: float | None = None
    collateral_decimals: int
    debt_usd: float
    loan_symbol: str
    loan_address: str | None = None
    lltv: float
    lif: float | None = None
    borrow_apy: float | None = None
    implied_apy: float | None = None
    maturity: str | None = None
    days_to_maturity: float | None = None
    oracle_mode: str
    oracle_ambiguous: bool
    pt_discount: float | None = None
    morpho_market: str | None = None
    borrower: str | None = None
    debt_raw: int | None = None
    loan_decimals: int
    oracle_price: float | None = None
    health_factor: float | None = None
    pendle_market: str | None = None
    underlying_address: str | None = None
    underlying_symbol: str | None = None
    underlying_drawdown_1y: float | None = None
    amm_liquidity_usd: float | None = None
    lending_liquidity_usd: float | None = None
    notes: list[str] = Field(default_factory=list)
    collateral_usd: float
    equity_usd: float
    liquidation_drop: float | None = None


class ReportGraphNode(BaseModel):
    id: str
    kind: str = Field(description="Lowercase layer kind: chain, asset, amm, issuer, lending, oracle…")
    label: str
    source: str | None = None
    evidence: str | None = None
    mode: str | None = None
    protocol: str | None = None
    registered: bool | None = None


class ReportGraphEdge(BaseModel):
    # networkx serialisation: `from`/`to`, not the source/target of /api/graph
    from_: str = Field(alias="from")
    to: str
    rel: str


class ReportGraph(BaseModel):
    nodes: list[ReportGraphNode]
    edges: list[ReportGraphEdge]


class ReportPrior(BaseModel):
    event: str
    node: str
    layer: str
    p_year: float
    a: float
    b: float
    basis: str
    recovery: float


class SimulationLayer(BaseModel):
    event: str
    layer: str
    node: str
    p_horizon: float
    mean_severity: float
    standalone_loss_usd: float
    contribution_usd: float
    liquidation_rate: float
    example_path: list[str] = Field(default_factory=list)
    basis: str = ""


class ReportSimulation(BaseModel):
    horizon_days: float
    n: int
    expected_loss_usd: float
    var95_usd: float
    cvar95_usd: float
    var99_usd: float
    cvar99_usd: float
    p_any_loss: float
    p_liquidation: float
    layers: list[SimulationLayer]
    interaction_usd: float


class ReportDecision(BaseModel):
    verdict: Verdict
    headline: str
    carry_usd: float
    exit_cost_usd: float
    expected_loss_usd: float
    net_stay_usd: float
    risk_multiple_to_exit: float | None = None
    liquidation_drop: float | None = None
    stress_drop: float
    reduction: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


class ExitQuote(BaseModel):
    source: str
    price_impact: float
    fee_usd: float
    estimated: bool = False
    amount_out_raw: str | None = None


class OracleSensitivity(BaseModel):
    oracle_mode: str
    verdict: Verdict
    expected_loss_usd: float
    cvar99_usd: float
    p_liquidation: float


class Report(BaseModel):
    generated: str
    data_as_of: str
    mode: str
    position: ReportPosition
    graph: ReportGraph
    priors: list[ReportPrior]
    simulation: ReportSimulation
    decision: ReportDecision
    exit_quote: ExitQuote
    oracle_sensitivity: OracleSensitivity | None = None


class AnalyzeRequest(BaseModel):
    market: str | None = Field(default=None, description="Morpho Blue market id. Omitted: the demo position.")
    user: str | None = Field(default=None, description="Borrower address; defaults to the market's largest.")
    pendle_market: str | None = Field(default=None, description="Analyse a bare PT holding instead of a borrow.")
    pt_amount: float | None = Field(default=None, description="PT units; required with pendle_market.")
    horizon: float = Field(default=30.0, gt=0, le=365, description="Horizon in days, capped at maturity.")
    paths: int = Field(default=20000, ge=1000, le=200000, description="Monte Carlo paths.")
    live: bool = Field(default=False, description="Fetch from the network instead of the cached snapshot.")


class Liquidation(BaseModel):
    """One borrower: the oracle fall that liquidates it, its debt and collateral (the vault's part, in a vault)."""

    drop: float
    debt_usd: float
    collateral_usd: float
    market: str | None = Field(default=None, description="The borrower's market id, in a vault's list.")


class MarketSummary(BaseModel):
    id: str
    label: str
    lltv: float
    collateral_price_usd: float | None = None
    collateral_drawdown_1y: float | None = Field(
        default=None,
        description="Worst 1-year drawdown of the collateral's USD price (DefiLlama); null without history.",
    )
    lif: float
    supply_usd: float
    borrow_usd: float
    liquidity_usd: float
    utilization: float
    borrow_apy: float


class Market(MarketSummary):
    borrowers: int
    liquidations: list[Liquidation]


class VaultMarket(MarketSummary):
    allocation_usd: float
    share_of_vault: float
    share_of_market: float


class Vault(BaseModel):
    address: str
    name: str
    asset_symbol: str
    total_assets_usd: float
    liquidity_usd: float
    markets: list[VaultMarket]
    liquidations: list[Liquidation] = Field(
        description="Every borrower of the vault's markets, its debt weighted by the vault's share of the market."
    )
