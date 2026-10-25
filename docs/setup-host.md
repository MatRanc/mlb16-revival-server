# Host setup: running the server

> **Easier:** the [MLB16 Online app](../README.md#setup) does all of this in one click. This page is the manual way.

One person runs the server, usually on the same PC they play on. Everyone else connects to it, over the same home
network or over Tailscale.

Tested as a host on Fedora 44 and Windows 11 (by hand and with the app), and on macOS with the app.

## 1. Get the server running

Linux / macOS:
```sh
git clone <this repo> && cd mlb16-revival-server/server
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./make_certs.sh            # once: makes your own root CA (certs/ca.pem) and a server certificate
.venv/bin/python server.py
```

Windows (PowerShell). First install [Python 3](https://www.python.org/downloads/) (tick **Add python.exe to PATH**) and
[Git for Windows](https://git-scm.com/download/win), which brings the `sh` and `openssl` that `make_certs.sh` needs:
```powershell
git clone https://github.com/MatRanc/mlb16-revival-server; cd mlb16-revival-server\server
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
& "C:\Program Files\Git\bin\sh.exe" make_certs.sh     # once
.venv\Scripts\python server.py
```
The first time it runs, Windows Firewall asks whether Python may accept connections. Allow it on both **Private** and
**Public** networks; the Tailscale network may count as either.

- It listens on **10050** (game API, HTTP), **10051** (game API, HTTPS) and **10070** (FLS).
- Port **443** (telemetry) is optional. On Linux it needs `sudo sysctl -w net.ipv4.ip_unprivileged_port_start=443`. Without it the server skips 443 and the game works anyway.
- Everything is logged to `server/requests.jsonl`. Player IDs are saved in `server/player_ids.json`.

**Keep `certs/ca.key` private.** Anyone with it could impersonate your server to your players. Only `certs/ca.pem` gets shared.

## 2. Set up your own RPCS3
Follow [setup-player.md](setup-player.md) on this machine too, with two differences:
- In IP/Hosts switches, use `127.0.0.1` for the game host. Optionally add the telemetry host as well:
  `production.mlb16.online.scea.com=127.0.0.1&&mlb16.api.wwsga.me=127.0.0.1`
- Install your own CA: `./certswap.sh install` on Linux/macOS, or on Windows
  `powershell -ExecutionPolicy Bypass -File certswap.ps1 install C:\RPCS3 certs\ca.pem` (your RPCS3 folder first).

## 3. Let the other players reach you

### Same home network
Find your LAN IP (`ip -4 addr` on Linux, System Settings → Network on macOS, `ipconfig` → IPv4 Address on Windows). Players put that IP in their hosts
switch. Make sure your firewall allows TCP 10050, 10051 and 10070. Fedora Workstation already allows ports 1025–65535.

Give each player your `certs/ca.pem`.

### Over the internet: Tailscale
[Tailscale](https://tailscale.com) gives your machines a private network with fixed `100.x.y.z` addresses, with no port forwarding.

Tailscale is only needed to reach **your server**. The match itself doesn't go through it (see
[How the match connects](#how-the-match-connects)).

Host on Windows or macOS: install Tailscale from [tailscale.com/download](https://tailscale.com/download), sign in, and
find your `100.x.y.z` address by clicking the Tailscale tray/menu bar icon.

Host on Linux (Fedora shown):
```sh
sudo dnf install tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up            # opens a login link; sign in with any account
tailscale ip -4              # your 100.x.y.z address; this goes in the players' hosts switch
```

Each friend:
1. Install Tailscale ([tailscale.com/download](https://tailscale.com/download); on Windows it's a normal installer that
   runs in the tray) and sign in with **their own** account.
2. The host shares the machine with them: in the [admin console](https://login.tailscale.com/admin/machines), open the
   host machine's **⋯ menu → Share…** and send the invite to the friend's email. The friend accepts it, and the host
   then shows up in their Tailscale.
   Alternatively, invite them as a user of your tailnet (admin console → Users → Invite).
3. Check it works: on the friend's machine, `tailscale ping <host 100.x IP>`, or open `http://<host 100.x IP>:10050/x.xml`
   in a browser (it should return a short XML).

Firewall: on Linux, Tailscale traffic arrives on the `tailscale0` interface. On Fedora it lands in the default zone,
which already allows 10050/10051/10070. On Windows, the firewall prompt from step 1 covers it.

Then players use `production.mlb16.online.scea.com=<host 100.x IP>` in their hosts switch.

### What to send each player
- Your IP: the LAN IP, or your Tailscale `100.x.y.z`.
- `certs/ca.pem` (rename it to `.cer` if that's easier for them). **Never send `ca.key` or `server.key`.**
- A link to this repo: they need [setup-player.md](setup-player.md), [`patches/MLB16_online.yml`](../patches/MLB16_online.yml),
  and on Windows [`server/certswap.ps1`](../server/certswap.ps1).

If something breaks, have everyone save their RPCS3 log **before restarting RPCS3**, since it overwrites the log:
`~/.cache/rpcs3/RPCS3.log` on Linux, `~/Library/Caches/rpcs3/RPCS3.log` on macOS, and in the RPCS3 folder on Windows.
Keep `server/requests.jsonl` from the server as well.

### How the match connects
The server only handles logins, rooms, chat and challenges. The match itself is a direct connection between the two
games, which RPCN sets up (NP Signaling):
- **Same home network:** RPCN gives each game the other's LAN address. Tested, works.
- **Over the internet:** RPCN gives each game the other's public internet address, and RPCS3 punches a direct UDP
  connection through both routers. This doesn't use Tailscale. Tested: home Wi-Fi vs a phone hotspot.

To give it the best chance, turn on **UPnP** in RPCS3 (Configuration → Network) on both machines. If the match still
won't connect, one player can forward **UDP port 3658** (RPCS3's peer-to-peer port) on their router to their PC.
Strict NAT (some mobile hotspots and ISPs that share one public IP between customers) can block it entirely.

## 4. What the host needs to keep doing
- Keep `server.py` running while people play.
- If your LAN IP changes (DHCP), players on your network need the new IP. A DHCP reservation in your router avoids this.
  Tailscale IPs don't change.
- Nothing to undo after playing: the certificate install keeps RPCS3's original certificates, so other games still work.
