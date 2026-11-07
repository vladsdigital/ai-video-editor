# film-cut

**What it does:** a hard vertical wipe with a thin white edge crosses the frame left to right in six frames and leaves the shot in a film look (deep blacks, teal shadows, warm highlights, some grain). It holds for one line, then cuts straight back on a frame.
**Job:** mood. One line that should feel like a film.
**Trigger phrases:** "make this line look like a film", "cinematic look on this line", "wipe into a film look".

## Footage it needs, and where it fails
- Any framing, any camera, one continuous shot. Very dark rooms lose shadow detail in the look: use `LOOK = 'mood'` or a lighter clip.
- Stops with a clear line when the look would hold for under 18 frames.

## Slot inputs
Full picture effect: `assets/aroll.mp4`, `words.json`, `clip.json`. No cutout, no extra packages beyond numpy.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `ON` | the word the wipe runs on | a word from words.json, or seconds |
| `BACK` | when it cuts back | `auto`, a word, seconds, `None` to hold to a cut |
| `LOOK`, `GRAIN` | the look | `film`, 7 |
| `SOUND` | a soft whoosh on the wipe | 0 |

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
- The edge is a clean upright line, plain picture to its right, the look to its left.
- Skin stays warm and alive, the shadows go deep without eating the face.
