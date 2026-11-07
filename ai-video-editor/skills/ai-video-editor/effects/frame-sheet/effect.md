# frame-sheet

**What it does:** the shot shrinks into cell 01 of a solid colour contact sheet (forest green by default). The numbered empty cells fill one real frame of this clip at a time, about one a frame, while a line of words rises in above them, then the camera snaps into the last cell and comes out as the live shot, full frame. Shrink 0.2 s, snap 0.12 s, the sheet about 1.3 to 1.6 s in all.
**Job:** hook. A line about time or amount, or one that should stop the scroll.
**Trigger phrases:** "fill a grid with frames of my video", "contact sheet", "one second of this video frame by frame".

## Footage it needs, and where it fails
- One continuous shot of about 3 s, with a phrase of about 1.5 s (declines when the sheet would get under 0.9 s). Any framing, any camera: the speaker is off screen while the sheet is up.
- A span across a cut is refused: the cells are this shot's frames and the dive lands back in it.

## Adapting to the footage
- The crop in each cell is placed from the face (layout.json), so the face sits in the same spot in every cell. Long lines get smaller type. The bottom right cells reach under the app's buttons (pictures and the number 30 only, nothing to read).

## Slot inputs
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout, no extra packages. `build.py` pulls the frames into `assets/sheet/` itself.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `LINES` | words above the grid, one string per line; every word must be said in the window | `None` = the spoken words, split by themselves |
| `T_IN`, `T_DIVE` | the shot starts to shrink, the snap starts (slot seconds) | first word from 0.4 s on; when the last word of the window ends |
| `SHRINK`, `DIVE` | length of the shrink and of the snap | 0.2 s, 0.12 s |
| `COLS`, `ROWS` | the grid | 6 x 5 = 30 frames, one second of video |
| `CURVE` | how the filling runs (under 1: a slow first few cells) | 0.87 |
| `LINE_SIZE` | largest size of the words | 112 |

STYLE block: `font`, `weight`, `tracking`, `case`, `ink` for the words (the reel's caption style wins), `ground` and `cell` for the sheet's flat colours.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` (no words above the grid; add the slot with `--captions keep` only if the reel's captions may sit on the sheet).

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. It hides the reel's captions while the sheet is up (`work/reel_captions.json`).

## What to look at in the final frames
- The first and last frames of the slot are the plain shot, and the frame after the dive has no jump.
- Each cell shows a face in the same place, with its number readable.
- The words rise in as they are said and the line stays under y 220.
