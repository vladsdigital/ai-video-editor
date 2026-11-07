# app-delete (App Delete)

**What it does:** a cream panel of plain tiles with labels sits above the head and jiggles. Each tile is deleted on its name: its badge flushes pink and swells, the tile shrinks away, the rest close the gap and the count drops. On the last word what is left hops and falls out of frame beside the head, one big italic word rises in the panel, and the panel fades.
**Job:** explain / proof. A list of things the viewer no longer needs ("no X, no Y, nothing").
**Trigger phrases:** "delete these apps one by one as I name them", "jiggling tiles that get deleted", "a panel of icons that empties out".

## Footage it needs, and where it fails
- A line that names 2 to 6 things and ends on one word.
- Room above the head: about 200 px between the safe zone (y 220) and the head. A tight selfie stops with one line saying how much room there is.
- Any camera: the panel is fixed to the screen, placed from `layout.json`.

## Adapting to the footage
- The whole panel scales as one piece to fit above the head (full size 882 x 330 px), centred in the frame.
- The last tiles fall on the side of the head with more room, so nothing crosses the face. With no open side they shrink away inside the panel instead (the build prints it).
- Tiles are plain coloured squares with the name's first letter. The buyer's own images go in the slot's `tiles/` folder.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots.
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. Optional `tiles/`. No cutout, no extra packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `TILES` | `(name, word, image)` per tile, left to right | word = the word it is deleted on (`'faktura'`, `'faktura#2'`, seconds), `None` = stays and falls on the last word. image = a file in `tiles/`, or `None` |
| `WORD` | the word that takes the panel | required |
| `T_WORD`, `T_IN`, `T_OUT` | when the word lands, the panel appears, the panel fades | `None` = from `words.json` |
| `MODE`, `COUNT` | corner labels | in the reel's language. `COUNT` is `'{n} items'` or a dict by number for plural forms |
| `BADGE` | the small mark on a tile | `'minus'` or `'x'` |
| `Y`, `SCALE` | bottom of the panel, size against full size | `None`, `None` |
| `SOUND` | pops, fall and word volume | .3, 0 = silent |

STYLE block: `word_font`, `word_italic`, `word_weight`, `word_case`, `label_font`, `label_weight`, `mono_font`, `letter_font`, `letter_italic`, `panel`, `ink`, `mode`, `dim`, `badge`, `tiles` (fill and letter colour per tile).
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: TILES, WORD, MODE and COUNT in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the panel size, the timing and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
`fx_new.py` prints these commands with the real paths filled in and saves them as `RUN.txt` in the slot. Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Each tile goes on its word, and the badge flushes just before it.
- The falling tiles stay beside the head, never across the face.
- No real product's logo: lettered tiles, or images the buyer owns.
