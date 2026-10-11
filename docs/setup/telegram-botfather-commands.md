# BotFather commands

The commands of Telegram's **@BotFather**, which creates and configures bots, as BotFather listed them on 2026-10-11. The alert bot of this project is `@AgenceTousRiskBot` (design and setup: `TELEGRAM_BOT.md`). The last column says what each command is for here: most are unused.

Manual: <https://core.telegram.org/bots>.

## Create and edit bots

| Command | What it does | Use for this project |
|---|---|---|
| `/newbot` | create a new bot | done: `@AgenceTousRiskBot` |
| `/mybots` | edit your bots (menu with the settings below) | as needed |
| `/setname` | change a bot's name | optional |
| `/setdescription` | change the bot description | optional, for the demo |
| `/setabouttext` | change the bot's about info | optional, for the demo |
| `/setuserpic` | change the bot's profile photo | optional, for the demo |
| `/setcommands` | change the list of commands shown to users | only once the bot takes commands (`/status`, `/mute`: "Later" in `TELEGRAM_BOT.md`) |
| `/deletebot` | delete a bot | after the project, if unused |

## Bot settings

| Command | What it does | Use for this project |
|---|---|---|
| `/token` | get the authorization token | to read it again; it goes in `keys.ini` `[alerts] telegram_bot_token` |
| `/revoke` | revoke the bot's access token (issues a new one, the old one stops working) | **if the token leaks**: then put the new one in `keys.ini` |
| `/setinline` | toggle [inline mode](https://core.telegram.org/bots/inline) | not needed |
| `/setinlinegeo` | toggle [inline location requests](https://core.telegram.org/bots/inline#location-based-results) | not needed |
| `/setinlinefeedback` | change [inline feedback](https://core.telegram.org/bots/inline#collecting-feedback) settings | not needed |
| `/setjoingroups` | whether the bot can be added to groups | set to **Disable** once it is in the alert channel, so nobody adds it elsewhere |
| `/setprivacy` | toggle [privacy mode](https://core.telegram.org/bots/features#privacy-mode) in groups | leave on (default); it does not affect posting to a channel |

## Web apps

| Command | What it does | Use for this project |
|---|---|---|
| `/myapps` | edit your [web apps](https://core.telegram.org/bots/webapps) | not needed |
| `/newapp` | create a new web app | not needed |
| `/listapps` | list your web apps | not needed |
| `/editapp` | edit a web app | not needed |
| `/deleteapp` | delete a web app | not needed |

## Games

| Command | What it does | Use for this project |
|---|---|---|
| `/mygames` | edit your [games](https://core.telegram.org/bots/games) | not needed |
| `/newgame` | create a new game | not needed |
| `/listgames` | list your games | not needed |
| `/editgame` | edit a game | not needed |
| `/deletegame` | delete a game | not needed |
