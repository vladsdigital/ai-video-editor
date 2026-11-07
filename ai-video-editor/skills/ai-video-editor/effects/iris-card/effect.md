# iris-card

**What it does:** an iris closes on the speaker's face (it follows the head measured on every frame), holds a beat on the head, goes to black; a dark green card opens out of the black in a circle; a thin double frame with small ornaments draws itself clockwise; the line comes in word by word in a serif as it is said, its last words large in italic under a small rule; then the iris reopens through the card onto the speaker.
**Job:** a line that lands on its own: a hook, a verdict, a turn.
**Trigger phrases:** "close on my face and put that line on a title card", "iris out to a title card", "silent film card for this line".

## Footage it needs, and where it fails
- A head in the picture and one short line (up to about 8 words) with about 0.7 s before it and 0.3 s after it. The close may sit on the end of the line before, across a cut: the head is followed per shot.
- Stops with a one-line reason when a word of `LINE` is not said in the slot, the slot leaves no time to close or reopen, or the cutout has no speaker.

## Adapting to the footage
- The hold radius comes from the measured head length. Long lines wrap and get smaller by themselves. No cutout: `--no-cutout` uses layout.json's per-shot head (no following inside a shot).

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): transparent outside the iris, `hf render` writes `renders/<slot>.webm`, the reel lays it over its own footage. `assets/subject.webm`, `words.json`, `clip.json`, the reel's `layout.json`, `segments.json`. Serif files in `fonts/` (EB Garamond, OFL, with č ć š ž đ).

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `LINE` | the words on the card, as spoken, in order | required |
| `BIG` | how many last words go large in italic | 2; 0 = none |
| `T_CLOSE`, `T_OPEN` | when the iris starts closing and reopening | `None` = from the words |
| `LINE_PX`, `BIG_PX` | sizes | 100, 138 |
| `SOUND` | soft whoosh on the close | 0 (silent by default) |

STYLE block: `font`, `font_file`, `big_font`, `big_file`, `big_italic`, `weight`, `case`, `ink`, `line`, `ground`, `black`, `dust`. A family from assets/fonts/fonts.css: set its `*_file` to None.
**Switches:** `SAFE=1`, `PREVIEW=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: LINE and BIG in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # measures the head, prints the times and the snapshot list
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
In a reel: `fx_add.py` hides the reel's captions only while the iris and card are up (`work/reel_captions.json`).

## What to look at in the final frames
- The iris stays centred on the head on the hold frames and the reopen.
- Letters č ć š ž đ in the card's serif, no word touching the frame, frame inside the safe zone.
