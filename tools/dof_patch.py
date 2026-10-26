"""Generate patches/MLB16_dof_fix.yml: a better depth-of-field blur for MLB The Show 16 (BCUS01089 v01.10).

The game's close-up/replay blur is one RSX fragment program stored in the EBOOT (2X MSAA variant at 0x1121cc0, 4XR at
0x1122080, same code). It averaged 5 taps about 3 px apart, which showed as doubled copies of the background and a halo
around in-focus objects with resolution scaling. This rebuilds it:
- 16 taps on a golden-angle spiral (radius R px at 720p) plus the centre, averaged by weight;
- a tap is dropped when it is nearer than the centre pixel AND in focus (its own CoC, from the game's formula, is small),
  so a sharp ball can't bleed into the blurred crowd but a blurred player still spreads over what's behind him;
- the blend factor is clamped to 0..1 (the game's reached ~2.4 for far objects, overshooting the sharp/blur lerp).
The depth/CoC part of the original is kept word for word. The new program is 167 slots, too big for the original
0x340 bytes, so it goes in the unused tail of the code segment's last 64K page (0x10a4400, past the file end 0x10a43e8)
and both headers' ucode size/offset and parameter tables point there.

usage: python3 dof_patch.py path/to/EBOOT.elf [R=2.4 eps=0.001] > ../patches/MLB16_dof_fix.yml
Needs your own decrypted v01.10 EBOOT.elf. --disasm prints the new program's opcodes instead.
"""
import math, struct, sys

args = [a for a in sys.argv[1:] if a != '--disasm']
eboot = open(args[0], 'rb').read()
R, EPS = (float(args[1]), float(args[2])) if len(args) > 2 else (2.4, 0.001)
VARIANTS = (0x1121cc0, 0x1122080)   # program headers: size at +0, ucode offset at +0x10, table at +0x48 (28 u16)
NEW = 0x10a4400
N = 16


def read(va, n):
    phoff, = struct.unpack_from('>Q', eboot, 0x20)
    phentsize, phnum = struct.unpack_from('>HH', eboot, 0x36)
    for i in range(phnum):
        p_type, _, off, vaddr, _, filesz = struct.unpack_from('>IIQQQQ', eboot, phoff + i * phentsize)
        if p_type == 1 and vaddr <= va < vaddr + filesz:
            return eboot[off + va - vaddr: off + va - vaddr + n]
    raise ValueError(hex(va))


# RSX fragment ucode: 16-byte slots of 4 u32 words, halfwords swapped in memory. Bit layout: RPCS3 RSXFragmentProgram.h
def word(b, i):
    w, = struct.unpack_from('>I', b, i)
    return ((w & 0xFFFF) << 16) | (w >> 16)


def raw(words):
    return b''.join(struct.pack('>I', ((w & 0xFFFF) << 16) | (w >> 16)) for w in words)


def cslot(vals):
    return raw([struct.unpack('>I', struct.pack('>f', v))[0] for v in vals])


def setbits(w, lo, n, v):
    m = ((1 << n) - 1) << lo
    return (w & ~m) | ((v << lo) & m)


def src(w, reg, sw='xyzw', neg=0, rtype=0):   # rtype 0 = temp register, 2 = inline constant (next slot)
    for lo, n, v in ((0, 2, rtype), (2, 6, reg), (8, 1, 0), (9, 8, sum('xyzw'.index(c) << 2 * k for k, c in enumerate(sw))),
                     (17, 1, neg)):
        w = setbits(w, lo, n, v)
    return w


def dst(w, reg, mask='xyzw'):
    return setbits(setbits(setbits(w, 1, 6, reg), 7, 1, 0), 9, 4, sum(1 << 'xyzw'.index(c) for c in mask))


orig = read(VARIANTS[0] + 0x80, 0x340)
assert all(read(h + 0x80, 0x340) == orig for h in VARIANTS), 'unexpected EBOOT: blur programs differ'
slot = lambda i: orig[16 * i:16 * i + 16]
logical = lambda i: [word(orig, 16 * i + 4 * k) for k in range(4)]
T_MAD, T_TEX = logical(7), logical(9)   # unconditional MAD / TEX [tex2]
OP = {'MOV': 1, 'MUL': 2, 'ADD': 3, 'MAD': 4, 'DP3': 5, 'DP4': 6, 'MAX': 9, 'SLT': 10, 'SGE': 11, 'DIV': 58}
C = object()   # an inline-constant source


def alu(op, d, mask, *srcs, const=None, sat=0):   # srcs: (reg, swizzle[, neg]) or C; built on the MAD template
    w0, s0, s1, s2 = T_MAD
    w0 = setbits(setbits(dst(w0, d, mask), 24, 6, OP[op] & 63), 31, 1, sat)
    s1 = setbits(s1, 31, 1, OP[op] >> 6)
    out = []
    for w, s in zip((s0, s1, s2), list(srcs) + [None] * (3 - len(srcs))):
        if s is None: out.append(setbits(w, 0, 2, 0))   # unused source must not look like an inline constant
        elif s is C: out.append(src(w, 0, rtype=2))
        else: out.append(src(w, s[0], s[1], neg=s[2] if len(s) > 2 else 0))
    return raw([w0] + out) + (cslot(const) if const else b'')


def tex(d, s, sw, unit):
    w0, s0, s1, s2 = T_TEX
    return raw([setbits(dst(w0, d), 17, 4, unit), src(s0, s, sw), s1, s2])


taps = [(R * math.sqrt((i + 0.5) / N) * math.cos(i * 2.39996), R * math.sqrt((i + 0.5) / N) * math.sin(i * 2.39996))
        for i in range(N)]
# taps decode depth like the original (z = dot(floor(tex.yxw*255+.5), C8)) without the floor, so the weights fold in 255
K = [255 * struct.unpack('>f', struct.pack('>I', word(slot(13), 4 * k)))[0] for k in range(3)]

COC = [0, 1, 2, 3, 4, 5, 6, 12, 13]   # ... DP3 R0.z = centre depth
code = b''.join(slot(i) for i in COC)
code += alu('MOV', 4, 'x', (0, 'zzzz'))   # R4.x = centre depth
# rest of the CoC chain -> H1.x: CoC = (z^16 - P.x) / (z^16 < P.x ? P.y : P.z). DOFparameters P is loaded into R13 once
# for the taps; the SLT that read P.x from an inline constant reads R13.x instead
code += b''.join(slot(i) for i in (14, 23, 26, 29))
code += alu('MOV', 13, 'xyzw', C, const=[0, 0, 0, 0])
d, s0, s1, s2 = logical(30)
code += raw([d, s0, src(s1, 13, 'xxxx'), s2])
code += b''.join(slot(i) for i in (32, 33, 40, 44, 45))
for i in (46, 47):   # MOV/DIV H1.x, now saturated
    d, s0, s1, s2 = logical(i)
    code += raw([setbits(d, 31, 1, 1), s0, s1, s2]) + (slot(48) if i == 47 else b'')
layout = COC + [None] + [14, 23, 26, 29] + [None, 'P'] + [30] + [32, 33, 40, 44, 45, 46, 47, 48]
moved = {old: new for new, old in enumerate(layout) if old is not None}
# live: R2 = uv.xy / texel.zw, H1.x (R0.zw) = blend factor, R4.x, R13 = P
code += alu('MOV', 8, 'xyzw', C, const=K + [EPS])
code += alu('ADD', 4, 'x', (4, 'xxxx'), (8, 'wwww', 1))   # R4.x = centre depth - eps
code += alu('DIV', 17, 'y', C, (13, 'yyyy'), const=[1, 1, 1, 1])
code += alu('DIV', 17, 'z', C, (13, 'zzzz'), const=[1, 1, 1, 1])
code += alu('ADD', 17, 'w', (17, 'yyyy'), (17, 'zzzz', 1))   # R17 = (_, 1/P.y, 1/P.z, 1/P.y - 1/P.z)
code += tex(11, 2, 'xyzw', 2)   # R11 = sum, starts with the centre tap at weight 1
cols = [3, 6, 9, 10]
for g in range(N // 4):   # 4 taps per group: colours in R3/R6/R9/R10, depths -> R7
    for p in range(2):
        (ax, ay), (bx, by) = taps[4 * g + 2 * p], taps[4 * g + 2 * p + 1]
        code += alu('MAD', 1, 'xyzw', (2, 'zwzw'), C, (2, 'xyxy'), const=[ax, ay, bx, by])
        code += tex(cols[2 * p], 1, 'xyzw', 2) + tex(5, 1, 'xyzw', 1)
        code += tex(cols[2 * p + 1], 1, 'zwzz', 2) + tex(1, 1, 'zwzz', 1)   # TEX reads R1.zw before writing R1
        code += alu('DP3', 7, 'xyzw'[2 * p], (5, 'yxww'), (8, 'xyzw'))
        code += alu('DP3', 7, 'xyzw'[2 * p + 1], (1, 'yxww'), (8, 'xyzw'))
    for k in range(4):
        code += alu('MUL', 14, 'xyzw', (7 if k == 0 else 14, 'xyzw'), (7 if k == 0 else 14, 'xyzw'))   # z^16
    code += alu('SLT', 15, 'xyzw', (14, 'xyzw'), (13, 'xxxx'))
    code += alu('ADD', 14, 'xyzw', (14, 'xyzw'), (13, 'xxxx', 1))
    code += alu('MAD', 15, 'xyzw', (15, 'xyzw'), (17, 'wwww'), (17, 'zzzz'))
    code += alu('MUL', 14, 'xyzw', (14, 'xyzw'), (15, 'xyzw'), sat=1)   # each tap's own CoC, 0..1
    code += alu('SGE', 7, 'xyzw', (7, 'xyzw'), (4, 'xxxx'))   # 1 where the tap is not nearer than the centre
    code += alu('MAX', 7, 'xyzw', (7, 'xyzw'), (14, 'xyzw'))   # ...or is blurred enough to spread over it
    for k in range(4):
        code += alu('MAD', 11, 'xyzw', (cols[k], 'xyzw'), (7, 'xyzw'[k] * 4), (11, 'xyzw'))
    code += alu('MOV', 12, 'xyzw', (7, 'xyzw')) if g == 0 else alu('ADD', 12, 'xyzw', (12, 'xyzw'), (7, 'xyzw'))
code += alu('DP4', 12, 'x', (12, 'xyzw'), C, const=[1, 1, 1, 1])
code += alu('ADD', 12, 'x', (12, 'xxxx'), C, const=[1, 1, 1, 1])   # + centre
code += alu('DIV', 11, 'xyzw', (11, 'xyzw'), (12, 'xxxx'))
code += slot(39)   # TEX R2 = sharp colour [tex0]
d, s0, s1, s2 = logical(49)
code += raw([d, src(s0, 11), s1, s2])   # ADD H0 = R11 - R2
code += slot(50) + slot(51)   # FENCB, MAD H0 = lerp END
dead = len(code) // 16   # the 10 old offset/weight parameters get written here, past END
code += bytes(16)

old_tbl = struct.unpack('>28H', read(VARIANTS[0] + 0x48, 56))
assert old_tbl[:7] == (1, 5, 4, 0x30, 0x2d, 0x21, 0x1f), old_tbl
table = struct.pack('>28H', 1, moved[5], 4, moved[48], moved[45], moved[33], moved['P'], *([1, dead] * 10), 0)

if '--disasm' in sys.argv:
    NAMES = {v: k for k, v in OP.items()} | {0x11: 'FLR', 0x17: 'TEX', 0x3E: 'FENCB'}
    i = 0
    while i < len(code):
        d, s0, s1, s2 = (word(code, i + 4 * k) for k in range(4))
        op = ((d >> 24) & 63) | ((s1 >> 31) << 6)
        consts = 2 in (s0 & 3, s1 & 3, s2 & 3)
        print(f'{i // 16:3d} {NAMES.get(op, hex(op))}' + (' (+const)' if consts else '') + (' END' if d & 1 else ''))
        i += 32 if consts else 16
        if d & 1:
            break
    sys.exit()

print(f'''Version: 1.2

PPU-395faa2b9c12c400d03343cad62ce7aad8ec985b:
  "Better depth of field":
    Games:
      "MLB The Show 16":
        BCUS01089: [ 01.10 ]
    Author: "mister"
    Notes: "The depth-of-field blur in close-ups and replays averaged 5 taps about 3 pixels apart, which showed as doubled copies of the background and a halo around in-focus players with resolution scaling. Replaces it with a 17-tap depth-aware blur ({R:g} px radius at 720p): in-focus objects no longer bleed into the background. Generated by tools/dof_patch.py."
    Patch Version: 3.0
    Patch:''')
for k in range(0, len(code), 8):
    print(f'      - [ be64, 0x{NEW + k:08x}, 0x{code[k:k + 8].hex()} ]')
for hdr in VARIANTS:
    h = read(hdr, 0x80)
    nh = bytearray(h)
    struct.pack_into('>II', nh, 0, len(code), struct.unpack_from('>I', h, 4)[0])
    struct.pack_into('>I', nh, 0x10, (NEW - hdr) & 0xFFFFFFFF)
    nh[0x48:0x48 + 56] = table
    for k in range(0, 0x80, 8):
        if nh[k:k + 8] != h[k:k + 8]:
            print(f'      - [ be64, 0x{hdr + k:08x}, 0x{nh[k:k + 8].hex()} ]')
