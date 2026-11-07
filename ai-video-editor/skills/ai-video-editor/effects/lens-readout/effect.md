# lens-readout

**What it does:** the picture starts punched in, a lens-distance strip snaps open above the head, its scale spins from tight numbers to wide ones while the picture pulls out to full, the strip goes, and the next words build letter by letter: a heavy line over a thin running rule, a serif italic line under it.
**Job:** a change of scale, a reveal, a "let me show you" line.
**Trigger phrases:** "do the lens strip and pull out when I say X", "zoom out with the lens numbers".

## Footage it needs, and where it fails
- One continuous shot of 2 s or more, the head with about 130 px above it inside the safe zone. No room: it declines.
- Start the slot on a cut of the reel: the picture then opens punched in. Anywhere else it eases into the punch over 8 frames first.
- The punch is an upscale of the footage: on a 1080 source it looks a little soft until the pull ends.

## Slot inputs
A full-frame effect (the picture itself moves): `hf render` writes `renders/<slot>.mp4`. `assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout. Pillow from the skill's own Python.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `HEAVY`, `ITALIC` | the two lines, the speaker's words after the pull | `''` = strip and pull only |
| `NUMBERS` | the scale, tight to wide | 85, 70, 50, 35, 24 |
| `PUNCH` | punch-in before the pull | 1.40 |
| `T_STRIP`, `T_PULL`, `T_STRIP_OUT` | strip open, spin and pull, strip gone | first word; 0.2 s after open; 0.6 s after the pull |
| `T_HEAVY`, `T_ITALIC`, `T_OUT` | first letters, words gone | when said; 0.45 s after the last word |
| `STAGGER` | frames between letters | 1.5 |
| `SOUND` | a whoosh on the spin | 0 (the look is silent) |

STYLE block: `font`, `weight`, `tracking`, `serif_font`, `serif_weight`, `serif_italic`, `num_font`, `num_weight`, `ink`, `accent`, `card`, `band`. The reel's look wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` (strip and pull only).

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder)
```
# edit: HEAVY and ITALIC in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. The reel's captions keep running during the strip and are hidden while the words are up.

## What to look at in the final frames
- The strip and the lines clear the head, also while punched in. The frame edge never shows during the pull.
- The last frame of the slot is the plain picture at full size, so the next shot joins cleanly.
