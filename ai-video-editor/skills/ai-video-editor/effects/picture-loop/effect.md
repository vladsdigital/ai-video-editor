# picture-loop

**What it does:** a thin cream frame comes in from the edges of the screen and the whole shot shrinks inside it into a framed picture on the wall, while the speaker stays in front at full size. The picture holds the same live shot with the same picture in it, four levels deep. Then the picture bursts back out, the speaker pushing past the camera, and it lands on the plain shot. Shrink 0.26 s, burst 0.23 s.
**Job:** proof. A line like "what you see here is what you get".
**Trigger phrases:** "put a picture of me inside a picture of me", "picture in picture forever", "recursion".

## Footage it needs, and where it fails
- One continuous shot of about 2 s or more with the clean cutout. Declines under about 1.2 s, when the cutout is nearly empty, and when the speaker fills most of the frame.

## Adapting to the footage
- The picture hangs on the side with more wall beside the head (`SIDE`). The cutout keeps the speaker in front; inside each level the speaker is in front of the deeper levels too, as in a real picture of that picture.

## Slot inputs
`assets/aroll.mp4`, `assets/subject.webm`, `clip.json`, the reel's `layout.json`. Uses numpy and OpenCV, which the skill's Python has. `build.py` writes `assets/loop.mp4` and reuses it while the settings do not change.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `T_IN`, `T_BURST` | frame in, burst starts | 0.1 s; 0.48 s before the slot ends |
| `SHRINK`, `BURST` | length of the two moves | 0.26 s, 0.23 s |
| `SCALE`, `LEVELS` | size of each level, how deep | 0.55, 4 |
| `SIDE`, `TOP` | where the levels run to | the side with more wall, 0.258 |
| `PUSH` | how large the speaker gets in the burst | 1.9 |

STYLE block: `line` (colour of the frame), `line_px`.
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
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The cutout edge against the picture behind the head: this effect shows it.
- The picture is on the wall side and its first level's face is visible beside the head.
- First and last frames are the plain shot.
