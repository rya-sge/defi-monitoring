"""Dependency graph of an address's Morpho positions and of vaults, as JSON and as an interactive HTML page.

Node types follow ANALYSIS_MONITORING.md §1:
  Actor     whose capital is at stake: an address with positions, or a Vault V2 (adapters folded in)
  Pool      where liquidity sits and is priced: a Blue market, a Pendle pool
  Asset     a token; a vault's share token only where another protocol reuses it (an oracle conversion)
  Oracle    a market oracle and the feeds it reads
  Admin     who decides for a vault: owner, curator, allocators, sentinels
  External  off-chain dependencies of a yield source (registry.json)
Every edge comes from an on-chain attribute or a role getter, with the amount it carries where one exists.
"""

from __future__ import annotations

import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from eth_abi import decode

from . import borrower as B
from . import discover
from . import sources as S
from .discover import REGISTRY
from .positions import discover_user
from .vault import _call, _symbol, _uint, discover_vault, read_state

ORACLE_GETTERS = ["BASE_VAULT()", "BASE_FEED_1()", "BASE_FEED_2()", "QUOTE_VAULT()", "QUOTE_FEED_1()", "QUOTE_FEED_2()"]


class Graph:
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def node(self, nid: str, kind: str, label: str, **details) -> str:
        nid = nid.lower()
        if nid in self.nodes:
            self.nodes[nid]["details"].update({k: v for k, v in details.items() if v is not None})
        else:
            self.nodes[nid] = {
                "id": nid,
                "kind": kind,
                "label": label,
                "details": {k: v for k, v in details.items() if v is not None},
            }
        return nid

    def edge(self, a: str, b: str, rel: str, amount: float | None = None, unit: str | None = None, **details):
        """One edge per (source, target, relation); a repeated edge updates the amount and details."""
        key = (a.lower(), b.lower(), rel)
        for e in self.edges:
            if (e["source"], e["target"], e["rel"]) == key:
                if amount is not None:
                    e["amount"], e["unit"] = amount, unit
                e["details"].update({k: v for k, v in details.items() if v is not None})
                return
        self.edges.append(
            {
                "source": key[0],
                "target": key[1],
                "rel": rel,
                "amount": amount,
                "unit": unit,
                "details": {k: v for k, v in details.items() if v is not None},
            }
        )


def _short(a: str) -> str:
    return f"{a[:6]}…{a[-4:]}"


def _asset(g: Graph, f, token: str, block, symbol: str | None = None) -> str:
    token = token.lower()
    if token not in g.nodes:
        sym = symbol or _symbol(f, token, block)
        reg = REGISTRY["issuers"].get(token) or REGISTRY["stables"].get(token) or {}
        g.node(
            token,
            "Asset",
            sym,
            address=token,
            issuer=reg.get("issuer"),
            source="ERC-20 symbol() on-chain" + (", issuer from registry.json" if reg else ""),
        )
    return token


def _oracle(g: Graph, f, oracle: str, block) -> str:
    oracle = oracle.lower()
    if oracle in g.nodes:
        return oracle
    code = S.rpc(f, "eth_getCode", [oracle, hex(block)]) or ""
    impl = "0x" + code[22:62] if code.startswith("0x363d3d373d3d3d363d73") else None
    res = S.rpc_batch(f, [_call(oracle, s) for s in ORACLE_GETTERS], block)
    feeds = [(name[:-2], "0x" + r[-40:]) for name, r in zip(ORACLE_GETTERS, res) if r and int(r, 16)]
    shape = "Morpho ChainlinkOracleV2" if any(r is not None for r in res) else "custom (no ChainlinkOracleV2 getters)"
    price = _uint(S.rpc_batch(f, [_call(oracle, "price()")], block)[0])
    g.node(
        oracle,
        "Oracle",
        f"Oracle {_short(oracle)}",
        address=oracle,
        shape=shape,
        implementation=impl,
        price_raw=str(price) if price is not None else "reverts",
        source="price() and getters read on-chain",
    )
    for name, addr in feeds:
        desc = S.rpc_batch(f, [_call(addr, "description()")], block)[0]
        label = name
        if desc:
            try:
                label = decode(["string"], bytes.fromhex(desc[2:]))[0]
            except Exception:
                pass
        if "VAULT" in name:
            # a vault share whose exchange rate the oracle applies: an asset reused by the oracle, not an actor
            fid = g.node(
                addr,
                "Asset",
                f"{_symbol(f, addr, block)} (vault share)",
                address=addr,
                role_in_oracle=name,
                source="oracle getter, symbol() on-chain",
            )
            g.edge(oracle, fid, "converts through")
        else:
            fid = g.node(
                addr, "Oracle", label, address=addr, role_in_oracle=name, source="oracle getter, description() on-chain"
            )
            g.edge(oracle, fid, "reads")
    return oracle


def _market(g: Graph, f, m: B.BorrowMarket, block, quotes_pt: bool = True) -> str:
    mid = g.node(
        m.id,
        "Pool",
        f"Blue {m.collateral_symbol}/{m.loan_symbol}",
        market_id=m.id,
        lltv=f"{m.lltv:.1%}",
        irm=m.irm,
        source="Morpho Blue idToMarketParams on-chain",
    )
    loan = _asset(g, f, m.loan_token, block, m.loan_symbol)
    coll = _asset(g, f, m.collateral_token, block, m.collateral_symbol)
    g.edge(mid, loan, "lends")
    g.edge(mid, coll, "takes as collateral")
    g.edge(mid, _oracle(g, f, m.oracle, block), "priced by")
    if quotes_pt and m.collateral_symbol.upper().startswith("PT-") and f"pendle:{m.collateral_token}" not in g.nodes:
        try:
            pm = discover.find_pendle_market(f, m.collateral_token)
        except (S.SourceError, S.CacheMiss):
            return mid
        pool = g.node(
            f"pendle:{m.collateral_token}",
            "Pool",
            f"Pendle {pm['name']} pool",
            address=pm["address"],
            expiry=pm["expiry"][:10],
            source="Pendle API markets",
        )
        g.edge(coll, pool, "trades in / redeems through")
        und = pm["underlyingAsset"].split("-", 1)[-1].lower()
        uid = _asset(g, f, und, block)
        g.edge(pool, uid, "yield source")
        reg = REGISTRY["issuers"].get(und)
        for i, dep in enumerate((reg or {}).get("dependencies", [])):
            ext = g.node(f"ext:{und}:{i}", "External", dep, source="registry.json")
            g.edge(uid, ext, "relies on")
    return mid


def _suppliers(g: Graph, f: S.Fetcher, m: B.BorrowMarket, block) -> None:
    """The main lenders of a market as actors (borrower.top_suppliers, D41)."""
    for sp in B.top_suppliers(f, m, block):
        kind = {"Vault V2": "Vault V2 (capital provider)", "Vault V1": "Vault V1 / MetaMorpho (capital provider)"}.get(
            sp.kind, "lender"
        )
        aid = g.node(
            sp.actor,
            "Actor",
            sp.label,
            address=sp.actor,
            actor_type=kind,
            adapter=sp.address if sp.address != sp.actor else None,
            source="market's top suppliers from the Morpho API; amounts on-chain",
        )
        g.edge(
            aid,
            m.id,
            "supplies",
            sp.assets / 10**m.loan_decimals,
            m.loan_symbol,
            share_of_market=f"{sp.share:.1%}",
            through_adapter=sp.address if sp.address != sp.actor else None,
            note="its withdrawal raises utilisation and the borrow rate of the market",
        )


def build(f: S.Fetcher, block: int, user: str | None = None, vaults: list[str] | None = None) -> Graph:
    g = Graph()
    vaults = [v.lower() for v in (vaults or [])]
    if user:
        user = user.lower()
        up = discover_user(f, user)
        pos = g.node(
            f"user:{user}",
            "Actor",
            f"Address {_short(user)}",
            address=user,
            actor_type="address with positions",
            source="Morpho API userByAddress (positions), Morpho Blue position() on-chain (amounts)",
        )
        if up.borrows:
            markets = B.discover_markets(f, up.borrows, block)
            states = B.read_borrows(f, markets, user, block)
            for mid, m in markets.items():
                st = states[mid]
                node = _market(g, f, m, block)
                hf = st.hf(m.lltv)
                g.edge(
                    pos,
                    node,
                    "borrows from",
                    st.debt / 10**m.loan_decimals,
                    m.loan_symbol,
                    collateral=f"{st.collateral / 10**m.collateral_decimals:,.2f} {m.collateral_symbol}",
                    health_factor=None if hf is None else round(hf, 4),
                    liquidation_at=None if hf in (None, math.inf) else f"-{1 - 1 / hf:.2%} oracle fall",
                )
                _suppliers(g, f, m, block)
        vaults += [v for v in up.vaults if v not in vaults]
    for va in vaults:
        view = discover_vault(f, va, block)
        st = read_state(f, view, block, user if user else None)
        unit = 10**view.decimals
        vid = g.node(
            va,
            "Actor",
            f"Vault {view.name}",
            address=va,
            actor_type="Vault V2 (capital provider)",
            total_assets=f"{st.total_assets / unit:,.0f} {view.asset_symbol}",
            idle=f"{st.idle / unit:,.0f} {view.asset_symbol}",
            plain_withdrawal_capacity=f"{st.withdrawable / unit:,.0f} {view.asset_symbol}",
            adapters=", ".join(f"{a.address} ({a.kind})" for a in view.adapters),
            source="Vault V2 getters on-chain",
        )
        g.edge(vid, _asset(g, f, view.asset, block, view.asset_symbol), "denominated in")
        if user and st.depositor_shares:
            g.edge(f"user:{user}", vid, "deposits in", st.depositor_assets / unit, view.asset_symbol)
        for a in view.adapters:
            for mp in a.markets.values():
                ms = st.markets[mp.id]
                m = B.BorrowMarket(
                    mp.id,
                    mp.loan_token,
                    mp.collateral_token,
                    mp.oracle,
                    mp.irm,
                    int(round(mp.lltv * 1e18)),
                    view.asset_symbol,
                    mp.collateral_symbol,
                )
                node = _market(g, f, m, block)
                g.edge(
                    vid,
                    node,
                    "supplies",
                    ms.vault_assets / unit,
                    view.asset_symbol,
                    share_of_vault=f"{ms.vault_assets / st.total_assets:.1%}" if st.total_assets else None,
                    share_of_market=f"{ms.vault_assets / ms.total_supply_assets:.1%}"
                    if ms.total_supply_assets
                    else None,
                    through_adapter=a.address,
                    utilization=f"{ms.utilization:.1%}",
                )
        # admins: owner and curator on-chain; allocators and sentinels listed by the API, each confirmed on-chain
        owner, curator = (
            ("0x" + r[-40:]).lower() if r else None
            for r in S.rpc_batch(f, [_call(va, "owner()"), _call(va, "curator()")], block)
        )
        roles: dict[str, list[str]] = {}
        for addr, role in ((owner, "owner"), (curator, "curator")):
            if addr:
                roles.setdefault(addr, []).append(role)
        try:
            d = S.morpho(
                f,
                """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
                    allocators{ allocator{address} } sentinels{ sentinel{address} } } }""",
                {"a": va},
            )["vaultV2ByAddress"]
            cand = [(x["allocator"]["address"].lower(), "allocator") for x in d["allocators"]] + [
                (x["sentinel"]["address"].lower(), "sentinel") for x in d["sentinels"]
            ]
            checks = S.rpc_batch(
                f,
                [
                    _call(va, "isAllocator(address)" if r == "allocator" else "isSentinel(address)", ["address"], [a])
                    for a, r in cand
                ],
                block,
            )
            for (addr, role), ok in zip(cand, checks):
                if _uint(ok):
                    roles.setdefault(addr, []).append(role)
        except (S.SourceError, S.CacheMiss, KeyError, TypeError):
            pass
        verb = {
            "owner": "owns (sets curator, sentinels)",
            "curator": "curates (timelocked changes)",
            "allocator": "allocates (immediate, within caps)",
            "sentinel": "can de-risk (lower caps, revoke)",
        }
        for addr, rs in roles.items():
            nid = g.node(
                f"admin:{addr}",
                "Admin",
                f"{' + '.join(rs)} {_short(addr)}",
                address=addr,
                source="owner()/curator() on-chain; allocators and sentinels from the Morpho API, "
                "confirmed with isAllocator()/isSentinel()",
            )
            for r in rs:
                g.edge(nid, vid, verb[r])
    return g


CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--panel:#f6f8fa;--line:#d1d9e0;
--Actor:#0072B2;--Pool:#009E73;--Asset:#E69F00;--Oracle:#CC79A7;--Admin:#D55E00;--External:#999999;--edge:#8c959f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;
--panel:#151b23;--line:#3d444d;--edge:#6e7681}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--panel:#151b23;--line:#3d444d;--edge:#6e7681}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
.app{display:grid;grid-template-columns:320px 1fr;height:100vh}
aside{background:var(--panel);border-right:1px solid var(--line);padding:16px;overflow:auto}
h1{font-size:1.05rem;margin:0 0 4px}h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:18px 0 6px}
.muted{color:var(--muted);font-size:.85rem}#cy{width:100%;height:100%}
.legend label{display:flex;align-items:center;gap:8px;margin:3px 0;cursor:pointer}
.sw{width:14px;height:14px;border-radius:3px;display:inline-block;border:1px solid var(--line)}
.sw.round{border-radius:50%}.sw.diamond{transform:rotate(45deg) scale(.8)}
input[type=search]{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
table{border-collapse:collapse;width:100%;font-size:.82rem}td{border-bottom:1px solid var(--line);padding:4px 2px;vertical-align:top;word-break:break-word}
td:first-child{color:var(--muted);width:38%}button{padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
@media (max-width:760px){.app{grid-template-columns:1fr;grid-template-rows:auto 70vh;height:auto}aside{border-right:0;border-bottom:1px solid var(--line)}}
"""

SHAPES = {
    "Actor": "round-rectangle",
    "Pool": "ellipse",
    "Asset": "round-tag",
    "Oracle": "diamond",
    "Admin": "triangle",
    "External": "rectangle",
}
DESCR = {
    "Actor": "whose capital is at stake: an address, a Vault V2",
    "Pool": "where liquidity sits: Blue market, Pendle pool",
    "Asset": "token: loan, collateral, yield source, reused vault share",
    "Oracle": "market oracle and the feeds it reads",
    "Admin": "decides for a vault: owner, curator, allocator, sentinel",
    "External": "off-chain dependency (registry.json)",
}


def to_html(g: Graph, title: str, subtitle: str) -> str:
    data = {"nodes": list(g.nodes.values()), "edges": g.edges}
    counts = {k: sum(1 for n in g.nodes.values() if n["kind"] == k) for k in SHAPES}
    legend = "".join(
        f'<label><input type="checkbox" checked data-kind="{k}"> <span class="sw" style="background:var(--{k})"></span>'
        f'<b>{k}</b> <span class="muted">({counts[k]}) {html.escape(DESCR[k])}</span></label>'
        for k in SHAPES
        if counts[k]
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Morpho Dependency Graph</title>
<style>{CSS}</style></head><body><div class="app"><aside>
<h1>{html.escape(title)}</h1><p class="muted">{html.escape(subtitle)}</p>
<h2>Node types</h2><div class="legend">{legend}</div>
<p class="muted">Shapes repeat the colour: rounded box Actor, ellipse Pool, tag Asset, diamond Oracle, triangle Admin, square External.
Edge width grows with the amount carried (log scale, in the token of the edge). Zoom in to read asset, oracle and off-chain labels; click a node to isolate its neighbours.</p>
<h2>Find</h2><input type="search" id="q" placeholder="symbol, address, market id…">
<p><button id="fit">Fit</button> <button id="lay">Re-layout</button></p>
<h2>Selection</h2><div id="info" class="muted">Click a node or an edge.</div>
</aside><div id="cy" role="img" aria-label="Interactive dependency graph"></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<script>
const DATA={json.dumps(data, default=str)};
const SHAPES={json.dumps(SHAPES)};
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt=x=>x==null?"":(Math.abs(x)>=1e6?(x/1e6).toFixed(2)+"M":Math.abs(x)>=1e3?(x/1e3).toFixed(1)+"k":x.toFixed(2));
const els=[...DATA.nodes.map(n=>({{data:{{id:n.id,label:n.label,kind:n.kind,details:n.details}}}})),
 ...DATA.edges.map((e,i)=>({{data:{{id:"e"+i,source:e.source,target:e.target,rel:e.rel,amount:e.amount,unit:e.unit,details:e.details,
   w:e.amount?Math.min(10,1+Math.log10(1+e.amount)/1.2):1,label:e.amount>=1?fmt(e.amount)+" "+(e.unit||""):""}}}}))];
const cy=cytoscape({{container:document.getElementById("cy"),elements:els,wheelSensitivity:0.2,
 style:[{{selector:"node",style:{{"background-color":e=>css("--"+e.data("kind")),"shape":e=>SHAPES[e.data("kind")]||"ellipse",
   "label":"data(label)","font-size":10,"color":css("--fg"),"text-valign":"bottom","text-margin-y":4,"width":26,"height":26,
   "text-wrap":"wrap","text-max-width":120,"border-width":1,"border-color":css("--line")}}}},
  {{selector:'node[kind="Actor"]',style:{{"width":44,"height":30,"font-weight":"bold","font-size":11,"text-max-width":90}}}},
  {{selector:'node[kind="Asset"],node[kind="Oracle"],node[kind="External"]',style:{{"min-zoomed-font-size":9}}}},
  {{selector:"edge",style:{{"width":"data(w)","line-color":css("--edge"),"target-arrow-color":css("--edge"),
   "target-arrow-shape":"triangle","curve-style":"bezier","opacity":0.75,"label":"data(label)","font-size":8,
   "color":css("--muted"),"text-rotation":"autorotate","text-background-color":css("--bg"),"text-background-opacity":0.8}}}},
  {{selector:".faded",style:{{"opacity":0.08}}}},{{selector:":selected",style:{{"border-width":3,"border-color":css("--fg"),"line-color":css("--fg")}}}}],
 layout:{{name:"preset"}}}});
// roots passed as a collection: ids such as "0x6dc5…" start with a digit and make a CSS selector fail
const roots=()=>cy.nodes().filter(n=>n.data("kind")==="Actor"||n.data("kind")==="Admin");
const relayout=()=>cy.layout({{name:"breadthfirst",directed:true,spacingFactor:1.5,roots:roots()}}).run();
relayout();
function row(k,v){{if(v==null||v==="")return"";const s=String(v);const link=/^0x[0-9a-f]{{40}}$/.test(s)?
 `<a href="https://etherscan.io/address/${{s}}" target="_blank" rel="noopener">${{s}}</a>`:s.replace(/[&<>]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));
 return `<tr><td>${{k.replace(/_/g," ")}}</td><td>${{link}}</td></tr>`}}
cy.on("tap","node",ev=>{{const d=ev.target.data();const nb=ev.target.closedNeighborhood();cy.elements().addClass("faded");nb.removeClass("faded");
 let h=`<b>${{d.label}}</b> <span class="muted">${{d.kind}}</span><table>`+Object.entries(d.details).map(([k,v])=>row(k,v)).join("");
 const out=ev.target.outgoers("edge").map(e=>row("→ "+e.data("rel"),cy.getElementById(e.data("target")).data("label")+(e.data("amount")?" · "+fmt(e.data("amount"))+" "+(e.data("unit")||""):""))).join("");
 const inc=ev.target.incomers("edge").map(e=>row("← "+e.data("rel"),cy.getElementById(e.data("source")).data("label")+(e.data("amount")?" · "+fmt(e.data("amount"))+" "+(e.data("unit")||""):""))).join("");
 document.getElementById("info").innerHTML=h+out+inc+"</table>"}});
cy.on("tap","edge",ev=>{{const d=ev.target.data();cy.elements().addClass("faded");ev.target.removeClass("faded");ev.target.connectedNodes().removeClass("faded");
 document.getElementById("info").innerHTML=`<b>${{cy.getElementById(d.source).data("label")}}</b> → ${{d.rel}} → <b>${{cy.getElementById(d.target).data("label")}}</b><table>`+
 row("amount",d.amount?fmt(d.amount)+" "+(d.unit||""):"")+Object.entries(d.details||{{}}).map(([k,v])=>row(k,v)).join("")+"</table>"}});
cy.on("tap",ev=>{{if(ev.target===cy){{cy.elements().removeClass("faded");document.getElementById("info").textContent="Click a node or an edge."}}}});
document.querySelectorAll("[data-kind]").forEach(cb=>cb.addEventListener("change",()=>{{
 cy.nodes(`[kind="${{cb.dataset.kind}}"]`).style("display",cb.checked?"element":"none")}}));
document.getElementById("q").addEventListener("input",e=>{{const q=e.target.value.toLowerCase();cy.elements().removeClass("faded");if(!q)return;
 const hit=cy.nodes().filter(n=>(n.data("label")+" "+n.id()+" "+JSON.stringify(n.data("details"))).toLowerCase().includes(q));
 cy.elements().addClass("faded");hit.closedNeighborhood().removeClass("faded")}});
document.getElementById("fit").onclick=()=>cy.fit(undefined,30);
document.getElementById("lay").onclick=relayout;
</script></body></html>"""


def to_dict(g: Graph, title: str, subtitle: str) -> dict:
    """The graph as plain JSON-ready data. `write` persists this; the API serves it."""
    return {"title": title, "subtitle": subtitle, "nodes": list(g.nodes.values()), "edges": g.edges}


def write(g: Graph, out_html: Path, title: str, subtitle: str) -> tuple[Path, Path]:
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(to_html(g, title, subtitle))
    out_json = out_html.with_suffix(".json")
    out_json.write_text(json.dumps(to_dict(g, title, subtitle), indent=1, default=str))
    return out_html, out_json


def subtitle_for(block: int) -> str:
    return (
        f"Ethereum mainnet, read at block {block:,} "
        f"({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}). "
        "Positions found with the Morpho API; amounts, parameters, oracles and roles read on-chain."
    )
