# riskdep: DeFi risk dependencies

**How a position's dependencies are found, priced, watched and turned into a stay-or-exit decision**

Ryan Sauge · v1.0 · 2026-10-11

Talk length: about 7 minutes (12 slides, 20 to 40 seconds each)

Source: the repository (`README.md`, `docs/README.md`, `docs/analysis/ARCHITECTURE.md`), the DeFi Risk Dependency Challenge brief (Belem Capital, EPFL Hackathon 2026)

---

## 1. riskdep: DeFi risk dependencies

A Python command-line tool, with an HTTP API and a web interface, for the risk of positions on Morpho (Ethereum): what a position depends on, what an incident costs it, how fast, and whether to stay or leave.

```mermaid
flowchart LR
    P["A DeFi position<br/>vault deposit or borrow"] --> R["riskdep"]
    R --> O["Dependencies, loss,<br/>timing, verdict, alerts"]
    style P fill:#E8EEF9,stroke:#3A5FA0
    style R fill:#E8F5E9,stroke:#2E7D32
    style O fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (20 s):** Built for Belem Capital's challenge at the EPFL Hackathon 2026. Everything shown today runs on real mainnet data, offline from recordings or live.

---

## 2. The question we answer

A dependency of a position is hit: an oracle, an issuer, a market. How much is lost, how fast does it land, and should the holder stay or exit, given that exiting has a cost of its own? The brief judges discovery (30 %), impact (30 %), decision usefulness (25 %) and a working demo on real data (15 %).

```mermaid
flowchart TB
    I["A dependency is hit"] --> L["How much is lost?"]
    L --> T["How fast?"]
    T --> D{"Stay or exit,<br/>given the exit cost?"}
    D -->|"loss avoided worth the cost"| X["Exit"]
    D -->|"cost higher than the loss avoided"| S["Stay"]
    style I fill:#FDEEEE,stroke:#B54A4A
    style L fill:#F0F2F5,stroke:#78909C
    style T fill:#F0F2F5,stroke:#78909C
    style D fill:#E8F5E9,stroke:#2E7D32
    style X fill:#F0F2F5,stroke:#78909C
    style S fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (30 s):** The brief's own example: a book in ten 10 % pockets, one is hit, and unwinding costs 11 %. Exiting is certain and costly, staying is cheap and uncertain. Every part of the tool exists to make that trade-off explicit.

---

## 3. One tool, five modes

Five modes share the same sources and modules. `graph` draws the dependencies, `shock` propagates a failure, `analyze` estimates risk and decides, and the two `watch` modes detect incidents block by block. The chain is authoritative: the APIs find positions, every amount is read on-chain.

```mermaid
flowchart LR
    subgraph SRC["Public sources"]
        RPC["Ethereum RPC"]
        API["Morpho, Pendle,<br/>DefiLlama APIs"]
    end
    subgraph MODES["riskdep"]
        G["graph"]
        SH["shock"]
        AN["analyze"]
        W["watch --vault<br/>watch --user"]
    end
    RPC --> MODES
    API --> MODES
    MODES --> OUT["HTML, JSON,<br/>alerts, HTTP API, web UI"]
    style SRC fill:#E8EEF9,stroke:#3A5FA0
    style MODES fill:#E8F5E9,stroke:#2E7D32
    style RPC fill:#E8EEF9,stroke:#3A5FA0
    style API fill:#E8EEF9,stroke:#3A5FA0
    style G fill:#E8F5E9,stroke:#2E7D32
    style SH fill:#E8F5E9,stroke:#2E7D32
    style AN fill:#E8F5E9,stroke:#2E7D32
    style W fill:#E8F5E9,stroke:#2E7D32
    style OUT fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (35 s):** No key is needed; Etherscan, Nexus and Pharos are optional. Two cross-checks run in the background: the block hash against a second node, and the Morpho API against the chain.

---

## 4. Dependency discovery

From one vault address, riskdep walks down to everything the money depends on: the markets the vault lends in, their oracles and feeds, the issuers of the collateral, and who can change each contract, up to the timelocks above them. Sibling markets that share a collateral or a price input are added around it.

```mermaid
flowchart TB
    V["Vault V2"] --> M["Morpho Blue<br/>markets"]
    M --> O["Oracle"]
    O --> F["Feeds"]
    M --> C["Collateral issuer"]
    F --> A["Proxy admin<br/>and timelock"]
    style V fill:#E8EEF9,stroke:#3A5FA0
    style M fill:#E8F5E9,stroke:#2E7D32
    style O fill:#E8F5E9,stroke:#2E7D32
    style F fill:#E8F5E9,stroke:#2E7D32
    style C fill:#E8F5E9,stroke:#2E7D32
    style A fill:#FDEEEE,stroke:#B54A4A
```

> **Speaker notes (40 s):** Each oracle gets a class: price-tracking, or constant-price when it reports an issuer's rate. That class decides whether a market fall liquidates anyone. On the Belem vault this walk found that one wallet writes the collateral's price, inside a fixed band, and that going below the band needs an upgrade behind a 48-hour timelock.

---

## 5. Probabilities

Each layer gets a yearly probability of an incident. Exploits come from DefiLlama's hack record: a rate for protocols of the same size, times a category multiplier and an age factor, kept between 0.5 % and 15 %. Depegs are judgements written in a registry with their reason. A simulation of 20,000 months turns them into a loss distribution.

```mermaid
flowchart TB
    H["Hack record<br/>size, category, age"] --> P["Prior per layer<br/>per year"]
    R["Registry<br/>depeg, oracle"] --> P
    P --> N["30-day probability"]
    N --> MC["20,000 simulated months"]
    MC --> E["Expected loss,<br/>CVaR 99 %"]
    style H fill:#E8EEF9,stroke:#3A5FA0
    style R fill:#E8EEF9,stroke:#3A5FA0
    style P fill:#E8F5E9,stroke:#2E7D32
    style N fill:#E8F5E9,stroke:#2E7D32
    style MC fill:#E8F5E9,stroke:#2E7D32
    style E fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (40 s):** For the Morpho Blue market of the demo: 34 hacks among 256 large protocols over five years gives 2.66 % a year; the lending multiplier brings Morpho Blue to 5.03 %. The demo position ends on REDUCE: a 6,265 USD expected loss against 5,697 USD of carry. Details in `docs/model/how-probabilities-are-computed.md`.

---

## 6. Impact: the shock engine

When a node fails (an oracle reads low, a collateral falls, a feed freezes), the shock engine re-evaluates every borrower of every market it reaches, applies Morpho's own liquidation and bad-debt rules, and carries the effect along the graph until nothing moves. The output is a loss per market, per vault and per depositor.

```mermaid
flowchart TB
    S["Shock on a node"] --> B["Every borrower<br/>re-evaluated"]
    B --> Q{"Collateral covers<br/>the debt?"}
    Q -->|"covers it"| LQ["Liquidation,<br/>no loss"]
    Q -->|"does not"| BD["Bad debt"]
    BD --> VL["Vault and<br/>depositor loss"]
    style S fill:#FDEEEE,stroke:#B54A4A
    style B fill:#E8F5E9,stroke:#2E7D32
    style Q fill:#E8F5E9,stroke:#2E7D32
    style LQ fill:#F0F2F5,stroke:#78909C
    style BD fill:#FDEEEE,stroke:#B54A4A
    style VL fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (40 s):** The engine is pure, with its transmission rules in the registry or in a file you pass. Example from the README: fxSAVE marked down 30 % leaves 2,284,812 USDC of bad debt in its market, and the f(x) vault takes its share.

---

## 7. Decision: when does leaving pay?

Given the incident, riskdep compares the depositor's loss if it stays with its loss if it leaves first, against the certain cost of leaving. The ratio is a breakeven probability p\*: leave if you believe the incident is more likely than p\*. A Nexus cover price, converted to an implied probability, is shown next to it, never used.

```mermaid
flowchart LR
    C["Cost of leaving<br/>yield given up"] --> PS["p* = cost ÷ loss saved"]
    LS["Loss saved by<br/>leaving first"] --> PS
    PS --> D{"Incident more<br/>likely than p*?"}
    D -->|"more likely"| EX["Leave"]
    D -->|"less likely"| ST["Stay"]
    N["Nexus implied range"] -.-> D
    style C fill:#F0F2F5,stroke:#78909C
    style LS fill:#F0F2F5,stroke:#78909C
    style PS fill:#E8F5E9,stroke:#2E7D32
    style D fill:#E8F5E9,stroke:#2E7D32
    style EX fill:#F0F2F5,stroke:#78909C
    style ST fill:#F0F2F5,stroke:#78909C
    style N fill:#E8EEF9,stroke:#3A5FA0
```

> **Speaker notes (40 s):** Two cases from the recordings. The f(x) vault under a 30 % fxSAVE markdown: leaving pays above 7.92 % over 30 days. The brief's ten-pocket example: leaving costs 110,000 USD for sure against 53,445 saved, so stay. For a book, act first on the vault with the lowest p\*.

---

## 8. Detection: watch

The watcher reads every new block, two blocks behind the head, with three detectors: events (liquidations, upgrades, mints, governance changes), differences between two state reads (oracle moves, bad debt, utilisation), and standing findings at start-up. An incident on-chain is reported about 24 to 36 seconds after its block.

```mermaid
flowchart LR
    B["New block<br/>2 confirmations"] --> EV["Events"]
    B --> SD["State difference"]
    ST["Start-up read"] --> SF["Standing findings"]
    EV --> AL["Alert<br/>info, warn, critical"]
    SD --> AL
    SF --> AL
    style B fill:#E8EEF9,stroke:#3A5FA0
    style EV fill:#E8F5E9,stroke:#2E7D32
    style SD fill:#E8F5E9,stroke:#2E7D32
    style ST fill:#E8EEF9,stroke:#3A5FA0
    style SF fill:#E8F5E9,stroke:#2E7D32
    style AL fill:#F0F2F5,stroke:#78909C
```

> **Speaker notes (40 s):** When a vault's oracle falls 2 % or more, the `OracleImpact` alert already states the vault's loss at the new price, what is liquidatable, the depositor's loss and the verdict. What each alert means and what to do: `docs/reference/alert-runbook.md`.

---

## 9. Seeing it before it lands

Some signals come before the loss. A feed upgrade queued on a timelock is reported when it is scheduled, a full delay before it can execute. Unrealised bad debt is counted the moment the price lands, before any liquidation books it. On a mainnet fork of the Belem vault, the upgrade was reported 48 hours ahead.

```mermaid
flowchart TB
    S["Upgrade scheduled<br/>warn"] --> W["48 hours"]
    W --> U["Upgrade executed<br/>critical"]
    U --> I["Price lands<br/>OracleImpact: loss 215,003"]
    I --> R["Liquidation<br/>bad debt 217,286"]
    style S fill:#E8F5E9,stroke:#2E7D32
    style W fill:#F0F2F5,stroke:#78909C
    style U fill:#FDEEEE,stroke:#B54A4A
    style I fill:#FDEEEE,stroke:#B54A4A
    style R fill:#FDEEEE,stroke:#B54A4A
```

> **Speaker notes (40 s):** The crisis is played on a local fork with the roles that could cause it: the issuer's feed admin, the Midas timelock, a liquidator. `scripts/fork/demo.sh --short` runs it in two minutes. The loss stated when the price landed was 1.1 % from the loss realised four blocks later.

---

## 10. Is the number defensible?

Two checks against reality. A backtest replays the PT-reUSD liquidations of 2026-08-25: from the state 60 blocks before, with the oracle's observed fall, it predicts the same 13 positions and 35.46M USDC liquidatable, against 35.19M repaid. On the fork, a 30 % markdown was predicted at 251,761 EURCV of loss before the crisis; 252,914 was lost.

```mermaid
flowchart LR
    subgraph PRED["Predicted"]
        P1["13 positions<br/>35.46M USDC"]
        P2["251,761 EURCV"]
    end
    subgraph REAL["Observed"]
        R1["13 positions<br/>35.19M USDC repaid"]
        R2["252,914 EURCV"]
    end
    P1 -->|"backtest, 2026-08-25"| R1
    P2 -->|"fork crisis"| R2
    style PRED fill:#E8F5E9,stroke:#2E7D32
    style REAL fill:#E8EEF9,stroke:#3A5FA0
    style P1 fill:#E8F5E9,stroke:#2E7D32
    style P2 fill:#E8F5E9,stroke:#2E7D32
    style R1 fill:#E8EEF9,stroke:#3A5FA0
    style R2 fill:#E8EEF9,stroke:#3A5FA0
```

> **Speaker notes (35 s):** The backtest tests the impact given the incident, not the oracle's fall itself, which is an input. The 0.5 % gap on the fork is the interest accrued during the 48-hour time jump.

---

## 11. Limitations

The design trades some coverage for numbers that can be checked; other gaps are on the roadmap.

```mermaid
flowchart LR
    subgraph BD["By design"]
        B1["Probabilities are base rates<br/>with a stated basis"]
        B2["Layers mostly independent"]
        B3["Issuer data taken<br/>as published on-chain"]
    end
    subgraph NI["Not implemented"]
        N1["Other chains:<br/>Solana, Base"]
        N2["A frozen feed alert<br/>FeedStale"]
        N3["Mempool, reorgs<br/>deeper than 2 blocks"]
    end
    style BD fill:#F0F2F5,stroke:#78909C
    style NI fill:#FDEEEE,stroke:#B54A4A
    style B1 fill:#F0F2F5,stroke:#78909C
    style B2 fill:#F0F2F5,stroke:#78909C
    style B3 fill:#F0F2F5,stroke:#78909C
    style N1 fill:#FDEEEE,stroke:#B54A4A
    style N2 fill:#FDEEEE,stroke:#B54A4A
    style N3 fill:#FDEEEE,stroke:#B54A4A
```

> **Speaker notes (30 s):** The hack record is biased low by survivorship: a protocol a hack destroyed leaves the sample. `docs/analysis/GAP.md` lists that and the other known weaknesses, with what each would take to fix. `analyze`'s Monte Carlo covers Pendle PT collateral on Morpho Blue only.

---

## 12. Conclusion

riskdep answers the brief's question end to end on real data: it finds what a position depends on, prices an incident, states how fast it lands and whether leaving pays, and watches for it live. Every threshold sits in a registry with its reason, and 327 offline tests replay recorded mainnet runs.

```mermaid
flowchart TB
    D["Discover"] --> P["Price"]
    P --> I["Impact"]
    I --> DC["Decide"]
    DC --> W["Watch"]
    style D fill:#E8F5E9,stroke:#2E7D32
    style P fill:#E8F5E9,stroke:#2E7D32
    style I fill:#E8F5E9,stroke:#2E7D32
    style DC fill:#E8F5E9,stroke:#2E7D32
    style W fill:#E8F5E9,stroke:#2E7D32
```

> **Speaker notes (30 s):** To try it: `uv sync`, then the three commands of the README's "answer in five minutes", or `scripts/fork/demo.sh --short` for the live crisis. The documentation index is `docs/README.md`.
