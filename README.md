# MLB The Show 16 revival server (PS3 / RPCS3)

**Play *MLB The Show 16* online again: 1v1 against a friend, both on RPCS3.**

Sony shut down the game's online service in 2020 with update 1.10. This repo is a small private server plus five RPCS3
game patches that bring back **Game Rooms**: join a room, see each other, chat, send a challenge, and play a full game.

![The first online game in years: Mets at Tigers, pitching on a Linux PC and batting on an M1 MacBook Air, both on RPCS3](docs/images/first-1v1.jpg)

> **Status: it works!** First online 1v1 game played on October 25, 2026 (Linux PC vs M1 Mac, same home network),
> then Windows 11 vs M1 Mac the same day, through a full inning and a concede, and then over the internet (home
> Wi-Fi vs a phone hotspot, through Tailscale), set up entirely with the app.
> It's still early: expect rough edges, and please report what you find.

| | |
|---|---|
| ✅ | Online menus unlocked, PSN sign-in through RPCN, login to the game server |
| ✅ | Game Rooms: room list, player list, chat |
| ✅ | Challenging a player, accepting, and the pre-game handshake |
| ✅ | Peer-to-peer connection and **playing a 1v1 game** |
| ✅ | Playing over the internet: the server through Tailscale, the match through RPCN's direct connection (home Wi-Fi vs a phone hotspot) |
| ✅ | Windows: server and game on Windows 11, playing against a Mac |
| ✅ | Conceding: the other player accepts, and both games go back to the room |
| ✅ | **MLB16 Online app**: set up RPCS3 and host or join with an invite file, tested on Fedora, Windows 11 and macOS |
| ❓ | Reliability: one early attempt dropped before the game started, one got stuck on stadium select, and RPCS3 once crashed mid-game with a graphics error |
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

One player also hosts the server, usually on the PC they play on. The app does that too.

Tested on:
- Ryzen 5 2600X, 32 GB DDR4, RTX 3060 Ti: Fedora 44 and Windows 11 (same PC, dual boot)
- MacBook Air M1, 16 GB, latest macOS

The patches are made for the disc version's v01.10 EBOOT. The digital version (NPUA81353) has a different EBOOT and
isn't supported yet.

## Setup

Download **MLB16 Online** from the [Releases page](https://github.com/MatRanc/mlb16-revival-server/releases/latest)
(Windows or macOS) and unzip it. It sets up RPCS3 in one click (the patches, the game's network and graphics
settings, and the server certificate), runs the server, and makes invite files. It only changes MLB The Show 16:
your other games keep their settings and their online features.

The app isn't signed, so the first launch needs one extra click:
- **Windows:** "Windows protected your PC" → **More info** → **Run anyway**.
- **macOS:** right-click the app → **Open** → **Open**.
- **Linux:** no download yet. Run it from source (see [Building and development](#building-and-development)).

<table>
  <tr>
    <td><img src="docs/images/app-setup.png" alt="The Set up RPCS3 tab: RPCS3 folder, who runs the server, options, Set up and Launch buttons, and a checklist"></td>
    <td><img src="docs/images/app-host.png" alt="The Host a game tab: Start/Stop server, your addresses, Save invite file, and server activity"></td>
  </tr>
</table>

**The host:**
1. **Set up RPCS3** tab → "Me, on this computer" → **Set up RPCS3**.
2. **Host a game** tab → **Start server**. Allow network access if your firewall asks.
3. **Save invite file…** and send it to your friend (Discord, email, anything: it holds your address and your
   public certificate, no secrets). Pick the Tailscale address if they're not on your home network (see below).

**Your friend:** **Set up RPCS3** tab → "A friend, who sent me an invite file" → **Open invite…** → **Set up RPCS3**.

**Then both of you:** **Launch RPCS3** → boot the game → **Online → Game Rooms** → pick the room. Select your friend,
choose **Challenge**, and they accept from the **Quick Menu** (SELECT). Your computer may ask whether RPCS3 can use
the network: allow it.

### Playing over the internet: Tailscale

[Tailscale](https://tailscale.com) (free) connects the two computers so your friend can reach your server, with no
port forwarding. Tested: host on home Wi-Fi, other player on a phone hotspot.

1. **Both of you** install Tailscale ([tailscale.com/download](https://tailscale.com/download)) and sign in. Each of
   you uses your own account. (Two computers of your own can just use the same account and skip step 2.)
2. **The host shares their computer with the friend:** in the [admin console](https://login.tailscale.com/admin/machines),
   click **⋯** next to your computer → **Share…**, and send the invite link to your friend. They open it and accept.
   Your computer then shows up in their Tailscale. Sharing gives access to that one computer only, not your network,
   and you can stop sharing from the same menu.
3. **The host** opens the **Host a game** tab (Tailscale has to be running), picks the **Tailscale** address,
   saves the invite file and sends it. Your friend opens it in the app and clicks **Set up RPCS3**.

**Does Tailscale slow down Discord or the game?** No. Tailscale only carries traffic sent to the other computer's
Tailscale address, which here is just the game server (logins, the room list, chat and challenges: very little data).
Discord, your browser and the match itself keep using your normal internet connection, so there's no split
tunneling to set up. (The one exception is a Tailscale "exit node", which is off unless you turn it on.)

The match connects directly between the two games (RPCN sets that up). If a challenge is accepted but the match
never starts, make sure UPnP is on in both routers.

## Troubleshooting

- **"ONLINE DISABLED … no longer available":** the patches aren't active, or your game isn't on update v01.10. Run
  **Set up RPCS3** again with RPCS3 closed.
- **"The Online features of MLB The Show are disabled":** PSN sign-in failed. Log in to RPCN in RPCS3
  (Configuration → RPCN).
- **"Your connection to The Show Online has been lost" right away:** the game can't reach the server. Is the host's
  server running? Over the internet: is Tailscale on for both of you, and did the friend accept the share? Did the
  friend run **Set up RPCS3** with the latest invite?
- **A player is missing from the room:** wait up to 8 s. Still missing: leave the room and join it again.
- **Stuck on the stadium select screen:** back out and send a new challenge. Seen once, cause unknown.
- **Dark crowd, or a black box around the runner's lead-off view:** the graphics settings below aren't on. Keep
  "Recommended graphics settings" ticked in the app and run **Set up RPCS3** again.
- **Something else:** before restarting anything, save the RPCS3 log (`RPCS3.log`: in the RPCS3 folder on Windows,
  `~/Library/Caches/rpcs3` on macOS, `~/.cache/rpcs3` on Linux) and the host's server log (`requests.jsonl` in the
  folder shown at the bottom of the **Host a game** tab), then open an issue.

## Graphics settings

**The app applies these for you** when "Recommended graphics settings" is ticked, for MLB The Show 16 only. To set
them by hand instead: right-click the game in RPCS3 → **Create Custom Configuration**, then set:
- **GPU:** Write Color Buffers, Strict Rendering Mode, ZCULL Accuracy *Precise*, Shader Quality *High*
- **Advanced:** Read Color Buffers, Read Depth Buffer, Write Depth Buffer, Disable Vertex Cache
- **CPU:** leave SPU XFloat Accuracy on *Approximate XFloat* and SPU Block Size on *Safe* (the defaults)

Without them, parts of the crowd go dark and the picture-in-picture windows (like the runner's lead-off) have a black
background. The crowd itself needs the **crowd fix patch** from
[mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes), which the app also installs.

<table>
  <tr>
    <th>GPU</th>
    <th>Advanced</th>
    <th>CPU</th>
  </tr>
  <tr>
    <td><img src="docs/images/settings-gpu.png" alt="GPU tab settings"></td>
    <td><img src="docs/images/settings-advanced.png" alt="Advanced tab settings"></td>
    <td><img src="docs/images/settings-cpu.png" alt="CPU tab settings"></td>
  </tr>
</table>

## The patches

All five are in [`patches/MLB16_online.yml`](patches/MLB16_online.yml). **Both players need all five.**

| Patch | Why |
|---|---|
| Re-enable online menus | Update 1.10 replaced the online menu entry with an "ONLINE DISABLED" popup. |
| Skip live roster download | Sony's roster files are gone. Everyone keeps the built-in roster, so rosters always match. |
| Allow game room challenges | The "challenges allowed" flag is normally set by a step tied to Sony's servers, so the Challenge option never appeared. |
| Fix NP ID lookup hang | RPCS3 never finishes the game's opponent lookup (`sceNpLookupNpIdAsync`), so both players hung on "Challenge accepted, waiting for a response". |
| Faster game room player list | The room only re-downloads its player list every 30 s, and nothing tells it when someone joins. This makes it 8 s. |

The NP ID lookup patch works around an RPCS3 bug. A fix in RPCS3 itself is on the
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
- **RPCS3's IP/Hosts switch** sends the game's dead Sony hostnames to this server. Adding your own certificate to
  the PS3 firmware's root certificates makes the game trust it.
- **The server** answers the game's XML web API and runs **FLS**, its live session server (AES-encrypted XML over TCP),
  which relays room chat and challenges between players.
- **RPCN** handles sign-in and NP Signaling, which connects the two games directly for the match.

The full protocol write-up is in [docs/protocol.md](docs/protocol.md).

## Known limits
- The player list is refreshed on a timer (8 s with the patch, 30 s without), so a player who just joined can take
  that long to appear. As far as we can tell, the game only downloads the list when you join and on that timer.
- Some player-list columns may show blank or zero: the column names are guesses, since the UI scripts are compiled.
- Endpoints the server doesn't know get an empty "OK" reply. That's enough for everything Game Rooms needs so far.

## Building and development

Run the app from source (this is also the way on Linux for now):
```sh
git clone https://github.com/MatRanc/mlb16-revival-server && cd mlb16-revival-server/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/python mlb16_online.py               # Windows: .venv\Scripts\python mlb16_online.py
```
tkinter may be a separate package: `sudo dnf install python3-tkinter` (Fedora), `sudo apt install python3-tk`
(Debian/Ubuntu), `brew install python-tk` (macOS with Homebrew's Python).

- **Tests:** `python test_setup_logic.py` in `app/` runs the setup steps against fake RPCS3 folders (Linux and Windows
  layouts).
- **Builds:** [`.github/workflows/build-app.yml`](.github/workflows/build-app.yml) builds the Windows and macOS apps with
  PyInstaller. It runs on a version tag (`v*`), which attaches both zips to a GitHub Release, or by hand from the
  Actions tab.
- **The server alone:** `python mlb16_online.py --server`, or `server/server.py` directly (it then keeps its
  certificates and logs next to itself; see [docs/setup-host.md](docs/setup-host.md)).
- **Without the app:** the manual setup is in [docs/setup-host.md](docs/setup-host.md) and
  [docs/setup-player.md](docs/setup-player.md).

What the app changes in RPCS3: `patches/BCUS01089_patch.yml` (its own file), the patches' entries in
`patch_config.yml`, the game's custom config (`custom_configs/config_BCUS01089.yml`: network and graphics), and the
PS3 root certificates in `dev_flash/data/cert` (each one becomes original + the host's CA; the originals are kept in
`cert.orig`). Its own files (settings, certificates, logs) live in `%APPDATA%\mlb16-online`,
`~/Library/Application Support/mlb16-online` or `~/.config/mlb16-online`.

## Repo

| | |
|---|---|
| `app/` | the MLB16 Online app: RPCS3 setup, server start/stop, invite files (`test_setup_logic.py` tests it) |
| `server/server.py` | the server: game API, FLS, logging |
| `server/make_certs.sh` | makes your own root CA and server certificate |
| `server/certswap.sh`, `certswap.ps1` | adds the host's CA to RPCS3's certificates, keeping the originals (Linux/macOS, Windows) |
| `patches/MLB16_online.yml` | the five RPCS3 patches |
| `patches/MLB16_crowd_fix.yml` | the crowd fix from [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes), installed by the app |
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
