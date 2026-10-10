# Running riskdep through eRPC

eRPC is an open-source RPC proxy. Run it on your machine with the repository's `erpc.yaml`, point riskdep at it with one environment variable, and riskdep's Ethereum requests are spread over six free endpoints instead of one. **It is optional**: without it, riskdep calls publicnode directly, as before.

## Contents

- [Why](#why)
- [Do I need it?](#do-i-need-it)
- [Set it up](#set-it-up)
- [Check that it works](#check-that-it-works)
- [Turn it off](#turn-it-off)
- [What does not change](#what-does-not-change)
- [Troubleshooting](#troubleshooting)
- [Changing the upstreams](#changing-the-upstreams)

## Why

riskdep reads everything on-chain through the free publicnode RPC. A `graph` run reads hundreds of contracts, and the borrowers of every market, in batches of up to 200 calls. Under that load publicnode throttles. It answers HTTP 429 with a `Rate limit exceeded` error on every call of the batch.

riskdep now waits and resends a throttled batch: 2, 4, … 12 s, up to 6 times. Nothing is lost, but a long run gets slow. Through eRPC, a throttled call is retried at once on another endpoint, and answers already given are served from a cache.

Measured on 2026-10-10:

| Run | Direct to publicnode | Through eRPC |
|---|---|---|
| `graph --vault 0xE018…1965` (RockawayX USDC Yield, 6 held markets and their siblings) | 43 s | 20 s |
| `graph --example` (Sentora RLUSD Main and two borrowers) | 8 to 12 min, 65 siblings | 3 min, 52 siblings (also with the $1M TVL floor) |

## Do I need it?

- **Tests:** no. They run offline from `fixtures/` and never touch the network.
- **`analyze --demo`, `watch --replay`, `graph --replay`:** no. They are offline too.
- **A live `watch`:** not usually. It polls a few calls every 12 s.
- **A live `graph`, or several tools running at once:** recommended.

## Set it up

eRPC is a single binary; Docker is an alternative. The repository pins version **0.3.0** (2026-09-21), the version `erpc.yaml` was tested with. No key or account is needed, and no `.env` file: every endpoint in `erpc.yaml` is public.

### Option A: the binary (Linux, macOS, Windows, WSL)

Download the file for your system from the [0.3.0 release](https://github.com/erpc/erpc/releases/tag/0.3.0): `erpc_linux_x86_64`, `erpc_linux_arm64`, `erpc_darwin_arm64` (Apple silicon), `erpc_darwin_x86_64` or `erpc_windows_x86_64.exe`. Then check it against the release's `checksums.txt`. For Linux x86-64:

```bash
mkdir -p ~/.local/bin && cd ~/.local/bin
curl -sSLO https://github.com/erpc/erpc/releases/download/0.3.0/erpc_linux_x86_64
curl -sSLO https://github.com/erpc/erpc/releases/download/0.3.0/checksums.txt
grep ' erpc_linux_x86_64$' checksums.txt | sha256sum -c -   # must print: erpc_linux_x86_64: OK
chmod +x erpc_linux_x86_64 && mv erpc_linux_x86_64 erpc && rm checksums.txt
```

On macOS, use `shasum -a 256 -c -` instead of `sha256sum -c -`. On Windows, compare the output of `certutil -hashfile erpc_windows_x86_64.exe SHA256` with the line in `checksums.txt`.

Start it from the repository root, in a terminal you leave open:

```bash
~/.local/bin/erpc erpc.yaml
```

It listens on `127.0.0.1:4000`, so only your machine can reach it.

### Option B: Docker

Inside a container the proxy must listen on all interfaces, so run a copy of the config with that one line changed. Docker then publishes the port on localhost only:

```bash
sed 's/httpHostV4: "127.0.0.1"/httpHostV4: "0.0.0.0"/' erpc.yaml > /tmp/erpc-docker.yaml
docker run --rm -p 127.0.0.1:4000:4000 -v /tmp/erpc-docker.yaml:/erpc.yaml ghcr.io/erpc/erpc:0.3.0
```

On Windows and macOS, Docker Desktop must be running first.

### Point riskdep at it

In the shell where you run riskdep:

```bash
export RISKDEP_RPC_URL=http://127.0.0.1:4000/main/evm/1
```

The path is eRPC's: project `main`, EVM chain `1` (Ethereum mainnet). To make it permanent, add the line to your `~/.bashrc` or `~/.zshrc`. It is not a secret, but it is personal (it only works where the proxy runs), so keep it out of committed files.

## Check that it works

```bash
curl -s -X POST http://127.0.0.1:4000/main/evm/1 -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
# {"jsonrpc":"2.0","id":1,"result":"0x18f3d4f"}

uv run python -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --no-siblings
# about 9 s through eRPC
```

## Turn it off

```bash
unset RISKDEP_RPC_URL
```

riskdep calls publicnode directly again. You can stop eRPC with Ctrl-C.

## What does not change

- **Cache keys and fixtures.** Requests are cached and recorded under the public publicnode URL whatever the route, so `fixtures/` stay valid and a recording made through eRPC replays without it.
- **The block-hash cross-check stays independent.** It still calls dRPC directly, and `erpc.yaml` leaves dRPC out of its upstreams. Otherwise the check could compare a node with itself.
- **Results.** The same calls at the same block. On 2026-10-10 the RockawayX graph built through eRPC was identical to the direct one: 74 nodes, 106 edges, same oracle classes.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `data source error: POST https://ethereum-rpc.publicnode.com failed after 3 attempts (sent through RISKDEP_RPC_URL: is the proxy running? …): ConnectionError` | `RISKDEP_RPC_URL` is set but eRPC is not running | start eRPC, or `unset RISKDEP_RPC_URL` |
| `bind: address already in use` when starting eRPC | another program, or an earlier eRPC, holds port 4000 | stop it, or change `httpPortV4` in a local copy of `erpc.yaml` and the port in `RISKDEP_RPC_URL` |
| warning `upstream=blockrazor … could not fetch genesis block … pruned history unavailable` at start | that endpoint keeps only recent history | harmless: riskdep reads recent blocks only |
| `… rate limited 6 time(s) …` from riskdep | every upstream throttled for about 40 s in a row | wait a minute and rerun; it is rare through eRPC |
| Docker: `Cannot connect to the Docker daemon` | Docker Desktop is not running | start it, or use the binary |

## Changing the upstreams

The six upstreams in `erpc.yaml` were chosen on 2026-10-10 by running riskdep's own call patterns against about 20 free endpoints: 30-call `eth_call` batches at a block 60 behind the head, `eth_getLogs`, and `eth_getStorageAt`.
- **Full batches:** publicnode, Blast, MEV Blocker.
- **Batches of 10 at most:** blockrazor, Nodies.
- **Single calls:** Tenderly's public gateway.
- **Left out:** dRPC (the cross-check's second opinion; its free plan also refuses batches above 3), 1RPC (discontinued), and endpoints that needed a key, were down, or refused `eth_getLogs`.

To add or remove one:
1. Edit `erpc.yaml`.
2. Run `erpc validate erpc.yaml`; it must report no error.
3. Run a live `graph` through it.
4. Update the upstream table in `PROVIDERS.md` in the same commit.
