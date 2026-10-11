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
    """One borrower: the oracle fall that liquidates it, and its debt (the vault's part, in a vault)."""

    drop: float
    debt_usd: float
    market: str | None = Field(default=None, description="The borrower's market, in a vault's list.")


class MarketSummary(BaseModel):
    id: str
    label: str
    lltv: float
    collateral_price_usd: float | None = None
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


# --- a known incident on a vault or a book of vaults: `vault_incident.VaultIncident` and `vault_book.BookIncident`


class BookVaultIn(BaseModel):
    address: str
    label: str | None = None
    depositor: str | None = Field(default=None, description="Whose position to weigh; default the largest depositor.")
    amount: float | None = Field(default=None, gt=0, description="`pocket` weighting: the book's position, in USD.")


class BookIn(BaseModel):
    """A book of Morpho Vault V2 vaults, as in `examples/*.json`."""

    name: str | None = None
    weighting: Literal["vault", "depositor", "pocket"] = "vault"
    vaults: list[BookVaultIn] = Field(min_length=1)


class IncidentRequest(BaseModel):
    """One of `vaults`, `book` or `example`, and at least one shock."""

    vaults: list[str] = Field(default_factory=list, description="Vault V2 addresses: an ad hoc book.")
    book: BookIn | None = Field(default=None, description="A book given inline.")
    example: str | None = Field(default=None, description="A book of `examples/` by name (GET /api/books).")
    shocks: list[str] = Field(
        min_length=1,
        description="As `analyze --shock`: `token=<collateral>:<fall>` (an issuer markdown), "
        "`borrower=<collateral, market id or all>:<recovery>[:<n>]` (the n largest borrowers default).",
        examples=[["token=PST:0.30"]],
    )
    user: str | None = Field(default=None, description="Depositor address, for every vault without its own.")
    horizon: float = Field(default=30.0, gt=0, le=365, description="Days over which the breakeven p* is stated.")
    exit_cost: float | None = Field(
        default=None,
        ge=0,
        lt=1,
        description="The cost of leaving as a share of what leaves (0.11 for the brief's 11 % unwind), instead of "
        "the vault's yield given up.",
    )
    conditional: bool = Field(
        default=False,
        description="Add the distribution of the loss of staying given the incident (needs a token=… shock).",
    )
    live: bool = Field(default=False, description="Read the chain instead of the recordings (nothing is saved).")


class BookSummary(BaseModel):
    name: str
    title: str
    weighting: Literal["vault", "depositor", "pocket"]
    vaults: list[BookVaultIn]


class Conditional(BaseModel):
    """Given the incident, its size and the liquidators drawn: the loss of staying against leaving, in USD."""

    paths: int
    stay_mean: float
    stay_p50: float
    stay_p95: float
    stay_p99: float
    leave_mean: float = Field(description="Loss left after leaving first, plus the certain cost of leaving.")
    p_stay_worse: float = Field(description="Share of paths where staying costs more than leaving.")
    no_liquidator_share: float
    text: str


class MarketHit(BaseModel):
    market_id: str
    label: str
    drop: float = Field(description="Fall of the collateral's value applied to this market.")
    borrowers: int
    total_borrow: float
    liquidatable_debt: float
    bad_debt: float = Field(description="What the market's lenders lose, in the loan token.")
    vault_share: float
    vault_loss: float
    oracle_class: str
    timing: str = Field(description="How fast the incident lands.")
    vault_exposure: float = 0.0
    via: str = ""
    seen: bool = True
    event: Literal["markdown", "default"] = "markdown"
    defaulters: list[str] = Field(default_factory=list)
    defaulted_debt: float = 0.0
    exit_route: Literal["none", "thin", "deep"] | None = None
    no_liquidator_shortfall: float = 0.0
    top1_share: float = 0.0
    top3_share: float = 0.0
    grade: str | None = Field(default=None, description="Pharos grade of the collateral, e.g. 'fxSAVE F 36'.")
    pharos_exposure: float = 0.0
    source: Literal["incident", "engine"] = "incident"
    engine: str = ""


class VaultIncident(BaseModel):
    vault: str
    name: str
    symbol: str
    block: int
    depositor: str | None
    shocks: dict[str, float]
    hits: list[MarketHit]
    vault_total: float
    vault_loss: float
    depositor_assets: float
    loss_if_stay: float
    can_leave_now: float
    stuck: float
    loss_if_exit_first: float
    verdict: Verdict = Field(description="Given the incident: it is assumed to happen.")
    reason: str
    notes: list[str] = Field(default_factory=list)
    asset: str = ""
    asset_usd: float | None = None
    events: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    pharos: str | None = None
    common_mode: list[str] = Field(default_factory=list)
    engine_block: int | None = None
    sibling_losses: list[tuple[str, str, float, str]] = Field(
        default_factory=list, description="Sibling markets the engine reaches: (market id, label, loss, loan token)."
    )
    apy: float | None = None
    horizon_days: float = 30.0
    exit_cost: float = 0.0
    p_star: float | None = Field(
        default=None, description="Probability over the horizon above which leaving now pays; ≥ 1: stay whatever."
    )
    p_star_year: float | None = None
    outside: list[str] = Field(default_factory=list)
    liquidity: tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0), description="What can leave: plain, through forceDeallocate, and its penalty."
    )
    exit_cost_rate: float | None = None
    conditional: Conditional | None = None


class VaultLine(BaseModel):
    vault: str
    name: str
    value_usd: float
    loss_usd: float
    exposure_usd: float
    verdict: Verdict
    hit_markets: list[str]
    priced: bool
    p_star: float | None = None
    p_star_year: float | None = None
    exit_cost_usd: float = 0.0
    saved_usd: float = 0.0
    reason: str = Field(default="", description="Why the verdict, in one clause.")


class BookIncident(BaseModel):
    name: str
    weighting: Literal["vault", "depositor", "pocket"]
    shocks: list[str]
    lines: list[VaultLine]
    value_usd: float
    loss_usd: float
    exposure_usd: float
    headline: str
    notes: list[str] = Field(default_factory=list)
    p_star: float | None = None
    p_star_year: float | None = None
    horizon_days: float = 30.0
    conditional: Conditional | None = None


class IncidentResponse(BaseModel):
    """The book's sum and headline, and each vault's detail (one vault: a book of one)."""

    book: BookIncident
    vaults: list[VaultIncident]
