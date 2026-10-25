# MLB The Show 16 revival server (PS3 / RPCS3)

**Play *MLB The Show 16* online again: 1v1 against a friend, both on RPCS3.**

Sony shut down the game's online service in 2020 with update 1.10. This repo is a small private server plus four RPCS3
game patches that bring back **Game Rooms**: join a room, see each other, chat, send a challenge, and play a full game.

![The first online game in years: Mets at Tigers, pitching on a Linux PC and batting on an M1 MacBook Air, both on RPCS3](docs/images/first-1v1.jpg)

> **Status: it works!** First online 1v1 game played on October 25, 2026 (Linux PC vs M1 Mac, same home network).
> Windows vs Windows over the internet is the next goal.
> It's still early: expect rough edges, and please report what you find.

| | |
|---|---|
| ✅ | Online menus unlocked, PSN sign-in through RPCN, login to the game server |
| ✅ | Game Rooms: room list, player list, chat |
| ✅ | Challenging a player, accepting, and the pre-game handshake |
| ✅ | Peer-to-peer connection and **playing a 1v1 game** |
| ❓ | Playing over the internet: the server through Tailscale, the match through RPCN's direct connection. Documented, not tested yet |
| ❓ | Windows: the server, scripts and setup are written for it, but no game has been played on Windows yet |
| ❓ | Reliability: one of the first two attempts dropped before the game started |
| ❓ | Saving results after a game |
| ❌ | Other online modes (Diamond Dynasty, Online Rated, Franchise…): out of scope for now |

## What you need

Every player needs:
- **RPCS3**: [rpcs3.net](https://rpcs3.net/download), on Windows, Linux or macOS.
- **PS3 system firmware**: download `PS3UPDAT.PUP` from Sony's
  [PS3 system software page](https://www.playstation.com/en-us/support/hardware/ps3/system-software/), then install it
  with **File → Install Firmware**.
- **Your own copy of the game, disc version (BCUS01089)**, as a decrypted dump. Dumping the disc on your own PS3 (for
  example with multiMAN or ManaGunZ) gives you one directly. A raw 1:1 disc image has to be decrypted first with your
  disc's key (for example with PS3Dec).
- **The v01.10 update**, from Sony's own update servers. Install it with **File → Install Packages/Raps/Edats**:
  [UP9000-BCUS01089_00-MLB16THESHOWBDPA-A0110-V0100-PE.pkg](http://b0.ww.np.dl.playstation.net/tppkg/np/BCUS01089/BCUS01089_T10/07a5f28c76691db4/UP9000-BCUS01089_00-MLB16THESHOWBDPA-A0110-V0100-PE.pkg)
- **A free RPCN account** (RPCS3's stand-in for PSN), created inside RPCS3.

One player also runs the server: any PC with Python 3.10+. It can be the same machine they play on.

The patches are made for the disc version's v01.10 EBOOT. The digital version (NPUA81353) has a different EBOOT and
isn't supported yet.

## Setup

1. **The host** follows [docs/setup-host.md](docs/setup-host.md): start the server, make a certificate, and let the
   other player reach it (same network, or [Tailscale](https://tailscale.com) over the internet).
2. **Every player, host included,** follows [docs/setup-player.md](docs/setup-player.md): RPCN, network settings,
   the patches, and the host's certificate. On Windows there's a PowerShell script for the certificate step.
3. Boot the game → **Game Rooms** → pick the room. When you both see each other (up to 30 s), select your friend,
   choose **Challenge**, and they accept from the **Quick Menu** (SELECT).

## The patches

All four are in [`patches/MLB16_online.yml`](patches/MLB16_online.yml). **Both players need all four.**

| Patch | Why |
|---|---|
| Re-enable online menus | Update 1.10 replaced the online menu entry with an "ONLINE DISABLED" popup. |
| Skip live roster download | Sony's roster files are gone. Everyone keeps the built-in roster, so rosters always match. |
| Allow game room challenges | The "challenges allowed" flag is normally set by a step tied to Sony's servers, so the Challenge option never appeared. |
| Fix NP ID lookup hang | RPCS3 never finishes the game's opponent lookup (`sceNpLookupNpIdAsync`), so both players hung on "Challenge accepted, waiting for a response". |

The last one works around an RPCS3 bug. A fix in RPCS3 itself is on the
[`fix-np-lookup-npid-async`](https://github.com/MatRanc/rpcs3/tree/fix-np-lookup-npid-async) branch of my fork. Until
something like it is in an official build, keep the patch on.

## How it works

```
  RPCS3 (you)                                         RPCS3 (friend)
 ┌──────────────┐  game API (XML over HTTPS)  ┌─────────────┐  ┌──────────────┐
 │ MLB The Show │────────────────────────────►│ server.py   │◄─│ MLB The Show │
 │ 16 + patches │  FLS: rooms, chat,          │ (this repo) │  │ 16 + patches │
 │              │────────────────────────────►│             │◄─│              │
 └──┬────────┬──┘  challenges                 └─────────────┘  └──┬────────┬──┘
    │        │                                                    │        │
    │        │   sign-in, NP Signaling      ┌──────┐              │        │
    │        └─────────────────────────────►│ RPCN │◄─────────────┘        │
    │                                       └──────┘                       │
    └──────────────────── the match itself, peer to peer ──────────────────┘
```

- **The game's online code is all still there.** Update 1.10 only blocked the way in, and the patches undo that.
- **RPCS3's IP/Hosts switch** sends the game's dead Sony hostnames to this server. Putting your own certificate in
  place of the PS3 firmware's root certificates makes the game trust it.
- **The server** answers the game's XML web API and runs **FLS**, its live session server (AES-encrypted XML over TCP),
  which relays room chat and challenges between players.
- **RPCN** handles sign-in and NP Signaling, which connects the two games directly for the match.

The full protocol write-up is in [docs/protocol.md](docs/protocol.md).

## Known limits
- Player lists refresh every 30 s (a timer in the game), so a player who just joined can take that long to appear.
- Some player-list columns may show blank or zero: the column names are guesses, since the UI scripts are compiled.
- Endpoints the server doesn't know get an empty "OK" reply. That's enough for everything Game Rooms needs so far.

## Repo

| | |
|---|---|
| `server/server.py` | the server: game API, FLS, logging |
| `server/make_certs.sh` | makes your own root CA and server certificate |
| `server/certswap.sh`, `certswap.ps1` | installs a CA into RPCS3 (Linux/macOS, Windows) and restores the originals |
| `patches/MLB16_online.yml` | the four RPCS3 patches |
| `docs/setup-host.md`, `setup-player.md` | setup guides |
| `docs/protocol.md` | hosts, TLS, the XML API, login, rooms, FLS, challenges, the pre-game handshake |
| `docs/endpoints.md` | all 347 API services the game knows, and which ones the server answers |
| `docs/code-map.md` | where things are in the game's code (addresses and our names) |
| `docs/research.md` | how to get the game's own config files from your copy and dig further |
| `tools/extract_gamedata.py` | extracts `servers_prod.xml` / `services.xml` from your installed update |

Contributions and test reports are welcome. [AGENTS.md](AGENTS.md) has the ground rules: most importantly, never commit
game files, Sony data, logs or certificate keys.

**Fun fact:** getting from the "ONLINE DISABLED" popup to a full 1v1 game took about 8 hours and roughly $60 in Claude
API costs.

Related: [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes) fixes the crowd rendering bug on
RPCS3, and documents the Ghidra/RenderDoc workflow used for both projects.

## Legal
This repo contains no game code, game files or Sony data: no EBOOT, no WAD contents, no config files, no captures.
It describes how the game talks to its servers so people can keep playing a game they own. You need your own copy of
the game. MLB The Show is © Sony Interactive Entertainment. Not affiliated with Sony or MLB.

## License
[Apache License 2.0](LICENSE).
