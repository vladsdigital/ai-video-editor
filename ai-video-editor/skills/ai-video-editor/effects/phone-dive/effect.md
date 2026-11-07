# phone-dive

**What it does:** a dark title card with a small running timecode and a big serif line that rises in word by word (about 1 s). It cuts to the shot, full frame. The shot then shrinks in 0.27 s into a plain phone on the same flat colour, plays there with a small time bar and the spoken words under it, and dives back in 0.27 s until it fills the frame.
**Job:** transition. A time jump, or a "now look at this" line.
**Trigger phrases:** "title card, then shrink me into a phone", "a time jump card", "show this video on a phone".

## Footage it needs, and where it fails
- One continuous shot of about 3 s or more, any framing, any camera. Declines when the card gets under 0.5 s or the phone holds under 0.4 s.

## Adapting to the footage
- The card's words are the ones said on the card, or `TITLE`. The time bar reads the reel's real time and length. Up to 4 lines on the card.

## Slot inputs
`assets/aroll.mp4`, `words.json`, `clip.json`. No cutout, no extra packages.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `TITLE` | the card's lines | one line per word said on the card |
| `T_SHOT`, `T_SHRINK`, `T_GROW` | card out, shrink starts, dive starts | 35% of the slot; 0.35 s later; 0.35 s before the end |
| `SHRINK`, `GROW` | length of the moves | 0.27 s each |
| `PHONE`, `PHONE_END`, `PHONE_Y` | phone size at landing and at the dive, and its middle | 0.48, 0.525, y 797 |
| `CAP_Y` | words under the phone | y 1361 |

STYLE block: `ground`, `title_font`, `title_size`, `title_case`, `ink`, `tc`, `rule`, `body`, and `cap_font`, `cap_weight`, `cap_size`, `cap_case`, `cap_on`, `cap_off` for the words under the phone (the reel's caption style).
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` (no words under the phone).

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. It hides the reel's captions on the card and while the phone is up.

## What to look at in the final frames
- The card's first frame sits on the reel's cut, the last frames are the plain shot with no jump.
- The phone has no logo, no notch of a real device; the words sit under it, inside the safe zone.
