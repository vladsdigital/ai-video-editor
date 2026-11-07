# film-gate

**What it does:** the shot turns into running 35mm film. The film look cuts on with the word, sprocket rails snap in from both sides in five frames, the picture rolls one frame down and lands, and then it runs: holes stepping past at 15 steps a second, an optical soundtrack strip drawn from the real voice of this clip, flicker, gate weave, dust and a faint scratch. It cuts straight back at the end.
**Job:** mood. Old times, memories, "the whole scene changes".
**Trigger phrases:** "make it look like old film", "add film strip rails", "project it like 35mm".

## Footage it needs, and where it fails
- A head clear of the rails (about 110 px left, 80 px right). Stops with a clear line when the head reaches under them.
- A voice in the slot: the strip is drawn from it. Stops when the slot has no sound.

## Slot inputs
Full picture effect: `assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout. numpy and Pillow.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `ON` | the word it starts on | a word from words.json, or seconds |
| `BACK` | when it cuts back | `auto`, a word, seconds, `None` to run to a cut |
| `LOOK`, `GRAIN` | the picture | `film`, 8 |
| `EDGE_PRINT` | tiny print on the film edge | the reel's language; `''` = none |
| `DUST`, `RATTLE` | dust and flicker, projector ticks | 1, 1 |

STYLE block: colours of the rail, holes, strip and print. No real film brand in `EDGE_PRINT`.
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
- The strip's shape follows the voice: wide on loud words, a thin line in the pauses.
- The roll lands cleanly with one black frame line passing through.
- No dust on the face.
