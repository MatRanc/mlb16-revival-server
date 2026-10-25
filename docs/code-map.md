# Code map (EBOOT v01.10, BCUS01089)

These are addresses in the decrypted EBOOT (`PPU-395faa2b9c12c400d03343cad62ce7aad8ec985b`), as shown in Ghidra with the
PS3 loader (`PowerISA-Altivec-64-32addr`). The names are our own. This is a map for finding your way, not code.

To work out what a string-referencing function does, search for the string in Ghidra and follow its references.
File offset = virtual address − `0x10000` for the data and text segments of this EBOOT.

## Online kill switch and login
| address | what |
|---|---|
| `0xf0dd4` | Script command `TopLevel_VerifyAdvOnlineBranch`. In 1.10 it only shows "ONLINE DISABLED…" and returns 0. **Patched** to return 1. |
| `0xf0ffc` | Registers the UI script commands (name → handler table). |
| `0xb7664`, `0x248bac` | PSN sign-in flows: NetStart dialog, then ticket. Use the message "The Online features … are disabled." (`0x755b7c`). |
| `0x7a7a7c`, `0x7a8008` | NP sign-in and ticket request objects (`sceNpManagerRequestTicket2`, `GetTicket`, entitlements). |
| `0x251b48` | Registers the `OnlineStartup_*` script states and the `mlb_login.login` service. |
| `0xbe170` | `OnlineStartup_ConnectionCheck`: online state > 2. |
| `0x251a50`, `0x251aa4` | `OnlineStartup_WaitForFLSConnect` / `FLSConnectBranch`. |
| `0x250a54` | `mlb_login.login`: builds the request (`console_id`, `platform`, `ticket`) and parses `login_data` / `fls_data`. |
| `0x75f400` | `server.select` reply parser. |
| `0x75c3f8`, `0x75ef18` | `session.ping` request and its callback (stores the time of the last good ping). |
| `0x75f8b8` | Online manager update. Produces "Your connection to The Show Online has been lost." |

## HTTP layer
| address | what |
|---|---|
| `0x723c08` | Builds a transaction: URL, headers `X-SC-Tmx`, `X-Title-UUID`, `X-Analytics-Session-UUID`. |
| `0x755124` | Generic response check: `status` / `message` / `id` / `response` ("Response Error. Code 1/2"). |
| `0x7aed5c` | Parses the reply XML **only if** `Content-Type == application/xml;charset=utf-8`. |
| `0x7ae288`, `0x7afbb8` | XML helpers: find child element; read an attribute as an integer. |

## FLS
| address | what |
|---|---|
| `0x71bd74` | FLS client constructor. |
| `0x71ced4` | Connect: stores address, port and key, opens a TCP socket. |
| `0x71f11c` | Creates the cipher (0x434-byte object, vtable `0x1049dd0`) and keys it with `server_private_key`. |
| `0x72b0f0` | Cipher setkey (mode 3 = 256-bit key, copies the key string's bytes). The cipher is AES; its tables are built at runtime. |
| `0x719e14` | Builds an outgoing message (XML), pads to 16 bytes, encrypts. |
| `0x71ac28` | Queues a message for sending. |
| `0x71e304` | Receive and dispatch for layer `989fls` (`Hello`, `Message`, `ZonePlayerJoin`, …). |
| `0x71efd8` | Per-frame update: 5 s connect timeout, 15 s keepalive. |
| `0x71d188` | `PluginRegister`. |
| `0x71cc64` | Disconnect (sends `<disconnect/>`). |

## Features
| address | what |
|---|---|
| `0x23166c` | Live roster engine step (0 = done, 1 = busy, 2 = failed). **Patched** to return 0. |
| `0xb9700` | `content_update.latest` (LIVE_ROSTERS) parser. |
| `0x2893c4` | Game room entry check (`player_skill_level`, `min_skill` / `max_skill`). |
| `0x2a4c00` | `lobby_channel_player.list` request and reply (refreshes the `playerlist` table). |

## Game data
- The update's `PATCH_GD.WAD` stores `frontend/services.xml` and `frontend/servers_prod.xml` as plain text.
- The UI scripts (for example `ol_GameRoom`) are inside `MLBPS3_GD.WAD` as compiled data.
- WAD index entries (`*.WAD.HDR`) are `(name hash, size, offset)`. File contents are IFF chunks.
