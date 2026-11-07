# room-swap

**What it does:** the buyer's own walkthrough video slides in from the right and replaces the room behind the cutout. A green plate opens on the chest with a numbered chapter name and a segmented progress row. Each new chapter slides in from the right over the last one while the name changes and the next segment fills. Large captions run under the plate. At the end the real room slides back the same way and the plate wipes away.
**Job:** explain ("I recorded a video walking you through it", "sites, apps, systems", any line that lists steps).
**Trigger phrases:** "put my walkthrough video behind me with chapters", "replace the room with my screen recording", "room swap".

## The video is the buyer's own
Ask for their own walkthrough video: one video (the chapters jump through it, `SOURCE_AT` says where) or one per chapter, mp4 or mov. A tall picture fills the frame; a landscape screen recording is cropped to 9:16 around `FOCUS`, so ask for one that reads when cropped. Copy it into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No video or too short: `build.py` stops and says what to ask for. Chapter names are their own words; no real product's logo or interface.

## Footage it needs, and where it fails
- One continuous shot, still or drifting camera, with the clean cutout (`assets/subject.webm`). Wide or medium.
- Room between the chin and the captions for the plate. A chin below about y 1150 and the plate no longer fits: `build.py` stops.
- The whole room is replaced, so anything not on the cutout (a desk or laptop the cutout does not hold) disappears for those seconds. Look at the first snapshot.
- Hair and hands against a bright walkthrough show the cutout's edge: look at it at full size.

**Slot inputs:** `assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, `clips/`. No extra Python packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder with the walkthrough | `clips` in the slot, or a full path |
| `CHAPTERS` | `[('name', 'word it starts on'), ...]` | 2 to 5; the first word is when the room starts to change. `None` spreads them evenly |
| `END_WORD` | the word the real room slides back on | `''` = 1.4 s after the last chapter starts |
| `SOURCE_AT` | one video: seconds where each chapter starts | `None` = spread through it |
| `SKIP`, `FOCUS` | start skipped per video; which part a crop keeps | 1.0, .5 |

STYLE block: the plate's colour, size and place, the name and number fonts, `ink`, `track`, and the `cap_` lines (the reel's caption style goes here). `SLIDE`, `OPEN`, `SHUT`, `LEAD` under the CLIP block set the motion.
**Switches:** `SAFE=1` guide (snapshots only), `CAPTIONS=0` no captions (the reel's own keep running: add the slot with `--captions keep`), `SFX=0` no sounds.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# first: the buyer's walkthrough in <slot>/clips; edit CHAPTERS and END_WORD in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the beats and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- First and last frames: the plain picture, the real room.
- The plate clears the chin; the captions stay readable over the walkthrough.
- Clean cutout edge against the brightest chapter, at full size.
