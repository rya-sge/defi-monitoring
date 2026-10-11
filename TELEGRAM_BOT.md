# Telegram bot: push the watch alerts to a private channel

How `riskdep` could post its alerts to a private Telegram channel, during the demo and beyond. This is the push-alert step D2 of `docs/analysis/NEXT_STEP.md`; `keys.example.ini` already reserves `[alerts] telegram_bot_token` and `telegram_chat_id` for it. **Status (2026-10-11): built** as `python3 -m riskdep notify` (`riskdep/notify.py`, tests in `tests/test_notify.py`); the bot is `@AgenceTousRiskBot`, its credentials are in `keys.ini`, and a test message reached the channel. Usage: `README.md`, section notify.

## Recommendation

A **separate local process, `riskdep notify`, that tails `out/watch-*.jsonl` and posts each new alert to the channel** (option B below). It needs no change to the watch loop, no public server and no inbound port; it works the same on a live `watch` and on a `watch --replay`, so the demo can show a real recorded alert landing on a phone. It sends **only when there is a risk**: an alert at or above the level (warn by default). No heartbeat, no periodic message.

## What already exists

- Every alert of `watch` and `watch --user` is appended, one JSON object per line, to `out/watch-<target>.jsonl` (`Printer.alert` in `riskdep/watch.py`), whatever `--level` the terminal shows. Fields: `level` (`info` / `warn` / `critical`), `block`, `tx`, `event`, `title`, `detail`, `depositor_impact`, `data`.
- `GET /api/alerts?target=…&since=<block>&level=…` reads the same files with a block cursor (`riskdep/api/routes/alerts.py`).
- `docs/reference/alert-runbook.md` says what each alert means and what to do: a message can link to its row.

## The options

| | How | For | Against |
|---|---|---|---|
| A. In the watch loop | a notifier called from `Printer.alert` | fewest moving parts | a slow or failing Telegram call blocks or crashes the poll loop, which must save its cursor last; mixes delivery into the watcher |
| **B. Sidecar tailing the JSONL** | `riskdep notify` follows the files, keeps its own byte offset per file, posts | watcher untouched; restartable; replays work; one notifier for every target | a second process to start |
| C. Sidecar polling the API | same as B, through `GET /api/alerts` | already has the cursor and the level filter | needs uvicorn running too; one more failure point for nothing B lacks |
| D. Bot with a webhook | Telegram calls a public HTTPS URL of ours | needed only for inbound commands | needs a tunnel (ngrok, cloudflared) or a server; not needed to *send* |

Sending never needs a server: it is one outbound `POST https://api.telegram.org/bot<token>/sendMessage`. A "local server" is only needed to *receive* commands, and even then long polling (`getUpdates`) avoids any public URL (see "Later").

B keeps the project's rule that the watcher is its own process writing `out/watch-*.jsonl` and everything else reads it.

## Design of option B

**Process.** `python3 -m riskdep notify [--level warn] [--target <name>] [--from-start]`, run in its own terminal next to `watch`. Every 2 s it reads new lines from each `out/watch-*.jsonl`, filters, formats and sends.

**State.** `out/notify.state.json`: per file, the byte offset already sent. Saved **after** a successful send, like the watch cursor, so a restart neither skips nor resends. By default a new file starts at its end (no flood of old alerts); `--from-start` sends the backlog, for the demo.

**Filtering.**
- Minimum level, default `warn`; `info` is too frequent for a phone.
- **Standing findings once.** At start, `watch` prints standing findings (`Exposure`, `Caps`, `NoNoticeChange`…) with `tx: null`; after a restart they come again. Deduplicate on `(target, event, title)` over a window of 1800 blocks, about 6 h (`registry.json` `notify.dedup_blocks`; blocks rather than wall time, so replays behave like live runs), kept in the state file, so only new facts are pushed.
- **Startup digest.** Alerts with `tx: null` from the same block are grouped into one message ("RockawayX USDC Yield, start: 2 critical, 5 warn"), followed by one message per critical.

**Message.** `parse_mode=HTML`, **one message per incident**: every alert of one block, so a cause and its consequences arrive together. Decision first, plain words, details folded (the Act 2 message of `scripts/demo-rock/`):

```
🔴 RockawayX Tori Ecosystem — The code behind a price or a token was replaced
RedStone Price Feed for strUSD_FUNDAMENTAL (feed of the oracle of strUSD/USDC) was upgraded
💸 The vault's loss: 1,236,933 USDC · yours 454,103 USDC
👉 Decision: EXIT. Withdraw the 2,374,262 USDC that can leave now: your loss falls from 454,103 to 293,378 USDC.
▸ Details: 6 alerts, block 26,165,574           (expandable quote: each alert in plain words, title and detail)
[ What to do ]  [ Etherscan ]                   (buttons)
```

- The headline is the plain-words meaning of the **cause** (`PLAIN` in `riskdep/notify.py`, from the runbook's "What it means"); alerts are ordered cause first: a change of code or owner, data problems, the price, the losses, the exit.
- The loss and the decision come from `OracleImpact`'s `data` (`vault_loss`, `loss_if_stay`, `loss_if_exit_first`, `can_leave_now`, `verdict`); without it, the depositor's share of the loss when an alert carries one.
- Addresses shortened to `0x1234…abcd`, `(LLTV …)` left out of the headline.
- Buttons: with `--web-url <riskdep web app>`, "Alerts in riskdep" (`/watch?target=<vault>`) and "Vault" (`/?target=<vault>`) open the web app (`scripts/demo-rock/` starts one on `127.0.0.1:5173`, live on the fork); "What to do" opens the runbook section of the cause's alert family; two buttons a row; "Etherscan" opens the transaction, and is left out on a fork (`RISKDEP_FORK`), whose transactions Etherscan does not have.
- `critical` with sound; `warn` and `info` with `disable_notification=true`.
- If Telegram rejects the HTML (HTTP 400), the message is sent once as plain text, so one bad message cannot block the queue.

**Rate limits.** Telegram allows about 20 messages a minute to one group or channel and answers `429` with `retry_after`. When several alerts arrive together, space them at least 3 s apart (no effect when there is nothing to send), honour `retry_after`, and above a burst threshold (say 10 queued) fall back to one digest message.

**Failures never stop anything.** A network error leaves the offset unchanged and retries with backoff; the watcher is unaffected because it never waits on the notifier. `notify` prints "telegram: not configured" and exits if the keys are missing.

**Credentials.** `keys.ini` `[alerts] telegram_bot_token`, `telegram_chat_id` (already in the template). The token is in the URL path, so never log request URLs; never write a response containing it under `fixtures/`.

**Code.** One module, `riskdep/notify.py`: a pure `format(alert, target_name) -> str` and `select(alerts, state, level) -> list`, and a thin `send()` using `requests` (already a dependency). No Telegram library needed.

**Tests (offline).** `format` and `select` on the alerts of a recorded replay (`fixtures/replay/`): level filter, deduplication of standing findings, digest grouping, HTML escaping, length cap. `send` against a stubbed `requests` session: success, `429` with `retry_after`, network error leaving the offset unchanged.

**Repository rules it triggers.** `docs/analysis/PROVIDERS.md` gains the Telegram Bot API (endpoint, limits, trust: it is an outward push, and messages are stored by Telegram); `README.md` gains the command; `registry.json` takes the thresholds (default level, dedup window, send interval, burst size) with their basis, documented in `docs/reference/registry-reference.md`.

## What you need to create and provide

Status checked on 2026-10-11: `keys.ini` exists, is git-ignored and `chmod 600`, and has an `[alerts]` section, but `telegram_bot_token` and `telegram_chat_id` are **empty**. Nothing else is needed: the Bot API is free, needs no account beyond Telegram itself, no payment, no server and no new Python dependency.

| # | What | Status | Where it goes |
|---|---|---|---|
| 1 | A Telegram account, with the app on the phone used in the demo | yours | — |
| 2 | A bot and its **token** (the "API key") | to create | `keys.ini` `[alerts] telegram_bot_token` |
| 3 | A **private channel** | to create | — |
| 4 | The bot added to the channel as an **administrator** allowed to post | to do | — |
| 5 | The channel's **chat id** | to read | `keys.ini` `[alerts] telegram_chat_id` |
| 6 | Teammates and judges invited to the channel | optional | — |
| 7 | Network access to `api.telegram.org` on the demo machine | to check at the venue | — |

### 1. Create the bot and get its token (2 min)

1. In Telegram, open a chat with **@BotFather** (the official one, with the blue check mark).
2. Send `/newbot`.
3. Give it a display name, e.g. `riskdep alerts`.
4. Give it a username ending in `bot`, unique across Telegram, e.g. `riskdep_belem_alerts_bot`.
5. BotFather answers with the token, of the form `123456789:AAH...` (a number, a colon, about 35 characters). That is the bot's only credential: whoever has it can post as the bot and read its updates.

Optional, in the same chat: `/setdescription` and `/setuserpic` for a cleaner look on screen; `/setjoingroups` → Disable, so nobody can add the bot elsewhere. All BotFather commands: `docs/setup/telegram-botfather-commands.md`.

If the token ever leaks (pasted in a chat, committed, shown on the projector): `/revoke` in BotFather, pick the bot, and put the new token in `keys.ini`. The old one stops working at once.

### 2. Create the private channel (1 min)

1. Telegram → New Channel → a name, e.g. `riskdep alerts`.
2. Channel type: **Private**. It then has no public `@name`, only an invite link.
3. Skip adding subscribers for now.

A private **group** works the same way if you prefer that teammates can reply under alerts; the steps below are identical, only the chat id differs.

### 3. Add the bot as administrator (1 min)

1. Channel → Administrators → Add Admin → search the bot's username.
2. Leave only **Post Messages** enabled (no editing, deleting or inviting rights are needed).

A bot cannot post to a channel unless it is an administrator.

### 4. Read the chat id (1 min)

1. Post any message in the channel, e.g. `hello`.
2. On the machine with the token:
   ```bash
   curl -s "https://api.telegram.org/bot<token>/getUpdates" | python3 -m json.tool
   ```
3. In the answer, `result[].channel_post.chat.id` is the chat id: a negative number starting with `-100`, e.g. `-1001234567890`.

If `result` is empty: post another message and run it again (updates are kept 24 h only). If the answer says a webhook is set, run `curl -s "https://api.telegram.org/bot<token>/deleteWebhook"` first. Run this from your terminal, not through an assistant, so the token does not end up in a transcript.

### 5. Put both values in `keys.ini`

`keys.ini` already exists; edit the two empty lines of its `[alerts]` section:

```ini
[alerts]
telegram_bot_token = 123456789:AAH...
telegram_chat_id = -1001234567890
```

Keep it `chmod 600` and never commit it (it is git-ignored). No environment variable and no `.env` file: the project reads secrets from `keys.ini` only.

### 6. Check it works, before any code exists

```bash
curl -s "https://api.telegram.org/bot<token>/sendMessage" \
  -d chat_id=-1001234567890 -d text="riskdep: test"
```

`"ok": true` and the message in the channel means everything on your side is done. Once `notify` is built, `python3 -m riskdep notify --test` does the same from `keys.ini`.

### 7. Invite people and check the venue network

- Channel → Invite Links → create a link, share it with teammates; for the judges, a QR code of the link on a slide lets them follow live on their own phones.
- On the demo machine and network, run the check in step 6 once before the session: some venue or university networks block Telegram.

## The demo

Two terminals and a phone on the projector, all offline except the send:

```bash
python3 -m riskdep notify --level warn --from-start     # terminal 1: the bot
python3 -m riskdep watch --replay                       # terminal 2: the recorded range, alerts land in the channel
```

- Clear `out/watch-<target>.jsonl` and `out/notify.state.json` before the demo, so the channel shows only this run.
- A replay writes its alerts within seconds; the send queue spaces them out, which reads well on screen. `watch --replay --step 1` replays block by block for a slower story.
- No recorded run has a `critical` alert (checked in `out/watch-*.jsonl`): the replays give `warn` alerts such as `Exposure` and `ExitQueue`. Never post the two invented `critical` alerts of `web/src/mocks/alerts.ts`. For a strong closing message, add `notify --post out/book-incident.json`, which sends the headline of an `analyze --book … --shock …` run ("PST −30 %: the book loses 5.2M USD… act first on Huma USDC Main"): real numbers, presented as a scenario.
- Have a fallback: if the venue's network blocks `api.telegram.org`, the terminal and the web Watch page show the same alerts.

## Later

- **Impact in the message.** When detection → impact reaches vaults (`NEXT_STEP.md` A3), a critical alert carries the loss, time to impact and verdict: put them on the first line ("EXIT · loss 3.27M USD · liquidation in ~15 min").
- **Commands by long polling.** `/status` (last block per target, open criticals), `/mute 1h`, `/shock token=PST:0.30` returning the book's headline from `pipeline.incident`. Long polling `getUpdates` from the same local process needs no public URL; accept commands only from the configured chat id.
- **Other channels.** The same sidecar can post to Slack, Discord or ntfy, whose keys are already in `keys.example.ini`; keep `format` channel-neutral and add one `send` per channel.
