# cover-build

**What it does:** a whole magazine page builds behind the speaker's head on one line. A thin gold frame draws itself from the top left corner, the masthead drops letter by letter and flips dark over anything bright behind it, a small line of type runs across above it, a barcode lands, two coverlines rise on the words, a round sticker slaps on, and the picture leaves through the next cut in a short zoom blur.
**Job:** hook or payoff line. A line that sums the reel up.
**Trigger phrases:** "build a magazine cover behind me", "make this line a full cover with a masthead and a barcode".

## Footage it needs, and where it fails
- Top of the head at about y 360 or lower. Declines when there is no room for the masthead above the head.
- A cut after the line, with about 0.4 s of the next shot in the slot (`fx_new.py` asks for exactly one cut in the span).
- About 1.8 s of the line before the cut. A still or slowly drifting camera; the page is fixed to the screen.
- A clean cutout: the head and raised hands pass in front of the page.
- The sticker needs about 120 px of wall beside the head and is left out without it. It goes on the side with more wall, and the barcode goes on the other.

## Adapting to the footage
The masthead's baseline sits 48 px below the top of the head and its size comes from the word (fits the width, capped by the room above the head). Everything else hangs from those numbers and the safe zone. A long word is smaller. No coverlines means the masthead may sit higher up.

## Slot inputs
`assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json` (the cut frame), the reel's `layout.json`. No extra packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `MASTHEAD` | the big word, capitals, 4 to 8 letters | a word of the line, or the buyer's own title |
| `TOP_LINE` | the small line above the masthead | issue and date style, in the reel's language |
| `LEFT`, `RIGHT` | (small label, [one or two lines]) | the speaker's own words. `('', [])` = none |
| `TICKET` | number line under the barcode | `''` = no barcode. The bars are made up, never a real code |
| `STICKER` | (small top word, script word, small bottom word) | `('', '', '')` = no sticker |
| `AT_START`, `AT_BARCODE`, `AT_LEFT`, `AT_RIGHT`, `AT_STICKER` | when each part lands | a word of the line, a slot second, or `None` for the default rhythm |
| `BOTTOM`, `STICKER_SIDE` | frame edge and sticker side | `None` measures them |
| `SOUND` | the sticker's tap | 0.30, 0 = silent |

STYLE block: masthead face and `mast_blend`, small type, coverline type, script, and colours. The default is cream paper, gold rules and an olive sticker.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
In a reel: `fx_add.py` keeps the reel's captions on; they sit over the chest as usual.

## What to look at in the final frames
- The letters sit behind the head and read over the wall. A very pale wall makes the difference blend go dark: set `mast_blend` to `normal` and pick a dark `ink`.
- Nothing of the page in the red area of a SAFE=1 snapshot.
- The blur peaks on the cut and clears on the next shot with no page left.
- No real magazine's name or look-alike logo.
