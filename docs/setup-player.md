# Player setup

> **Easier:** the [MLB16 Online Launcher](../README.md#setup) does all of this in one click. This page is the manual way.

What each player does once, including the host.

You need:
- RPCS3 (Windows, Linux or macOS)
- the PS3 firmware, installed in RPCS3
- your own copy of *MLB The Show 16* (disc dump BCUS01089) and the **v01.10** update (see the main README for Sony's download link)

From the host you need two things: their **IP** (LAN or Tailscale) and their **`ca.pem`**.

## 1. RPCN account
Each player needs their own. In RPCS3: Configuration → RPCN (or Manage → RPCN) → Create Account, then enter the
token from the email. The server tells players apart by their RPCN name.

## 2. Network settings
Configuration → Network:
- Network status: **Connected**
- PSN status: **RPCN**
- IP/Hosts switches: `production.mlb16.online.scea.com=<host IP>`
- UPnP: **on** (helps the match connect when you're not on the host's network)

## 3. Patches
Put [`patches/MLB16_online.yml`](../patches/MLB16_online.yml) in RPCS3's `patches` folder, renamed to
`imported_patch.yml`:
- Windows: `<RPCS3 folder>\patches\`
- Linux: `~/.config/rpcs3/patches/`
- macOS: `~/Library/Application Support/rpcs3/patches/`

If you already have an `imported_patch.yml` there, paste this file's contents at the end of it instead, without its
first line (`Version: 1.2`). Then open RPCS3 → **Manage → Game Patches**, tick all five under MLB The Show 16, and Save:
- **Re-enable online menus.** Update 1.10 replaced the online entry point with an "ONLINE DISABLED" popup.
- **Skip live roster download.** Sony's roster files are gone. Everyone keeps the built-in roster, so rosters always match.
- **Allow game room challenges.** The game only enables challenges after a server-driven step we don't replicate yet, so the Challenge option would never appear.
- **Fix NP ID lookup hang.** RPCS3 never finishes the game's opponent ID lookup (`sceNpLookupNpIdAsync`), so both players would hang on "Challenge accepted, waiting for a response".
- **Faster game room player list.** The room refreshes its player list every 8 s instead of every 30 s.

Also recommended: the crowd fix from [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes).

## 4. Trust the host's certificate
The game only talks to servers whose certificate it trusts, so the host's certificate gets added to each of RPCS3's PS3
root certificate files. The originals stay in place, so other games keep working and there's nothing to undo.

Linux / macOS, using the script from this repo:
```sh
./server/certswap.sh install /path/to/host-ca.pem
# optional: put the untouched originals back
./server/certswap.sh restore
```

Windows (PowerShell), using [`server/certswap.ps1`](../server/certswap.ps1). The first path is your RPCS3 folder,
the one containing `rpcs3.exe`:
```powershell
powershell -ExecutionPolicy Bypass -File certswap.ps1 install C:\RPCS3 C:\Users\you\Downloads\ca.pem
# optional: put the untouched originals back
powershell -ExecutionPolicy Bypass -File certswap.ps1 restore C:\RPCS3
```
By hand instead: in `<RPCS3 folder>\dev_flash\data\cert`, copy all `.cer` files to a backup folder, then open each
`.cer` file in a text editor and paste the contents of the host's `ca.pem` at the end.

Switching to another host: run `install` again with their `ca.pem`. It rebuilds the files from the backup, so the old
host's certificate is dropped.

## 5. Graphics settings
Right-click the game → **Create Custom Configuration**, and set the settings listed (with screenshots) in the
[graphics section of TECHNICAL.md](../TECHNICAL.md#graphics-settings). Without them, parts of the crowd go dark and
picture-in-picture windows get a black background. For the crowd itself, add the crowd fix patch from
[mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes).

## 6. Play
With the host's server running: boot the game → **Game Rooms** → pick the room. Everyone in the room appears in the
player list, and chat works. Select a player to challenge them.

The first time, your computer may ask whether RPCS3 (and on the host, Python) may use the network. Allow it, on private
and public networks on Windows, or the match can't connect.

If a player is missing from the list, wait up to 8 s (30 s without the faster list patch); if they still don't show
up, leave the room and join it again.

## Troubleshooting
- **"ONLINE DISABLED … no longer available":** the re-enable patch isn't ticked, or your game isn't v01.10.
- **"The Online features of MLB The Show are disabled":** PSN sign-in failed. Check that PSN status is RPCN and you're logged in.
- **"Your connection to The Show Online has been lost" right away:** the server isn't reachable (hosts switch IP, firewall, Tailscale), or the certificate isn't installed.
- **"Downloading live roster failed":** the skip-roster patch isn't ticked.
- **Stuck on "Challenge accepted, waiting for a response":** the NP ID lookup patch isn't ticked on one of the machines.
- **Stuck on the stadium select screen:** back out and send a new challenge. Seen once, cause unknown.
- **Dark crowd, or a black box around the runner's lead-off view:** see [Graphics settings](#5-graphics-settings).
