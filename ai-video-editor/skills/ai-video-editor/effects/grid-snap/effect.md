# grid-snap

**What it does:** on a solid forest green backdrop the speaker's whole picture shrinks into the middle tile of a 3x3 grid, eight of the buyer's own videos pop in around it in a fixed order (all playing), then the tiles clear and the speaker snaps back to full frame. About 1.4 s from start to finish.
**Job:** proof ("look at everything I made", "500 members", "everyone is doing this"). Works anywhere: the frames before and after are the plain picture.
**Trigger phrases:** "shrink me into a grid of my videos", "put me in the middle of my reels", "grid snap".

## The videos are the buyer's own
Ask for a folder of their own videos: at least 8, mp4 or mov, each about 1.7 s or longer (a longer HOLD needs longer ones). Copy them into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No videos, too few or too short: `build.py` stops and says exactly what to ask for. Leave the effect out rather than repeat or borrow videos.

## Footage it needs, and where it fails
- Any framing and camera: the whole picture shrinks, no cutout. One continuous shot (it needs the same frames playing on the way in and out).
- 0.3 s before the shrink and 0.2 s after the way back, so the slot opens and closes on the plain picture.
- A very dark or empty speaker shot reads less well among bright tiles.

**Slot inputs:** `assets/aroll.mp4`, `words.json`, `clip.json`, `clips/`. No cutout, no extra Python packages. `build.py` cuts the videos to size into `assets/tiles/` (never the originals).

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder of the buyer's videos | `clips` in the slot, or a full path. File-name order fills the grid |
| `SKIP` | seconds skipped at the start of each video | 1.0 |
| `WORD` | the word the shrink starts on | a word said in this slot; `''` = `T_IN` |
| `T_IN` | shrink start, slot seconds | `None` = 0.3 |
| `HOLD` | seconds from the start of the shrink to the way back | 1.2 |

STYLE block: `backdrop`, tile size, `gap`, `radius`, and the `cap_` lines for the caption line (only drawn when no reel captions carry the words).
**Switches:** `SAFE=1` guide (snapshots only), `CAPTIONS=0` no caption line (the default in a reel: the reel's captions stay on top), `SFX=0` no sounds.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# first: the buyer's videos in <slot>/clips; edit WORD in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1 CAPTIONS=0      # prints the beats and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py CAPTIONS=0      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The first and last frames are the plain picture, with no green.
- No tile shows before its arrival frame; the eight are all full by about 0.8 s after the shrink starts.
- The tiles sit beyond the Reels safe zone by design, as pictures, not as text to read. Anything that has to be read stays on the caption line.
- Only the buyer's own material in the tiles. No real product's logo unless it is in their own video.
