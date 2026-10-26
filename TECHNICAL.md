# Technical details

The [README](README.md) covers playing. This page is for people who want to know how it works, change it, build it,
or do the same for another game. The deep dives are in [`docs/`](docs/).

| | |
|---|---|
| [docs/protocol.md](docs/protocol.md) | hosts, TLS, the XML API, login, rooms, FLS, challenges, the pre-game handshake |
| [docs/code-map.md](docs/code-map.md) | where things are in the game's code (addresses, our names, what's patched) |
| [docs/endpoints.md](docs/endpoints.md) | all 347 API services the game knows, and which ones the server answers |
| [docs/research.md](docs/research.md) | how to get the game's own config files from your copy and dig further |
| [docs/setup-host.md](docs/setup-host.md), [setup-player.md](docs/setup-player.md) | the manual setup, without the launcher |

## Graphics settings

The launcher applies these when "Recommended graphics settings" is ticked, for MLB The Show 16 only (in the game's
custom config). By hand: right-click the game in RPCS3 → **Create Custom Configuration**, then set:
- **GPU:** Write Color Buffers on, Strict Rendering Mode **off**, ZCULL Accuracy *Precise*, Shader Quality *High*,
  Output Scaling *Bilinear*. Picture: Default Resolution *720p* at Resolution Scale *100%*, or for a sharper picture
  (the launcher's 1080p) Default Resolution *1080p*, Resolution Scale *150%* and Anisotropic Filter *8x*.
- **Advanced:** Read Color Buffers, Read Depth Buffer, Write Depth Buffer, Disable Vertex Cache on; **Accurate SPU
  Reservations on** (the default)
- **CPU:** SPU Block Size **Safe**, RSX FIFO Accuracy **Atomic** and SPU XFloat Accuracy *Approximate XFloat* (the
  defaults)

Write Color Buffers is the one that fixes the dark crowd and the black background in picture-in-picture windows (like
the runner's lead-off). Strict Rendering Mode isn't needed: it costs performance (mostly on Macs) and makes RPCS3
ignore the anisotropic filter. A "too bright" night sky it seemed to fix turned out to be dusk: "Night" games start at
dusk and get dark as the game goes on.

The CPU settings matter for stability: two online matches froze on a player who had SPU Block Size *Mega* and
Accurate SPU Reservations off (with 1440×1080 and 200% scale) (one silent hang, and one RPCS3 error inside `cellSpursRemoveWorkload`).
On Linux, RSX FIFO Accuracy *Fast* logged "FIFO error: possible desync event" every few seconds, then froze or crashed
RPCS3; *Atomic* logged none. Every freeze traced so far came from a setting changed away from RPCS3's default, often
copied from the player's global config (RPCS3's **Create Custom Configuration** copies all global values). So the
launcher always resets every CPU, SPU and RSX accuracy or timing setting for this game to RPCS3's default (the full
list is `STABILITY` and `VIDEO_STABILITY` in [app/setup_logic.py](app/setup_logic.py)), and sets this game's
per-channel log levels back to Notice, even with "Recommended graphics settings" unticked. Default
Resolution *1440×1080* is not 1440p: it's a stretched PS3 output mode, and the game still renders at 720p. The crowd itself needs the **crowd fix patch** from
[mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes), which the launcher also installs.

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
- With Strict Rendering Mode on (no longer set), an M1 Mac ran about 35 FPS in a match. Not measured without it yet.
- RPCS3 itself can still freeze mid-game. Seen: an SPU-related hang and error on Windows with non-default SPU
  settings, and on Linux a frozen picture or an RSX crash after "FIFO error: possible desync event" errors, which
  went away with RSX FIFO Accuracy *Atomic*. The launcher now resets all of these to RPCS3's defaults. When one player's game freezes, the
  other's waits for it and freezes too.
- Close-ups (walk-ups, the manager in the dugout, mound visits) are CPU-bound. On a Ryzen 5 2600X at 720p: about 60
  FPS fielding, 35 batting, 24 on the pitching view, 15 to 20 in close-ups. Tested without much effect: Strict Rendering
  Mode off (+1 to 2 FPS), FIFO accuracy, Max SPURS Threads 4, SPU loop detection. RPCS3's profiler showed the main
  game thread waiting most of the time and the work spread over 25+ SPU programs, with no single hotspot worth
  patching. A faster CPU is the fix.

## Building and development

Run the launcher from source (this is also the way on Linux for now):
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
- **Without the launcher:** the manual setup is in [docs/setup-host.md](docs/setup-host.md) and
  [docs/setup-player.md](docs/setup-player.md).

What the launcher changes in RPCS3: `patches/BCUS01089_patch.yml` (its own file), the patches' entries in
`patch_config.yml`, the game's custom config (`custom_configs/config_BCUS01089.yml`: network and graphics), and the
PS3 root certificates in `dev_flash/data/cert` (each one becomes original + the host's CA; the originals are kept in
`cert.orig`). Its own files (settings, certificates, logs) live in `%APPDATA%\mlb16-online`,
`~/Library/Application Support/mlb16-online` or `~/.config/mlb16-online`.

## Repo layout

| | |
|---|---|
| `app/` | the MLB16 Online Launcher: RPCS3 setup, server start/stop, invite files (`test_setup_logic.py` tests it) |
| `server/server.py` | the server: game API, FLS, logging |
| `server/make_certs.sh` | makes your own root CA and server certificate |
| `server/certswap.sh`, `certswap.ps1` | adds the host's CA to RPCS3's certificates, keeping the originals (Linux/macOS, Windows) |
| `patches/MLB16_online.yml` | the five RPCS3 patches |
| `patches/MLB16_crowd_fix.yml` | the crowd fix from [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes), installed by the launcher |
| `tools/extract_gamedata.py` | extracts `servers_prod.xml` / `services.xml` from your installed update |

Contributions and test reports are welcome. [AGENTS.md](AGENTS.md) has the ground rules: most importantly, never commit
game files, Sony data, logs or certificate keys.

## Reviving another game

The same approach should work for other PS3 games whose servers are gone (another sports title, for example). What
carried over from this project:
1. **Find the hostnames and the API.** The game's own config files (here `servers_prod.xml` and `services.xml`, inside
   the update's data archive) list every server and endpoint. [docs/research.md](docs/research.md) shows how they were
   found and extracted.
2. **Redirect and trust.** RPCS3's IP/Hosts switch sends the hostnames to your server; appending your own CA to the
   PS3 root certificates makes the game accept it. That part is generic: see `app/setup_logic.py`.
3. **Log everything, answer what's needed.** The server answers unknown calls with an empty "OK" and logs them, so you
   play, read the log, find the reply parser in the EBOOT with Ghidra, and add a real reply. [AGENTS.md](AGENTS.md)
   describes that loop for an AI agent.
4. **Patch what can't be served.** Where the game checks something no server can answer anymore (here: the
   "ONLINE DISABLED" popup, the live roster download), a small RPCS3 patch skips it.
5. **Peer-to-peer goes through RPCN.** Matches use the PS3's NP Signaling, which RPCN already provides, so the server
   only has to handle the lobby.

Pointing an AI agent at this repo with "do this for game X" is a reasonable start: `docs/protocol.md`,
`docs/code-map.md` and `AGENTS.md` describe what was done and how.

