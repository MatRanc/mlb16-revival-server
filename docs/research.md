# Digging further

How to get the game's own files from your copy, and the tools and approach used so far. The repo never includes these
files; everyone extracts them from their own game.

## The online config files
The v01.10 update's `PATCH_GD.WAD` contains `frontend/servers_prod.xml` (server addresses and ports) and
`frontend/services.xml` (all 347 API endpoints) as plain text. With the update installed in RPCS3:

```sh
python3 tools/extract_gamedata.py            # finds RPCS3's dev_hdd0/game/BCUS01089/USRDIR/PATCH_GD.WAD
python3 tools/extract_gamedata.py /path/to/PATCH_GD.WAD out_dir
```

It writes `gamedata/servers_prod.xml`, `gamedata/services.xml` and a couple of sample cached replies (`doc*_result.xml`,
handy for seeing the reply format).

## The EBOOT
To read the game's code, decrypt the update's `EBOOT.BIN` with RPCS3 (**Utilities → Decrypt PS3 Binaries**, pick
`dev_hdd0/game/BCUS01089/USRDIR/EBOOT.BIN`). Then load the resulting `EBOOT.elf` into Ghidra with the PS3 scripts.
[docs/code-map.md](code-map.md) lists the interesting addresses. The Ghidra setup is in
[mlb-show-rpcs3-fixes/docs/setup.md](https://github.com/MatRanc/mlb-show-rpcs3-fixes/blob/main/docs/setup.md).

Plain-text strings in the EBOOT are the fastest way in. Service names (`lobby_channel_player.join`), XML attribute names
(`player_skill_level`) and log messages sit next to the code that uses them.

## The UI scripts
Menu screens are scripts inside `MLBPS3_GD.WAD` on the disc. They're compiled, but their string constants are readable.
For example, the game room screen `ol_GameRoom` lists its services and table bindings. To search them without
unpacking:
```sh
7z e -so "MLB The Show 16.iso" PS3_GAME/USRDIR/MLBPS3_GD.WAD | grep -a -b -o "ol_GameRoom"
```

## Watching the game talk
`server/server.py` logs every request, every unknown endpoint (`"event": "unhandled"`) and every decrypted FLS message
to `server/requests.jsonl`. Unknown `.xml` endpoints get an empty success reply, so the game keeps going. When a
screen needs real data, the unhandled list tells you which endpoint to implement next. Find its reply parser in the
EBOOT by searching for the service name or the attribute names near it.

RPCS3's own log (`RPCS3.log`) shows DNS lookups (`DnsHook`), connections (`sys_net`) and PSN/RPCN calls (`sceNp`).
Raise channels to Trace in the config's `Log:` section, for example `sys_net: Trace`.
