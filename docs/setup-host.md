# Host setup: running the server

One person runs the server, usually on the same PC they play on. Everyone else connects to it, over the same home
network or over Tailscale.

Tested on Fedora 44 with Python 3.14. Any OS with Python 3.10+ should work.

## 1. Get the server running

```sh
git clone <this repo> && cd mlb16-revival-server/server
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./make_certs.sh            # once: makes your own root CA (certs/ca.pem) and a server certificate
.venv/bin/python server.py
```

- It listens on **10050** (game API, HTTP), **10051** (game API, HTTPS) and **10070** (FLS).
- Port **443** (telemetry) is optional. On Linux it needs `sudo sysctl -w net.ipv4.ip_unprivileged_port_start=443`. Without it the server skips 443 and the game works anyway.
- Everything is logged to `server/requests.jsonl`. Player IDs are saved in `server/player_ids.json`.

**Keep `certs/ca.key` private.** Anyone with it could impersonate your server to your players. Only `certs/ca.pem` gets shared.

## 2. Set up your own RPCS3
Follow [setup-player.md](setup-player.md) on this machine too, with two differences:
- In IP/Hosts switches, use `127.0.0.1` for the game host. Optionally add the telemetry host as well:
  `production.mlb16.online.scea.com=127.0.0.1&&mlb16.api.wwsga.me=127.0.0.1`
- Install your own CA with `./certswap.sh install`.

## 3. Let the other players reach you

### Same home network
Find your LAN IP (`ip -4 addr` on Linux, System Settings → Network on macOS). Players put that IP in their hosts
switch. Make sure your firewall allows TCP 10050, 10051 and 10070. Fedora Workstation already allows ports 1025–65535.

Give each player your `certs/ca.pem`.

### Over the internet: Tailscale
[Tailscale](https://tailscale.com) gives your machines a private network with fixed `100.x.y.z` addresses, with no port forwarding.

Host (Fedora shown; see tailscale.com/download for other systems):
```sh
sudo dnf install tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up            # opens a login link; sign in with any account
tailscale ip -4              # your 100.x.y.z address; this goes in the players' hosts switch
```

Each friend:
1. Install Tailscale and sign in with **their own** account.
2. The host shares the machine with them: in the [admin console](https://login.tailscale.com/admin/machines), open the
   host machine's **⋯ menu → Share…** and send the invite to the friend's email. The friend accepts it, and the host
   then shows up in their Tailscale.
   Alternatively, invite them as a user of your tailnet (admin console → Users → Invite).
3. Check it works: on the friend's machine, `tailscale ping <host 100.x IP>`, or open `http://<host 100.x IP>:10050/x.xml`
   in a browser (it should return a short XML).

Firewall: Tailscale traffic arrives on the `tailscale0` interface. On Fedora it lands in the default zone, which
already allows 10050/10051/10070. On other systems, allow those TCP ports on `tailscale0`.

Then players use `production.mlb16.online.scea.com=<host 100.x IP>` in their hosts switch.

## 4. What the host needs to keep doing
- Keep `server.py` running while people play.
- If your LAN IP changes (DHCP), players on your network need the new IP. A DHCP reservation in your router avoids this.
  Tailscale IPs don't change.
- When you're done, `./certswap.sh restore` puts RPCS3's original certificates back. Other games' online features need them.
