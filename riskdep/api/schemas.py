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
    discovery: dict[str, Any] | None = Field(
        default=None,
        description="The layers the borrower's recorded dependency graph adds: oracle inputs and who can change "
        "them, sibling markets, the collateral's backing and grade, the protocols' share of DeFi (plan 2026-10-11-depth).",
    )


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
    kind: Literal["vault", "borrow", "pt"] = Field(
        default="vault",
        description="`borrow`: a Morpho Blue borrow, `address` is then the market id; `pt`: a PT held without a "
        "borrow, `address` is then its Pendle market and `amount` is required.",
    )


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
        "`borrower=<collateral, market id or all>:<recovery>[:<n>]` (the n largest borrowers default), "
        "`venue=<exchange>:<loss>` (a share of USDe's backing at that venue lost; Ethena), "
        "`sky=<source>:<loss>` (a share of a Sky source lost, e.g. `sky=spark:0.2`).",
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


class AfterRequest(BaseModel):
    """A vault after an incident that began at block `since` (`analyze --vault V --since BLOCK`)."""

    vault: str = Field(description="Vault V2 address.")
    since: int = Field(gt=0, description="The block the incident began at.")
    at: int | None = Field(default=None, gt=0, description="The block to read now; default the head (live).")
    shocks: list[str] = Field(
        min_length=1,
        description="The incident in full, as `analyze --shock`: `token=<collateral>:<fall>`, `venue=…` or `sky=…`; "
        "the part the oracle already took is not applied again.",
        examples=[["token=PT-reUSD-10DEC2026:0.10"]],
    )
    user: str | None = Field(default=None, description="Depositor address; default the largest.")
    horizon: float = Field(default=30.0, gt=0, le=365, description="Days of yield given up by leaving.")
    exit_cost: float | None = Field(default=None, ge=0, lt=1, description="Cost of leaving as a share of what leaves.")
    live: bool = Field(default=False, description="Read the chain (an archive RPC for `since`) instead of recordings.")


class AfterMarket(BaseModel):
    market_id: str
    label: str
    oracle_seen: float = Field(description="The oracle's fall since `since`, as read.")
    pending_drop: float = Field(description="The fall still to come before the oracle reaches the incident's price.")
    unrealised: float = Field(description="Bad debt now, not yet written off, the whole market, loan units.")
    at_full: float
    pending: float = Field(description="Bad debt still to come once the oracle passes the incident on.")
    vault_share: float
    liquidations: int = 0
    repaid: float = 0.0
    written_off: float = 0.0


class AfterResponse(BaseModel):
    """What has landed, what is still at risk, and the verdict on that part only (D228–D231)."""

    vault: str
    name: str
    since: int
    at: int
    depositor: str
    unit_symbol: str
    share_price_since: float
    share_price_at: float
    landed: float = Field(description="The depositor's loss since, on what it still holds: sunk.")
    landed_vault: float
    unrealised: float = Field(description="The vault's part of the bad debt not yet written off.")
    pending: float = Field(description="The vault's part of the loss the oracle has not passed on yet.")
    at_risk: float = Field(description="unrealised + pending: what leaving may still avoid.")
    stay: float
    leave: float
    par: float
    stuck: float
    verdict: Verdict
    reason: str
    exit_cost: float
    markets: list[AfterMarket]
    notes: list[str] = Field(default_factory=list)


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


class ValueAtRisk(BaseModel):
    """What the incident puts at risk, in one block (D227): the figures are the book's, gathered."""

    incident: str = Field(description="The incident the figures are given for, in words.")
    exposure_usd: float = Field(description="Money in the markets the incident hits.")
    loss_usd: float = Field(description="Loss if the incident happens, at the size given (no probability).")
    loss_share: float = Field(description="That loss over the book's value.")
    pockets_hit: int
    pockets: int
    worst_pocket: str | None = None
    worst_pocket_loss_usd: float = 0.0
    p95_usd: float | None = Field(default=None, description="95 % worst case given the incident (with `conditional`).")
    p99_usd: float | None = Field(default=None, description="99 % worst case given the incident (with `conditional`).")
    leave_cost_usd: float = Field(description="Certain cost of leaving the hit pockets now.")
    saved_usd: float = Field(description="What leaving them saves if the incident happens.")
    beyond_markets: int = Field(description="Other markets the incident reaches, outside the book.")
    beyond_by_unit: dict[str, float] = Field(description="Their lenders' loss, by loan unit (USDC, EURCV…).")
    returned_usd: float = Field(
        default=0.0,
        description="Liquidity the liquidations free (repaid debt), withdrawable once they have; 0 if none.",
    )
    loss_is_whole_vaults: bool = Field(
        description="`vault` weighting: the loss counts each vault whole; the draw, the cost of leaving and the saving "
        "are the followed depositors'."
    )
    lines: list[str] = Field(description="The block in words, as the CLI prints it.")


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
    exit_impact: float | None = Field(
        default=None, description="Slippage against the oracle selling what the liquidations seize (KyberSwap)."
    )
    exit_capacity: float | None = Field(default=None, description="Largest size the aggregator routes, loan token.")
    exit_source: str = Field(default="", description="KyberSwap (quoted), registry (measured by hand) or empty.")
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
    zama: list[str] = Field(
        default_factory=list, description="For a Zama confidential vault: the confidential share and the two exits."
    )
    returned_liquidity: float = Field(
        default=0.0,
        description="What the vault can withdraw more once liquidators have repaid (asset units); 0 if nobody "
        "liquidates.",
    )


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
    value_at_risk: ValueAtRisk | None = None


class IncidentResponse(BaseModel):
    """The book's sum and headline, and each vault's detail (one vault: a book of one)."""

    book: BookIncident
    vaults: list[VaultIncident]


# --- a failure propagated through the dependency graph: `shock.trace` and `shock.run_sweep` (docs/model/shock-trace.md)


class ShockGraph(BaseModel):
    target: str = Field(description="Pass it as `vault` (or `user`) to the shock routes to run offline.")
    vaults: list[str]
    users: list[str]
    block: int
    siblings: bool


class ShockTarget(BaseModel):
    node: str = Field(description="Address or id; use it before the colon of a shock.")
    label: str
    kind: str
    oracle_class: str | None = None
    held: int = Field(description="Markets of the vault (or the user) whose price this node enters.")
    siblings: int = Field(description="Sibling markets whose price it enters.")
    markets: list[str]


class ShockRequest(BaseModel):
    vault: list[str] = Field(default_factory=list, description="Vault V2 addresses: GET /api/shock/graphs offline.")
    user: list[str] = Field(default_factory=list, description="Addresses whose borrows seed the graph.")
    shocks: list[str] = Field(
        min_length=1,
        description="As `shock --shock`: `<node>:<mode>[:<size>]`, node an address, a market id or a unique label "
        "fragment; mode reads-low, reads-high, frozen or price. Applied together.",
        examples=[["Ojo PT:reads-low:10%"]],
    )
    siblings: bool = Field(default=True, description="Include the sibling markets (live only: a recording fixes it).")
    live: bool = Field(default=False, description="Read the chain instead of the recording (nothing is saved).")


class ShockSweepRequest(BaseModel):
    vault: list[str] = Field(default_factory=list)
    user: list[str] = Field(default_factory=list)
    mode: Literal["reads-low", "reads-high", "frozen", "price"]
    size: str | None = Field(default=None, description="e.g. `10%`; none for frozen.", examples=["10%"])
    top: int = Field(default=15, ge=1, le=200)
    siblings: bool = True
    live: bool = False


class ShockSweepRow(BaseModel):
    node: str
    label: str
    kind: str
    vault_loss: float
    markets_hit: int
    worst_market: str | None = None
    worst_market_loss: float


class ShockSweep(BaseModel):
    block: int
    mode: str
    size: float | None = None
    ranking: list[ShockSweepRow] = Field(description="Ranked by the vaults' total loss.")


class ShockTrace(BaseModel):
    """The propagation as data: the shape is `docs/model/shock-trace.md`; the inner objects are kept open."""

    format: str
    block: int | None = None
    as_of: str | None = None
    note: str
    shocks: list[dict[str, Any]]
    converged: bool
    evaluations: int
    graph: dict[str, Any]
    rules: dict[str, Any]
    steps: list[dict[str, Any]]
    evaluations_log: list[dict[str, Any]]
    waves: list[dict[str, Any]]
    nodes: dict[str, Any]
    paths: dict[str, list[int]]


# --- a past incident replayed: `backtest.Backtest`


class BacktestSummary(BaseModel):
    episode: str
    title: str
    markets: int
    recorded: bool = Field(description="False: GET /api/backtest/{episode} answers 404 until it is recorded.")


class MarketBacktest(BaseModel):
    market_id: str
    label: str
    loan_symbol: str
    oracle_fall: float
    borrowers: int
    predicted_positions: int
    predicted_debt: float
    predicted_bonus: float
    predicted_bad_debt: float
    realised_positions: int
    realised_events: int
    realised_repaid: float
    realised_bonus: float
    realised_bad_debt: float
    missed: list[str] = Field(default_factory=list, description="Liquidated, not predicted.")
    extra: list[str] = Field(default_factory=list, description="Predicted, not liquidated.")
    extra_later: list[str] = Field(default_factory=list)
    extra_defended: list[str] = Field(default_factory=list)
    left_debt: float = 0.0
    left_dust: int = 0
    from_sale: dict[str, Any] | None = None


class Backtest(BaseModel):
    episode: str
    title: str
    before_block: int
    blocks: tuple[int, int] = Field(description="First and last liquidation block.")
    markets: list[MarketBacktest]
    notes: list[str]
    pool: dict[str, Any] | None = Field(default=None, description="The Pendle pool behind the oracle (D208).")
    lines: list[str] = Field(description="The CLI's table, line by line.")
