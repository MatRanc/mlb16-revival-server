"""Pull the online config files out of your own installed v01.10 update.

The update's PATCH_GD.WAD stores frontend/servers_prod.xml and frontend/services.xml as plain text.
This finds each XML document in the archive and saves the two config files (plus any other XML found).

usage: python3 extract_gamedata.py [path/to/PATCH_GD.WAD] [out_dir=gamedata]
default WAD path: RPCS3's dev_hdd0/game/BCUS01089/USRDIR/PATCH_GD.WAD (Linux or macOS RPCS3 folder)
"""
import os, re, sys

default = [os.path.expanduser(p) for p in (
    '~/.config/rpcs3/dev_hdd0/game/BCUS01089/USRDIR/PATCH_GD.WAD',
    '~/Library/Application Support/rpcs3/dev_hdd0/game/BCUS01089/USRDIR/PATCH_GD.WAD')]
wad = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else next((p for p in default if os.path.exists(p)), default[0])
out = sys.argv[2] if len(sys.argv) > 2 else 'gamedata'
data = open(wad, 'rb').read()
os.makedirs(out, exist_ok=True)

starts = [m.start() for m in re.finditer(rb'<\?xml ', data)]
saved = 0
for n, s in enumerate(starts):
    m = re.match(rb'<\?xml[^>]*>\s*(?:<!--.*?-->\s*)*<(\w+)', data[s:s + 4096], re.S)
    if not m:
        continue
    root = m.group(1).decode()
    end = data.find(f'</{root}>'.encode(), s)
    if end < 0:
        continue
    doc = data[s:end + len(root) + 3]
    name = {'servers': 'servers_prod.xml', 'services': 'services.xml'}.get(root, f'doc{n}_{root}.xml')
    open(os.path.join(out, name), 'wb').write(doc)
    print(f'{name}: {len(doc)} bytes')
    saved += 1
if not saved:
    sys.exit(f'no XML found in {wad} - is this the v01.10 update PATCH_GD.WAD?')
