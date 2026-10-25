# MLB The Show 16 revival server (PS3 / RPCS3)

Sony shut down *MLB The Show 16*'s online service on July 28, 2020, with update 1.10. This is a small private server,
plus four RPCS3 game patches, that brings back **Game Rooms** so you can play 1v1 against a friend, both on RPCS3.

**Status: work in progress.** What works so far:

| | |
|---|---|
| ✅ | Online menus unlocked (patch) |
| ✅ | PSN sign-in through RPCN, login to the game server |
| ✅ | FLS session server (encrypted, now understood) |
| ✅ | Game Rooms: room list, joining, the player list, chat between players |
| ✅ | Challenging a player and accepting it (Quick Menu) |
| ✅ | After the accept: opponent info, game ID, and the clients agreeing on the match |
| 🚧 | Peer-to-peer connection: NP ID lookup hang fixed with a patch, NP Signaling (RPCN) untested |
| ❓ | The match itself |

Other modes (Diamond Dynasty, Online Rated, Franchise…) reach the server but need many more endpoints. They're out of
scope for now.

## How it works, in short
- The game still has all its online code. Update 1.10 only swapped the menu's "go online" check for an "ONLINE DISABLED"
  popup, and the first patch undoes that. The others skip Sony's (deleted) live roster download, enable game
  room challenges (which normally switch on after a step tied to Sony's servers), and work around an RPCS3
  NP lookup call that never finishes.
- RPCS3's **RPCN** stands in for PSN: sign-in tickets, friends, and the peer-to-peer connection.
- RPCS3's **IP/Hosts switch** points the game's dead hostnames at this server. Replacing the PS3 firmware's root
  certificates with your own makes the game trust it.
- This server answers the game's XML web API and runs its **FLS** live session server, which uses AES-encrypted XML
  over TCP. FLS relays chat and challenges between players.

The full write-up of the protocol is in [docs/protocol.md](docs/protocol.md).

## Setup
1. **Everyone:** own the game (BCUS01089) and install the v01.10 update, downloadable from Sony's own servers:
   [UP9000-BCUS01089_00-MLB16THESHOWBDPA-A0110-V0100-PE.pkg](http://b0.ww.np.dl.playstation.net/tppkg/np/BCUS01089/BCUS01089_T10/07a5f28c76691db4/UP9000-BCUS01089_00-MLB16THESHOWBDPA-A0110-V0100-PE.pkg)
2. **One person hosts:** [docs/setup-host.md](docs/setup-host.md) covers running the server, your certificate, and same-network or Tailscale access.
3. **Each player:** [docs/setup-player.md](docs/setup-player.md) covers RPCN, network settings, the patches and the certificate.

## Known limits
- Player lists refresh every 30 s (a client timer), so a newly joined player takes up to 30 s to appear.
- Player-list column names are guesses (the UI script is compiled), so some fields may show blank or zero.

## Repo
| | |
|---|---|
| `server/` | `server.py` (the server), `make_certs.sh` (your CA), `certswap.sh` (install a CA into RPCS3) |
| `patches/MLB16_online.yml` | the four RPCS3 patches: re-enable online menus, skip live roster, allow challenges, fix NP ID lookup hang |
| `docs/protocol.md` | hosts, TLS, the XML API, login and room flows, the FLS protocol |
| `docs/endpoints.md` | all 347 game API services the client knows, and which ones the server implements |
| `docs/code-map.md` | where things are in the game's code (addresses and our names) |
| `docs/research.md` | how to get the game's own config files and dig further |
| `tools/extract_gamedata.py` | extracts `servers_prod.xml` / `services.xml` from your installed update |

Related: [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes) has the crowd rendering fix, plus the
Ghidra/RenderDoc workflow used for this project too.

## Legal
This repo contains no game code, game files or Sony data: no EBOOT, no WAD contents, no config files, no captures.
It describes how the game talks to its servers so people can keep playing a game they own. You need your own copy
of the game. MLB The Show is © Sony Interactive Entertainment. Not affiliated with Sony or MLB.

## License
Apache License 2.0.
