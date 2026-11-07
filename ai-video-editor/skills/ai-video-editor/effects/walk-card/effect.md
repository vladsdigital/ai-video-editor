# walk-card

**What it does:** a card unfolds in the free space over the speaker: a 16:9 picture on top and a deep green panel with a serif title under it. A round play button presses on a spoken word, the buyer's own walkthrough video starts playing inside, and titled chapters skip by (a hard cut in the picture, the numbered name slides up, a thin line runs along the bottom of the picture). Then the picture sinks into the green and the card folds away.
**Job:** explain ("I recorded a video walking you through it", "there are three parts", "here is how").
**Trigger phrases:** "show my walkthrough video in a card above my head", "a video card with chapters", "walk card".

## The video is the buyer's own
Ask for their own walkthrough video: one video (the chapters jump through it, `SOURCE_AT` says where) or one per chapter, mp4 or mov. Copy it into `clips/` in the slot (`fx_new.py --buyer-files <folder>`), or point `CLIPS` at the folder. The effect ships none. No video or too short: `build.py` stops and says what to ask for. Title and chapter names are their own words; no real product's logo or interface.

## Footage it needs, and where it fails
- **Wide shot, head top below about y 820:** the card sits above the head at full size (764 x 573). This is the look it was made for.
- **Chin above about y 700:** with no room above the head it sits on the chest under the chin, a little smaller, and `build.py` prints the `--caption-y` value for the reel's captions.
- **Medium shot with a low chin:** it sits beside the head in the larger free side, smaller (385 px wide on a 1080 frame with the head at x 440 to 830), and the title has room for about 16 characters.
- **Close-up with no room either side:** it declines with one line. It never covers the face.
- An overlay: any camera, and the span may cross cuts as long as every shot in it leaves the same space free.

**Slot inputs:** an OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `clips/`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout, no extra Python packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `CLIPS` | folder with the walkthrough | `clips` in the slot, or a full path |
| `TITLE` | the card's title | the buyer's words. Required |
| `KICKER`, `COUNT` | small words under the title before play | `''` = none |
| `CHAPTERS` | `[('name', 'word it starts on'), ...]` | 2 to 5; the word is said in this slot. `None` spreads them evenly |
| `PRESS_WORD` | the word the play button presses on | the card starts 7 frames before it; `''` = 0.25 s |
| `T_END` | when the card starts to close | `None` = 0.9 s after the last chapter starts |
| `SOURCE_AT` | one video: seconds where each chapter starts | `None` = spread through it |
| `FOCUS` | which part of a tall video the 16:9 picture keeps | .3 |
| `PLACE`, `HEAD_TOP` | `'auto'`, `'above'`, `'chest'`, `'side'`; head top when measured wrong | `'auto'`, `None` |

STYLE block: `panel`, the title, chapter and number fonts, `ink`, `track`, `radius`, and the `cap_` lines.
**Switches:** `SAFE=1` guide with footage (snapshots only), `CAPTIONS=0` no caption line (the default in a reel: the reel's captions keep running), `SFX=0` no sounds.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# first: the buyer's walkthrough in <slot>/clips; edit TITLE, CHAPTERS, PRESS_WORD in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1 CAPTIONS=0      # prints the place, the beats and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py CAPTIONS=0      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The press lands on the word; the video starts after it, not before.
- The card clears the head and the red area in a SAFE=1 snapshot. Every chapter name is readable on a phone.
