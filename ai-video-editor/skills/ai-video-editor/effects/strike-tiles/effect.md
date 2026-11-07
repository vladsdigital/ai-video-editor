# strike-tiles (Strike Tiles)

**What it does:** plain tiles pop up above the head on their names, a red pen line strikes through each one and the tile dulls. On the last word they hop and fall out of frame beside the head, and one italic word rises in their place, holds and fades.
**Job:** explain / proof. A list of things the viewer no longer needs, ending on one word.
**Trigger phrases:** "cross these out with a red pen as I name them", "icons that get struck through", "strike out the tools I name".

## Footage it needs, and where it fails
- A line that names 1 to 4 things and ends on one word, with about half a second between the last name and that word.
- Room above the head: about 150 px between the safe zone (y 220) and the head. A tight selfie stops with one line saying how much room there is.
- Any camera: the tiles are fixed to the screen, placed from `layout.json`.

## Adapting to the footage
- The tiles scale as one row to fit above the head (full size 225 px each) and centre on the head's x.
- They fall on the side of the head with more room, so nothing crosses the face. With no open side they shrink and fade above the head (the build prints it).
- Tiles are plain coloured squares with the name's first letter. The buyer's own images go in the slot's `tiles/` folder.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots.
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. Optional `tiles/`. No cutout, no extra packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `TILES` | `(name, word, image)` per tile, left to right | word = the word it pops up on (`'faktura'`, `'faktura#2'`, seconds). image = a file in `tiles/`, or `None` |
| `WORD` | the italic word at the end | required |
| `T_WORD`, `T_OUT` | when the word lands, when it fades | `None` = from `words.json`, .55 s after it lands |
| `STRIKE_AFTER` | from a tile popping up to its strike | .24 s |
| `Y`, `SCALE` | top of the tiles, size against full size | `None`, `None` |
| `SOUND` | pops, pen and fall volume | .3, 0 = silent |

STYLE block: `word_font`, `word_italic`, `word_weight`, `word_case`, `ink`, `label_font`, `label_weight`, `letter_font`, `letter_italic`, `pen`, `pen_tip`, `tiles` (fill and letter colour per tile), `shadow`.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: TILES and WORD in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the tile size, the timing and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
`fx_new.py` prints these commands with the real paths filled in and saves them as `RUN.txt` in the slot. Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Each tile pops on its word and the pen line runs past both of its edges.
- The falling tiles stay beside the head, never across the face.
- No real product's logo: lettered tiles, or images the buyer owns.
