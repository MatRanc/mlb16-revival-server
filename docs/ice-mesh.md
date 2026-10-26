# Pin-holes in player faces: the ICE mesh SPU cull

Notes on how [`patches/MLB16_triangle_fix.yml`](../patches/MLB16_triangle_fix.yml) was found, so it can be checked or
extended. Game: BCUS01089 v01.10. Addresses are virtual addresses in the decrypted EBOOT; "LS" is the SPU's local store.

## Symptom

With RPCS3's resolution scale above 100%, faces, ears and cap edges show thin lines and dots where the field or sky
shows through. It's worst at 300–500%, still visible at 100%, and is the same with depth of field on or off, MSAA on or
off, and SPU XFloat Accuracy set to Accurate.

## What the frame shows (RenderDoc)

- Pixel history on a hole: no draw touches the pixel at all, so no depth or alpha test failed.
- The head is 8 or more draws (face, eye area, nose, mouth, ears…), triangle lists with culling off. Where pieces meet,
  their shared vertices match bit for bit.
- Inside each piece there are small closed loops of open edges, exactly where the holes are. Measured in screen space,
  almost all of them are smaller than one 720p pixel. The triangles are missing from the index data RPCS3 was given.

## Where they go

The game processes character meshes on the SPU with Naughty Dog's **ICE** mesh library ("icemesh", "IMFE PPU Thread").
The SPU program is embedded in the EBOOT at `0x1161300` (size at `0x11612c4`, `c0dec0de` marker). It loads at LS
`0x4000`, so LS address = file offset in the module + `0x4000`, and EBOOT address = `0x1161300 + LS − 0x4000`.

The PPU side (`0x730c8`, called from the IMFE thread) builds a command list of 16-bit words per mesh: high byte =
command, low byte = argument. The SPU dispatches them through a table at LS `0x14770` (one word per command), with
argument counts in a byte table at LS `0x14740`. Relevant commands:

| cmd | LS handler | what it does |
|---|---|---|
| `0x0c` | `0x12830` | decompress the index list |
| `0x22` | `0x10190` | continuous LOD blend (geomorph) |
| `0x25` / `0x26` | `0x13520` / `0x13518` → `0x132e0` | **triangle cull** of skinned meshes: screen-space test at `0xd080`, then writes the new index count to context +276/+280 |
| `0x2c` | `0x12dc0` → `0x12c08` | **triangle cull** using an extra data block (loaded by `0x2b`): test at `0x82c0`, same write-back |
| `0x27` | `0x11790` | copy the (culled) index list to the output buffer |

The PPU emits `0x25`/`0x26` for every skinned mesh and `0x2c` when the mesh has the extra block. The culls drop
back-facing triangles and triangles that don't cover a 720p sample. That's invisible on a PS3 at 720p, but with
resolution scaling those slivers cover real pixels, so their absence shows as holes.

## The patch

Each of the three handlers is a tail-call entry, so replacing its first instruction with `bi $lr` (`0x35000000`) makes
the command a no-op. The index count then stays at the full value, which is the same state a mesh without culling
commands is in:

| EBOOT address | LS | original | patched |
|---|---|---|---|
| `0x011700c0` | `0x12dc0` (`0x2c`) | `br 0x12c08` | `bi $lr` |
| `0x01170818` | `0x13518` (`0x26`) | `il $4,1` | `bi $lr` |
| `0x01170820` | `0x13520` (`0x25`) | `il $4,0` | `bi $lr` |

Back faces are now drawn too. The depth test hides them, so the picture is the same at a small GPU cost, only for
characters. That's why the launcher makes it a checkbox (*Fix holes in player faces*, on by default) that people with weak GPUs
can untick. Tested at 300% in gameplay and the attract demo with no freeze and no visual regressions.

## Dead ends

- **Bypassing the SPU index path on the PPU** (`0x73278`, mask `0x8071` → 0): meshes set up for the SPU path have no
  GPU-side index list, and RSX fails with `rsx::get_address(offset=0x1fffffff): RSXIO memory not mapped`.
- **Only `0x2c`:** faces use `0x25`/`0x26`, so it changed nothing visible.
- **RPCS3 settings** (MSAA, SPU XFloat Accuracy Accurate): no effect, because the SPU does exactly what the game asks.

Ghidra doesn't decode SPU code here; any SPU disassembler works on the extracted module (bytes `0x1161300` to
`0x1161300 + size`).
