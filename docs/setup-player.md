# Player setup

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

## 3. Patches
Manage → Game Patches → drag [`patches/MLB16_online.yml`](../patches/MLB16_online.yml) onto the window, then tick all four:
- **Re-enable online menus.** Update 1.10 replaced the online entry point with an "ONLINE DISABLED" popup.
- **Skip live roster download.** Sony's roster files are gone. Everyone keeps the built-in roster, so rosters always match.
- **Allow game room challenges.** The game only enables challenges after a server-driven step we don't replicate yet, so the Challenge option would never appear.
- **Fix NP ID lookup hang.** RPCS3 never finishes the game's opponent ID lookup (`sceNpLookupNpIdAsync`), so both players would hang on "Challenge accepted, waiting for a response".

If drag and drop doesn't work (it may not on macOS), copy the file into RPCS3's `patches/` folder as `imported_patch.yml`.
To tick patches without the checkboxes, add them to RPCS3's `patch_config.yml`.

Also recommended: the crowd fix from [mlb-show-rpcs3-fixes](https://github.com/MatRanc/mlb-show-rpcs3-fixes).

## 4. Trust the host's certificate
The game only talks to servers whose certificate it trusts, so replace RPCS3's PS3 root certificates with the host's.

Linux / macOS, using the script from this repo:
```sh
./server/certswap.sh install /path/to/host-ca.pem
# undo later:
./server/certswap.sh restore
```

Windows (PowerShell), using [`server/certswap.ps1`](../server/certswap.ps1). The first path is your RPCS3 folder,
the one containing `rpcs3.exe`:
```powershell
powershell -ExecutionPolicy Bypass -File certswap.ps1 install C:\RPCS3 C:\Users\you\Downloads\ca.pem
# undo later:
powershell -ExecutionPolicy Bypass -File certswap.ps1 restore C:\RPCS3
```
By hand instead: in `<RPCS3 folder>\dev_flash\data\cert`, copy all `.cer` files to a backup folder, then copy the host's
`ca.pem` over each `.cer` file, keeping each original filename.

## 5. Play
With the host's server running: boot the game → **Game Rooms** → pick the room. Everyone in the room appears in the
player list, and chat works. Select a player to challenge them.

## Troubleshooting
- **"ONLINE DISABLED … no longer available":** the re-enable patch isn't ticked, or your game isn't v01.10.
- **"The Online features of MLB The Show are disabled":** PSN sign-in failed. Check that PSN status is RPCN and you're logged in.
- **"Your connection to The Show Online has been lost" right away:** the server isn't reachable (hosts switch IP, firewall, Tailscale), or the certificate isn't installed.
- **"Downloading live roster failed":** the skip-roster patch isn't ticked.
- **Stuck on "Challenge accepted, waiting for a response":** the NP ID lookup patch isn't ticked on one of the machines.
