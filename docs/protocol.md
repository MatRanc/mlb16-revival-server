# How MLB The Show 16 talks to its servers (PS3, v01.10)

Worked out from the game's code and its traffic against our server.

## Hosts

| host | port | what |
|---|---|---|
| `mlb16.api.wwsga.me` | 443 (HTTPS) | WWS telemetry: JSON `POST /games/<uuid>/telemetry`. Optional; the game works without it. |
| `production.mlb16.online.scea.com` | 10050 HTTP / 10051 HTTPS | Game API (XML). Calls flagged `use_ssl` go to 10051. |
| FLS (address from the login reply) | any, TCP | Live session server: rooms, chat, challenges. We serve it on 10070. |

Both hostnames still belong to Sony, but the servers are gone. RPCS3's **IP/Hosts switches** setting points them at our server.

## TLS

- The game uses the PS3 firmware's own SSL library and verifies certificates against the firmware's root CAs in `dev_flash/data/cert`. Replacing those files with your own CA (`server/certswap.sh`) makes the game trust your server. No game patch is needed.
- The PS3 negotiates TLS 1.2 with AES256-SHA256. The server also allows TLS 1.0 just in case.

## HTTP API

Requests:
- `application/x-www-form-urlencoded` bodies or query strings.
- Headers: `X-SC-Tmx` (a request signature that the server doesn't need to check), `X-Title-UUID` (the PS3 title UUID from `servers_prod.xml`) and `X-Analytics-Session-UUID`.
- **There are no cookies.** The analytics session UUID stays constant for a client's whole session, so the server uses it to tell players apart.

Responses:
- The `Content-Type` must be **exactly** `application/xml;charset=utf-8`. Anything else and the client ignores the body ("Response Error. Code 2").
- Envelope:
  ```xml
  <result><status><id>0</id><message>Successful completion</message></status><response>…</response></result>
  ```
  A negative `id` means an error. A missing `status`/`message`/`id` gives "Code 2", and a missing `response` gives "Code 1".
- Data comes as **XML attributes**, not child text.

### Login flow
1. `POST mlb_logins/login.xml` (SSL). Form fields: `console_id` (MAC address), `platform=PS3`, `ticket` (base64 NP ticket from RPCN). Reply:
   ```xml
   <login_data player_id="1001" player_name="name"/>
   <fls_data server_address="host" server_port="10070" server_private_key="32 ASCII chars"
             ticket_session_uuid="…" ticket_signature="…" ticket_player_id="1001"
             ticket_username="name" ticket_expiration_date="2030-01-01T00:00:00Z"/>
   ```
   The player's name comes from the NP ticket, a list of TLVs. The online ID is the first type-4, length-32 field.
2. `POST mlb_login/post_update.xml`: favorite team, timezone, telemetry ID. Answer with an empty success.
3. The client connects to FLS (see below).
4. `POST universal_profiles/update.xml`, `GET inventories/view.xml`, and more; empty success replies are enough.
5. `POST session/ping.xml` about every 30 s. The client only records when the last good ping happened; failed pings end the session.
6. `POST servers/select.xml` (`server_type=FLS`) can move the client to another FLS:
   `<server address port server_private_key><ticket session_uuid signature player_id username expiration_date/></server>`

### Game Rooms
- `GET lobby_channels/list_with_my_league_rooms.xml?page=1`:
  `<lobby_channels page total_pages player_skill_level="…"><lobby_channel id name min_skill max_skill …/></lobby_channels>`.
  `player_skill_level` is required, and the room's `min_skill`/`max_skill` must accept it.
- `GET lobby_channels/show.xml?id=N`
- `POST lobby_channel_players/join_with_ping.xml` (`lobby_channel_id=0&ping=…`) and `POST lobby_channel_players/quit.xml`
- `GET lobby_channel_players/list_with_ping.xml?lobby_channel_id=N&page=1&per_page=100&ping=…`:
  `<lobby_channel_players><lobby_channel_player …/></lobby_channel_players>`
- The room screen's UI script binds `playerlist.lobby_channel_player`. Its column names are compiled to hashes, so the server sends several likely names (`username`, `name`, `player_id`, `ping`, the stats, …). `username` works.

### Live roster
`GET content_updates/latest.xml?content_update_type=LIVE_ROSTERS` expects
`<content_update uuid created_at content_url data_md5 description id name/>`. The client then downloads `content_url`,
checks it against `data_md5` ("mismatched roster" if they differ) and applies it as a roster pack. Sony's roster files
are gone, so the "Skip live roster download" patch reports success instead, and everyone keeps the built-in roster.

## FLS (the live session server)

- **Transport:** TCP. Each frame is a `u16` big-endian length followed by the payload.
- **Payload:** XML, zero-padded to a multiple of 16 bytes, then encrypted with **AES-256-ECB**. The key is the **ASCII bytes** of `server_private_key` from the login reply, which the server chooses.
- **Message format:**
  ```xml
  <?xml version="1.0" encoding="utf-8"?>
  <message delivery="gtd" layer="989fls" target="srvr" targetID="0">
      <Hello expiration_date="…" player_id="1001" session_uuid="…" signature="00" username="name"/>
  </message>
  ```
  - `target` is one of `zone`, `plyr`, `srvr` or `cons`.
  - `delivery` is `gtd` or `opt`.
  - Messages from the server carry `sender`/`senderID`.
- **Core layer `989fls`**, messages from the client:
  - `Hello`: the server answers with a `Hello`.
  - `Keepalive`: every 15 s. The server sends its own about every 10 s.
  - `PluginRegister Layer=… ServiceClass=PluginData|PluginLogic|PluginDataAndLogic` / `PluginUnregister`
  - `disconnect`
- **Core layer `989fls`**, messages the client accepts from the server: `Hello`, `Message`, `ZonePlayerJoin`, `ZonePlayerQuit`, `BuddyInvite`, `PlayerKick`, `System`.
- **Plugin layers seen:**
  - `MLBAM`, registered after login.
  - In a game room: `CHATTEXT_<a>_<room>` for chat, as `<ChatText>message</ChatText>` sent to `target="zone"`, and `CHATOOB_<a>_<room>`, an out-of-band layer used for challenges.
- **Relaying:** challenge and chat payloads go client to client. The server forwards `target="plyr"` messages to that player and `target="zone"` messages to everyone else registered on the same layer, stamping `sender=<username> senderID=<id>` (the client shows `sender` as the chat name). It doesn't need to understand the payloads.

## Not done yet
- The challenge handshake and the start of a game (`mlb_game.create` / `mlb_game.start`).
- The peer-to-peer match itself, which runs over NP Signaling through RPCN.
