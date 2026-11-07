# live-grid

**What it does:** six of the buyer's own videos, all playing, drop from above the frame one after another and land with weight in a 3 x 2 grid behind the speaker (cutout in front). Each one speeds up as it falls, hits, sinks a few pixels, and its tilt dies away. Then they lift out, last one first. The room stays as it is. About 2 s.
**Job:** proof ("look, all of these", "every one of them works").
**Trigger phrases:** "drop my videos in a grid behind me", "my reels fall in behind me", "live grid".

## The videos are the buyer's own
Ask for a folder of their own videos: at least 6, mp4 or mov, each about 2 s or longer. Copy them into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No videos, too few or too short: `build.py` stops and says what to ask for.

## Footage it needs, and where it fails
- One continuous shot, about 2.1 s, still or drifting camera, with the clean cutout (`assets/subject.webm`).
- Wide or medium. The wall is fixed in the upper frame: on a medium shot the head hides much of the lower middle tile. A close-up hides most of it: leave it out.
- A weak cutout shows at the hair against bright tiles: look at the edge at full size.

**Slot inputs:** `assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, `clips/`. No extra Python packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder of the buyer's videos | `clips` in the slot, or a full path. File-name order is the order they drop |
| `SKIP` | seconds skipped at the start of each video | 1.0 |
| `WORD` | the word the first tile starts falling on | a word said in this slot; `''` = `T_IN` |
| `T_IN` | first fall, slot seconds | `None` = 0.2 |
| `HOLD` | seconds from the first tile to the way out | 1.43 |

STYLE block: tile size, `gap`, `top`, `radius`, `edge`, and the `cap_` lines. `FALL_FRAMES`, `BOUNCE`, `SETTLE`, `LIFT_FRAMES` under the CLIP block set the weight.
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
- First and last frames: the plain picture.
- The tiles pass behind the head and hands, never over them. Every tile lands in its own place and is level by the time the next two have landed.
- Clean cutout edge against the brightest tile, at full size.
