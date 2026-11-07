# key-rain (Key Rain)

**What it does:** keyboard keycaps with shortcut glyphs rain down, land with weight on the speaker's head and on an invisible shelf level with it, and stack row on row with real physics. The pile rides the head as it moves. On the sweep word a gold ruler bar crosses the frame and shoves the pile tumbling out of the side.
**Job:** explain. A line about hard, fiddly or endless work, cleared on a turn ("today", "now", "gone").
**Trigger phrases:** "rain keyboard keys on my head", "shortcuts pile up on me", "keycaps fall and stack up".

## Footage it needs, and where it fails
- Room above the head: about 130 px between the safe zone (y 220) and the head. A tight selfie stops with one line saying how much room there is.
- Still or drifting camera. The cutout is measured for the top of the head, nothing is layered. Without a cutout the pile stays still at the height from `layout.json`.
- A hand raised over the head is ignored in the measure.

## Adapting to the footage
- The keys size themselves so their rows fit between the head and the safe zone (at most 120 px tall, 4 rows). With little room a top row is left out.
- The bottom row covers only a sliver of the hair, never the face, and the whole pile moves with a slow follow of the head.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots.
`assets/aroll.mp4`, `assets/subject.webm` (measured), `words.json`, `clip.json`, the reel's `layout.json`. Physics: `pile_sim.py` beside `build.py`, plain Python and numpy, same result every run.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `KEYS` | rows, bottom first: `(shown, tiny word, width in key units, dark?)` | `None` = the default English set; in another language retype the tiny words. ⌘ ⌥ ⇧ ⌫ draw as shapes |
| `T_RAIN`, `RAIN_DUR` | first key, seconds to the last | a word or seconds; 1.15 s |
| `T_SWEEP` | when the bar crosses | required, a word or seconds. Needs about 0.4 s after it before the slot ends |
| `SWEEP_DIR` | `'right'` or `'left'` | `'right'` |
| `KEY_H`, `FLOOR_Y` | key height, shelf y | `None`, `None` = measured |
| `SOUND` | landings and sweep volume | .3, 0 = silent |

STYLE block: `font`, `weight`, `label_font`, `label_weight`, `key`, `key_lip`, `key_ink`, `key_dim`, `dark`, `dark_lip`, `dark_ink`, `dark_dim`, `ruler`.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: KEYS, T_RAIN and T_SWEEP in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # runs the physics, prints the pile size, the timing and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
`fx_new.py` prints these commands with the real paths filled in and saves them as `RUN.txt` in the slot. Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Keys land flat enough to read and rest on each other with no overlap.
- The bottom row touches the hair and never the face, as the head moves.
- The sweep clears every key out of the frame before the slot ends.
