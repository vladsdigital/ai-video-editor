# color-picker

**What it does:** a small cream palette card slides in beside the face, an eyedropper cursor taps five colours measured off this clip, one every 0.1 s, and each flies into the card with its hex code typing in. Then the shot steps three times towards dark and drained, and swatches, codes and the three small marks in the card's header step with it.
**Job:** mood. A line about the look, or about things going dull and grey.
**Trigger phrases:** "pick the colors off my shot", "eyedropper color grade", "palette card that changes with the grade".

## Footage it needs, and where it fails
- Room beside the face for a card 216 px wide. Stops with a clear line when there is none.
- Calm picture off the face to sample. The cursor and the flying swatches stay off the face: samples are only taken where the flight to the card clears the head.
- The speaker's cutout (tells clothes from the wall). Made by `fx_new.py`.

## Slot inputs
Full picture effect: `assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, the reel's `layout.json`. numpy.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `ON` | the word of the first grade step | a word from words.json, or seconds |
| `TITLE`, `LABELS` | the card's words | the reel's language |
| `OUT` | `auto` leaves in the last 0.4 s; `None` stays to a cut | |

STYLE block: `small_font`, `paper`, `ink`, `faint`. Every code on the card is measured, and every later code is the same colour through the grade.
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
- The cursor taps calm spots: the printed code matches what is under it.
- Cursor and swatches do not cross the face. The build prints a note if the cursor has to.
- The card is clear of the face and inside the safe zone.
