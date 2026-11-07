# split-grade

**What it does:** a tilted white divider snaps in from the right with a small overshoot and settles across the speaker's face, the new grade on its right, the plain picture on its left, a round handle on it and two small tags up top. On the word it sweeps off to the left in five frames and the whole shot is in the new grade.
**Job:** reveal. Any line where something changes: then and now, "and it warms up".
**Trigger phrases:** "split the grade across my face", "before and after grade slider", "show the color grade with a slider".

## Footage it needs, and where it fails
- Any framing, any camera. The grade is baked from the slot's own frames, and a dark clip is lifted a little so the look lands (printed by the build).
- One continuous shot. Stops with a clear line when the word comes earlier than 13 frames into the slot.

## Slot inputs
Full picture effect: `assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout, no extra packages beyond numpy.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `COMMIT` | the word the line sweeps on | a word from words.json, or seconds |
| `LOOK` | the new grade | `warm`, `mood`, `film` |
| `LABELS` | the two tags | the reel's language; `None` = off |
| `SPLIT_AT`, `TILT` | where the line crosses the head, its lean | .22, 8 |
| `HANDLE_Y`, `TAG_Y` | place of the handle and the tags | `None` keeps the handle under the caption line |
| `OUT` | `auto` eases the grade off at the end; `None` holds it to a cut | |

STYLE block: `small_font` and `ink` for the tags, `card` for the tag on the plain side.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```

## What to look at in the final frames
- The line passes through the face and the handle sits under the chin and off the caption line.
- Left of the line is the plain picture, right of it the grade, with no seam after the sweep.
- The change reads at phone size. If it does not, try another `LOOK`.
