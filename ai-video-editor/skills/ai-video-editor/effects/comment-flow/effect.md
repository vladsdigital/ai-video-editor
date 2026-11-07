# comment-flow

**What it does:** the call to action. A dark block wipes white and folds into a comment field at the top, a two-line headline lands over it, the keyword types itself in and posts, a reply card slides in under it word by word, a like lands on the comment, the cards lift away, then a follow pill rises at the chest and its button presses.
**Job:** call to action, with a keyword the speaker says.
**Trigger phrases:** "show my comment keyword being typed and answered", "comment and follow on screen", "comment CTA with a follow button".

## Footage it needs, and where it fails
- A keyword the speaker says, or any moment when `TIMES` sets the typing. About 4 to 7 s; under about 3.5 s it declines.
- Room above the head for the cards (they scale down to fit, and decline below 62%). Any camera.

## Adapting to the footage
- The whole top stack scales with the room over the head and may touch the hair, never the face. The rhythm tightens by itself to fit the slot (the build prints the pace).

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): transparent graphics, `hf render` writes `renders/<slot>.webm`, the reel lays it over its own footage. `assets/aroll.mp4` only for SAFE snapshots, `words.json`, `clip.json`, `layout.json`. Optional: the buyer's round picture in `assets/` (`AVATAR`).

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `HEADLINE` | one or two short lines | the speaker's words |
| `KEYWORD` | what types in | required; typing starts when it is said |
| `HANDLE`, `AVATAR` | the buyer's real handle, picture | required, optional (`''` = a letter tile) |
| `REPLY` | the answer card, word by word | short |
| `FOLLOW`, `FOLLOWING`, `SUB` | button labels, small true line under the name | `''` = no small line |
| `PLACEHOLDER`, `ME`, `NOW` | small words in the field | in the reel's language |
| `TIMES` | seconds for: in, type, post, reply, like, out, follow, press, sub | `{}` = keep the look's rhythm |
| `HEAD_Y`, `FOLLOW_Y`, `SOUND` | place, ping on the press | `None`, `None`, 0.3 |

STYLE block: `font`, `weight`, `tracking`, `small_font`, `small_weight` and the colours. The reel's style wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: HEADLINE, KEYWORD, HANDLE, REPLY, SUB in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the pace, the place and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Cards clear of the eyes and forehead when the speaker leans in; inside the safe zone.
- Reply readable before it lifts away. If it flies past, make the slot longer.
- Follow pill under the reel's caption line. No real product's logo or interface: plain cards.
