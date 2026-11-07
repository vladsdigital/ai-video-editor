# reel-rain

**What it does:** the room behind the speaker dims and eight of the buyer's own videos tumble in out of the dark in 3D, two by two in two waves. Each tile flies up fast with a tilt and a thin cream edge while its picture is still dim and blurred, then the picture sharpens. They settle into a 4 x 2 wall behind the speaker (cutout in front), all playing, hold, then fall back into the dark as the room comes back. About 2 s.
**Job:** proof ("then my best videos", "sites, apps, systems", "everything we built").
**Trigger phrases:** "my best videos tumble in behind me", "a wall of my reels flying in behind me", "reel rain".

## The videos are the buyer's own
Ask for a folder of their own videos: at least 8, mp4 or mov, each about 2 s or longer. Copy them into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No videos, too few or too short: `build.py` stops and says what to ask for.

## Footage it needs, and where it fails
- One continuous shot, about 2.1 s, still or drifting camera, with the clean cutout (`assets/subject.webm`).
- Wide or medium. The wall is fixed in the upper frame: on a medium shot the head hides the lower middle tiles (the outer ones and the top row stay readable). A close-up hides most of it: leave it out.
- A weak cutout shows at the hair against bright tiles: look at the edge at full size.

**Slot inputs:** `assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, `clips/`. No extra Python packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder of the buyer's videos | `clips` in the slot, or a full path. File-name order is arrival order |
| `SKIP` | seconds skipped at the start of each video | 1.0 |
| `WORD` | the word the first tile appears on | a word said in this slot; `''` = `T_IN` |
| `T_IN` | first tile, slot seconds | `None` = 0.2 |
| `HOLD` | seconds from the first tile to the way out | 1.53 |

STYLE block: tile size, gaps, `top`, `radius`, `edge`, `dim` (0 keeps the room as it is), and the `cap_` lines.
**Switches:** `SAFE=1` guide (snapshots only), `CAPTIONS=0` no caption line (the default in a reel), `SFX=0` no sounds.

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
- First and last frames: the plain picture at full brightness.
- The speaker is never dimmed and never covered; the tiles pass behind the head and hands.
- Clean cutout edge against the brightest tile, at full size.
