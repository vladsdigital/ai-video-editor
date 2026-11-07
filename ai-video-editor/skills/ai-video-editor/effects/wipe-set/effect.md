# wipe-set

**What it does:** turns a hard cut into a shape wipe, chosen by name, with a thin light line on its edge: `iris` (a circle accelerates open from the speaker's face in the next shot), `blinds`, `barn doors`, `clock wipe`. 6 to 12 frames centred on the cut; the sound stays a straight cut.
**Job:** a transition, one per cut.
**Trigger phrases:** "make that cut an iris wipe", "blinds on this cut", "barn doors", "clock wipe".

## Footage it needs, and where it fails
- Two shots with a hard cut in the reel, with at least half the wipe plus 2 frames on each side. Stops with a reason when the span holds no cut or more than one.

## Adapting to the footage
- The iris and clock centre on the head of the next shot, from layout.json (`CENTRE` overrides). Each frame is drawn from the shots themselves: shot A plays up to the cut with shot B's first frame held in the shape, then shot B plays with shot A's last frame held round it.

## Slot inputs
`assets/aroll.mp4` holding both shots, `clip.json` with `cut_frames` (fx_new.py writes it), the reel's `layout.json`. No cutout. Numpy only.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `WIPE` | `iris`, `blinds`, `barn doors`, `clock wipe` | required, by name |
| `FRAMES` | length | `None` = 6, 10, 8, 12 |
| `BLINDS` | slats of `blinds` | 9 |
| `CENTRE` | centre of iris and clock | `None` = the measured face |
| `SOUND` | one soft whoosh on the cut | 0 (silent by default) |

STYLE block: `edge`, `edge_px`.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# fx_new.py wipe-set --project <project> --from <cut - 0.5> --to <cut + 0.5>   (a second cut: add --name wipe-set-2)
# edit: WIPE in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # bakes the plate, prints frames and snapshot list
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Both edges of the slot are the plain shots. The edge line is clean all the way round. No held frame on a blink.
