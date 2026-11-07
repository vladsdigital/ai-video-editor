# feed-flick

**What it does:** the speaker is flicked away into a full-screen phone feed: plain line buttons down the side, a back arrow, a search mark, a small circle and name at the bottom. The feed flicks past eight of the buyer's own videos, holding each for 3 frames, then 2, with one frame of heavy vertical motion blur between them, and a thin scroll mark walking down the edge. Then it brakes hard on the speaker: one soft frame, then sharp. About 1 s.
**Job:** hook or proof ("everyone is scrolling past", "I made all of these", "and then there is this one").
**Trigger phrases:** "flick through a feed of my videos and stop on me", "scroll a feed and land on me", "feed flick".

## The videos are the buyer's own
Ask for a folder of their own videos: at least 8, mp4 or mov. Copy them into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No videos or too few: `build.py` stops and says what to ask for. `HANDLE` is their own account name; leave it empty if they have not given one. No like or view numbers are drawn: never invent any.

## Footage it needs, and where it fails
- Any framing and camera, no cutout. One continuous shot around the landing.
- About 1 s before the word it brakes on, and 0.2 s after it. The buyer's videos fill the frame, cropped to 9:16: landscape ones lose their sides.
- Buttons and name sit where the real app's own buttons go, so on a real phone the platform's buttons land on the same spots for that second. It reads as a feed either way; say so if the buyer asks.

**Slot inputs:** `assets/aroll.mp4`, `words.json`, `clip.json`, `clips/`. numpy (already in the skill's Python). No cutout. `build.py` writes the blurred picture to `assets/tiles/`.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder of the buyer's videos | `clips` in the slot, or a full path. File-name order is feed order |
| `SKIP` | seconds skipped at the start of each video | 1.0 |
| `HOLDS` | frames each video stays still | `[2,3,3,3,2,2,2,2]`; its length is how many videos it needs |
| `WORD` | the word it brakes on | a word said in this slot; `''` = `T_LAND` |
| `T_LAND` | slot seconds of the braking frame | `None` = as early as the slot allows |
| `HANDLE`, `FOLLOW` | small name and pill word | the buyer's own name, a word in the reel's language; `''` = none |

STYLE block: `ui` colour and font, the `cap_` lines for the caption line. `BLUR` and `LAND` under the CLIP block set the smear.
**Switches:** `SAFE=1` guide (snapshots only), `CAPTIONS=0` no caption line (the default in a reel), `SFX=0` no sounds.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# first: the buyer's videos in <slot>/clips; edit WORD, HANDLE, FOLLOW in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1 CAPTIONS=0      # prints the beats and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py CAPTIONS=0      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- One blur frame between every two videos, no button on a blur frame, and the speaker sharp from the frame after the brake.
- First and last frames are the plain picture.
