# camera-cuts

**What it does:** turns a hard cut into one fast camera move, 8 frames centred on the cut, chosen by name: `whip`, `zoom`, `spin`, `push`, `drop`. Every frame of the move is the average of many camera positions inside its shutter, in linear light, so bright things streak like through a lens. Sound stays a straight cut plus one whoosh.
**Job:** a transition, one per cut.
**Trigger phrases:** "make that cut a whip pan", "spin into the next shot", "zoom through to the next clip", "push transition", "drop into the next shot".

## Footage it needs, and where it fails
- Two shots with a hard cut, at least 6 frames each side (13 after the cut for `drop`). Stops with a reason when the span holds no cut or more than one. A cut in the middle of a word fights the move.
- `zoom` is the plain version and needs nothing from the shots; `zoom-through-cut` is the dive through dark fabric with the passage kept dark and captions travelling with it.

## Slot inputs
`assets/aroll.mp4` holding both shots, `clip.json` with `cut_frames`, the reel's `layout.json` for the head (zoom, spin). No cutout. Numpy and Pillow only.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `MOVE` | `whip`, `zoom`, `spin`, `push`, `drop` | required, by name |
| `HALF` | frames each side of the cut | 4 |
| `STRENGTH`, `SHUTTER` | size of the move, blur length | 1, 1 |
| `DIRECTION` | whip and push direction | 1 |
| `CENTRE` | centre of zoom and spin | `None` = the measured face per shot |
| `WHOOSH` | volume of the whoosh | .3; 0 = silent |

**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# fx_new.py camera-cuts --project <project> --from <cut - 0.5> --to <cut + 0.5>   (a second cut: add --name camera-cuts-2)
# edit: MOVE in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # bakes the plate, prints frames and snapshot list
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Both edges of the slot are the plain shots, the blur peaks on the cut, nothing stutters. Mirrored picture at the frame's edges only shows under heavy blur.
