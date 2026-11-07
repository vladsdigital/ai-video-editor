# comment-letters

**What it does:** a comment box appears above the head, the keyword's big letters drop in one by one in 3D above it, dark over the light parts of the picture and cream over the dark, then each letter falls into the box and becomes typed text, the comment posts and lifts up, and reply cards stack under it on a thread line, with a like.
**Job:** call to action, with a short keyword the speaker says.
**Trigger phrases:** "drop my comment keyword into a comment box letter by letter", "3D letters falling into a comment", "comment keyword with replies stacking".

## Footage it needs, and where it fails
- A keyword of 2 to 8 letters, about 3 to 5 s. Too short for the flow: it declines and says so.
- Room above the head for the letters and cards. Declines on a tight close-up.
- A still or drifting camera for the two-tone letters: on a moving camera set `TWO_TONE = False`.

## Adapting to the footage
- Box just above the head, big letters as big as the room over the box allows, the posted stack ends on the hair at most, everything scales together.
- `build.py` looks at a still of the slot and finds the line between light and dark in the band over the head. A background of one tone gets cream letters only (it prints that).

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): transparent graphics, `hf render` writes `renders/<slot>.webm`, the reel lays it over its own footage. `assets/aroll.mp4` (for the mask, and under SAFE snapshots), `words.json`, `clip.json`, `layout.json`. It writes `assets/lightmask.png`. Optional: the buyer's round picture in `assets/` (`AVATAR`).

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `KEYWORD` | the big word, 2 to 8 letters | required; letters drop when it is said |
| `HANDLE`, `AVATAR` | the buyer's real handle, picture | required, optional (`''` = a letter tile) |
| `REPLIES` | 1 or 2 short replies, they stack | the speaker's words |
| `PLACEHOLDER`, `POST`, `ME`, `NOW` | small words on the card | in the reel's language |
| `TWO_TONE` | dark over light, cream over dark | `True` |
| `TIMES` | seconds for: box, drop, fall, post, reply, like, out | `{}` |
| `SOUND` | low hit when the first letter lands | 0.26 |

STYLE block: `font`, `font_file`, `weight`, `tracking`, `small_font`, `small_weight` and the colours. The reel's style wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: KEYWORD, HANDLE, REPLIES in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # writes the mask, prints times, place and snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Cards off the eyes and forehead when the speaker leans in. Everything inside the safe zone.
- Each big letter readable where it crosses the light and dark line.
- Each typed letter appears as its big letter arrives. No real product's logo or interface: plain cards.
