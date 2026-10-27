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

- The game uses the PS3 firmware's own SSL library and verifies certificates against the firmware's root CAs in `dev_flash/data/cert`. Appending your own CA to each of those files (`server/certswap.sh`) makes the game trust your server while keeping the
  originals, so other games still work. RPCS3 joins the files into one PEM buffer, and the game's SSL library accepts every
  certificate in it. No game patch is needed.
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
  - `Hello`: the server answers with a `Hello`. The server takes the `player_id` / `username` in it at face value
    (no check against the login), which is fine for a server only friends can reach.
  - `Keepalive`: every 15 s. The server sends its own about every 10 s.
  - `PluginRegister Layer=… ServiceClass=PluginData|PluginLogic|PluginDataAndLogic` / `PluginUnregister`
  - `disconnect`
- **Core layer `989fls`**, messages the client accepts from the server: `Hello`, `Message`, `ZonePlayerJoin`, `ZonePlayerQuit`, `BuddyInvite`, `PlayerKick`, `System`.
- **Plugin layers seen:**
  - `MLBAM`, registered after login.
  - In a game room: `CHATTEXT_<a>_<room>` for chat, as `<ChatText>message</ChatText>` sent to `target="zone"`, and `CHATOOB_<a>_<room>`, an out-of-band layer used for challenges.
- **Relaying:** challenge and chat payloads go client to client. The server forwards `target="plyr"` messages to that player and `target="zone"` messages to everyone else registered on the same layer, stamping `sender=<username> senderID=<id>` (the client shows `sender` as the chat name). It doesn't need to understand the payloads.

### Challenges (game rooms)
- A challenge is a client-to-client FLS message on layer `MLBAM`, `target="plyr" targetID=<opponent>`, carrying
  `<BinMsg>` (base64). The binary payload is a `CBinaryApplicationMessenger` frame: `u32 protocol (1)`, `u32 total size`,
  `char[32] sender username`, then the body. A 280-byte challenge holds both player IDs and the match settings.
  A 44-byte message follows when it's cancelled or times out (about 80 s). The server just relays these.
- The receiver gets a notification (bottom-left plus a controller rumble). The challenge is accepted from the
  **Quick Menu** (SELECT), which calls `POST players/batch_lookup.xml` (`usernames=a,b,…`, the pending challengers).
  **The reply must contain a `<players>` element, or the game freezes.**
- After accepting, the challenge goes on:
  1. The accepter sends a BinMsg of type 2 (accept), then type 6.
  2. The accepter calls `GET players/info2.xml?id=<opponent>` (`player.info_for_challenge`). The reply must contain
     `<player …/>`; it fills the CHALLENGER_PROFILE table.
  3. The challenger calls `POST mlb_games/start.xml` (`game_mode=0&opponent_player_id=<id>`). The reply must be
     `<game uuid="…"/>`; the client stores the uuid as the match ID.
  4. The two clients exchange BinMsg protocol 0 messages, relayed by the server: `10500` both ways, then `10501`
     (108 bytes) from the challenger, carrying match settings and the game uuid.
- These steps are "challenge modules" run in order: … `GetGameID` (10500/10501) → `SetSeed` → `Natpunch` → `Join` →
  `UserSettings` → … → `Start`.
- Before connecting, each client resolves the opponent's online ID with `sceNpLookupNpIdAsync`, then sets up
  **NP Signaling** (`sceNpSignalingCreateCtx` / `ActivateConnection`) to get a direct connection. The match then runs
  over PS3 UDP peer-to-peer sockets (`DGRAM-P2P`, RPCS3's port 3658), not the stream (`P2PS`) kind. RPCS3 never completes
  that lookup's transaction, so `sceNpLookupPollAsync` returns "busy" forever. The "Fix NP ID lookup hang" patch skips
  the poll; RPCS3 has already filled in the NP ID. The game does the same lookup again when a match ends (call at
  `0x7a994c`, poll at `0x7a99c4`); without the patch there, the online menu came back blank.
- Clients sometimes enter the only room as id 0 (`CHATTEXT_0_0`) instead of 1. The server treats both as one room.

### End of a match
- When a match ends, each client sends `POST mlb_games/create.xml` with one form field, `game_data`: JSON with
  `general` (`game_mode` `EXHIBITION`, `game_uuid` from `mlb_games/start`, both player and MLB team IDs,
  `is_complete`, `is_ranked`, and `home_game_state` or `away_game_state`), `pitcher_highlights`, `game_stats`,
  `box_score` and `game_log`. Seen states: `FINISHED` from both sides; `CONCEDE` from one side with `CONCEDE_ON` from the
  other; `QUIT` with `QUIT_ON` the same way. An empty success is enough: both games go back to the
  room, and the next challenge works.
- During a match both clients call `universal_profiles/view.xml?player_id=N`. A dropped attempt showed
  `POST league_games/cancel.xml`.

### Home Run Derby
Online Derby works with no extra server code: it uses the same rooms and FLS relay as a match. At the end each
client sends `POST hrd_stats/update_stats.xml` (`best_round`, `home_runs`, `longest` in feet, `place`, `rounds`,
`xp`), and the Derby menu calls `GET hrd_stats/my_stats.xml`. Both get an empty success.

## Telemetry

The game posts analytics to `mlb16.api.wwsga.me` (`POST /games/<uuid>/telemetry`, HTTPS on 443) as JSON:
`{"events":[{"header":{…},"data":{"event_type":…}}]}`. Our server answers `{}` and keeps the request in the host's
`requests.jsonl`; nothing is forwarded anywhere. Port 443 is optional and the game works without it.

Every event's header carries `user_id` (the PSN/RPCN name), `client_ipaddress` (the console's local address),
`session_id`, `client_timezone`, `client_timestamp` and `title_id`. The event types, from the EBOOT's strings (the
field names sit next to each event name) and from our logs (marked *seen*):

**Standard telemetry library** (strings at `0xfbc9xx`, event start `0x78acf0`):

| event | fields |
|---|---|
| `BootStart` (seen) | `build_version`, `disc_id`, `is_trial`, `issuer_id`, `np_communication_id`, `title_name` |
| `UserProfile` (seen) | `np_online_id`, `age`, `restrict_chat`, `restrict_ugm` |
| `HardwareProfile` (seen) | `Video_Width`, `Video_Height`, `Video_Mode`, `Resolution`, `capable_3d` |
| `NetworkProfile` (seen) | `connection_type`, `wifi`, `mac_address` |
| `MenuScreen` (seen) | `menu_screen`, `referrer`, `referrer_menu`, `time_on_screen` |
| `GameStart`, `GameEnd` (seen) | `game_id`, `mode`, `online`, `stadium_id`, `player_count`, `duration_secs`, … |
| `CurrencyAcquired` (seen), `CurrencySpent` | `currency_type` (Stubs), `amount`, `source` / `sink`, `prior_currency`, `new_currency` |
| `StoreStart`, `StoreEnd` (seen), `ItemDetailView`, `CartResult` | `store_session_id`, `sku`, `result_code`, `duration_secs`, `did_purchase` |
| `CommercePurchaseProduct`, `CommerceConsumeEntitlement` | `item_name`, `item_cost` |
| `FriendProfile` | `friend_list`, `block_list` |
| `SocialInteraction` | `target_np_account_id`, `target_np_account_name`, `interaction_type` |
| `TrophyAchieve` | `trophy_id`, `trophy_type`, `is_first_time` |

**The Show's own events:**

| event | fields |
|---|---|
| `ScreenVisit` (seen, `0xb5780`) | `username`, `screen_name`, `screen_time`, `game_mode`, `resolution` |
| `GameOptions` (seen) | `game_mode`, `play_mode`, `game_options`, `user_settings`, `is_online`, perks, training mode |
| `GameResult` (seen) | teams, scores, `end_type`, `local_player_win`, team and user ratings, `game_time` |
| `ModeOptions`, `Stadium`, `Faction_Level`, `Preloaded_Throw` (all seen) | mode settings, offered vs picked stadium, level, throwing controls |
| `AudioProfile` (seen) | HDMI/optical, encoder, channels, sample rate |
| `AudioInGameInfoExit`, `PresentationInfoExit`, `OsdInGameInfoExit` (seen) | `GAME_UUID` and a submit count |
| `MyArenaTeamComposition` | `player_ids`, `series_ids`, `matchup_stars` (Diamond Dynasty lineup) |

`ScreenVisit` and `MenuScreen` are most of the traffic: about 420 events in one evening of play, one per screen
visited. The friends list, social and purchase events never appeared in our logs (no PSN friends, no store purchases
on RPCN), but the game has them.

## Not done yet
- Saving results: match results (`mlb_games/create.xml`) and Derby stats are acknowledged but not stored, and the
  replies' expected contents aren't checked.
