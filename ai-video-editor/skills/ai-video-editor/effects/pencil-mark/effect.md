# pencil-mark

**What it does:** the shot snaps to high-contrast black and white on a spoken word. A rose-red grease pencil draws a loose loop round the head (measured, it follows slowly), a beat later a short handwritten word writes itself above and beside the head, and an arrow runs from it to the circle.
**Job:** point at the speaker on a line about them ("you", "me", "this guy").
**Trigger phrases:** "circle me in red pencil", "draw on the video with an arrow", "mark me with a handwritten word".

## Footage it needs, and where it fails
- One continuous shot, about 1.6 s from the snap. Room above or beside the head for the word.
- Stops with one line when the head fills the frame, the word is over 10 letters, the slot is too short, or the trigger word is not said.

## Adapting to the footage
- The circle's size comes from the measured head; the word goes on the emptier side (`PLACE` overrides). Without a cutout (`--no-cutout`) it uses layout.json's per-shot head and does not follow.

## Slot inputs
Full picture: the render holds the footage in grey, `hf render` writes `renders/<slot>.mp4`. `assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, `layout.json`.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `WORD` | the short handwritten word | required |
| `TRIGGER` / `F_SNAP` | spoken word the snap lands on / or a frame | from words.json |
| `F_BACK` | frame the colour comes back | `None` = holds to the slot end: the slot must end on a cut |
| `PLACE` | side of the word | `auto` |
| `SOUND` | a soft stroke sound | 0 (silent by default) |

STYLE block: `pencil`, `font`, `weight`, `word_px`, `stroke`, `contrast`.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: WORD, TRIGGER, F_BACK in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # measures the head, prints the frames and the snapshot list
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. The reel's captions keep running.

## What to look at in the final frames
- The circle sits round the whole head with the chin inside it and does not cross the eyes.
- The letters write on left to right. The arrow's tip stops short of the circle.
