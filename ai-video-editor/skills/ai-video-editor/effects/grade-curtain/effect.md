# grade-curtain

**What it does:** on the word, a thin light edge falls from the top of the frame in a third of a second, fast then slowing, and pulls a dark, drained grade behind it. Grain and a vignette hold while it is dark. At the end the edge rises back the same way.
**Job:** mood. A line that turns serious: a problem, a warning, a confession.
**Trigger phrases:** "make it moody on this line", "drop a dark curtain over the shot", "the colors go dark here".

## Footage it needs, and where it fails
- Any framing, any camera, one continuous shot. Footage that is already very dark changes less: use `LOOK = 'film'` there.
- Stops with a clear line when the slot has no room for the fall, a hold and the rise.

## Slot inputs
Full picture effect: `assets/aroll.mp4`, `words.json`, `clip.json`. No cutout, no extra packages beyond numpy.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `DROP` | the word it falls on | a word from words.json, or seconds |
| `LIFT` | when it rises | `auto`, a word, seconds, `None` to stay dark to a cut |
| `LOOK` | the grade | `mood`, `film`, `warm` |
| `GRAIN`, `VIGNETTE` | texture while dark | 8, .5 |

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
- The edge is one clean line with the plain picture under it and the dark one above it.
- The face is still readable while it is dark. If not, lower `VIGNETTE`.
- The last frame of the slot is the plain picture.
