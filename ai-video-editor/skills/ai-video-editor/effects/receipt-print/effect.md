# receipt-print (Receipt Print)

**What it does:** a thin forest-green printer bar sits above the head and prints what the speaker says as a cream paper receipt in mono type: a header, the sentence line by line in step with the words, a total line. Then the paper jerks, tears off and is gone out of the top of the frame in a quarter of a second, and the bar leaves a moment later.
**Job:** explain. One sentence the speaker tells an AI or a person to do, or a short "here is all it took" line.
**Trigger phrases:** "print what I say as a receipt", "receipt printer above my head", "the instruction comes out on a receipt".

## Footage it needs, and where it fails
- A spoken sentence of up to about 70 characters.
- Room above the head: about 250 px between the safe zone (y 220) and the head. Wide and medium shots. A tight selfie stops with one line saying how much room there is.
- Any camera: the receipt is fixed to the screen, placed from `layout.json`.

## Adapting to the footage
- The bar sits just above the head and follows the head's x (kept inside the safe zone). The whole receipt scales as one piece to fit the room above the head (full size is 525 px wide, three lines about 370 px tall), so its proportions never change. Under 58% of full size it declines.
- The reel's captions stay on, on the chest, and the receipt repeats the words from above the head.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots.
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. No cutout, no extra packages. Make the slot run about 1 s past the end of the sentence.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `TEXT` | the sentence that prints | required, the speaker's own words |
| `HEADER`, `NUMBER`, `TO` | header rows (the time beside `TO` is filled in from the reel) | the reel's language; never a real product's name unless the buyer asks |
| `TOTAL_LABEL`, `TOTAL_VALUE` | the total line | "TOTAL", "1 SENTENCE" in the reel's language |
| `T_START`, `T_DONE` | first word, total line | `None` = from `words.json` |
| `HOLD` | how long the finished receipt stays | .4 s |
| `Y`, `SCALE` | top of the bar, size against full size | `None`, `None` (from the room above the head) |
| `SOUND` | feed, tear and whoosh volume | .22, 0 = silent |

STYLE block: `font`, `weight`, `head_weight`, `char_width` (mono letter width, used for wrapping), `case`, `paper`, `paper_ink`, `paper_dim`, `bar`, `bar_edge`, `dots`, `led`. Mono type is the look of a receipt, so it stays mono unless the buyer asks otherwise; the colours can take the reel's.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: TEXT and the header and total words in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the receipt size, its timing and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
`fx_new.py` prints these commands with the real paths filled in and saves them as `RUN.txt` in the slot. Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Each line comes out as its first word is said, and the total as the sentence ends.
- The bar sits clear of the head; the paper stays inside the safe zone until it tears off (only the flight crosses the top edge).
- Letters with marks (č ć š ž đ) all draw in the mono face. Plain paper and bar, no real product's name or logo.
