# counter-dive

**What it does:** a deep green plaque stands up above the head with a rolling length counter that runs from the raw footage's real length down to the finished reel's real length. The label swaps, the plaque folds away, the whole live frame shrinks into a smaller copy of itself in a thin cream border, again and again inside itself, then the picture pushes in, tips, blurs and comes out in the next shot.
**Job:** payoff. A line about how little time it took, or about how long the video is.
**Trigger phrases:** "count my raw length down to this reel", "shrink the frame into itself".

## Footage it needs, and where it fails
- About 190 px between the safe zone top and the top of the head for the plaque, else 190 px on the chest (the plaque moves there and build.py prints the --caption-y value that puts the captions under it). Declines with neither.
- Room for the small frame: above the head when that gives a third of the picture's height, else in the wall on the side with more room. Declines under 20% of the frame's size.
- A cut after the line, with about 0.4 s of the next shot in the slot. About 2.8 s before the cut; declines under 2.1 s.
- Real lengths: reads the reel's source clips and `segments.json`. Declines rather than making them up.

## Slot inputs
`assets/aroll.mp4`, `clip.json` (the cut frame), `words.json`, the reel's `layout.json`, `sources.json`, `segments.json`. No cutout: the small frames sit on top of the picture. Standard library and ffprobe only.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `RAW_LABEL`, `FINAL_LABEL` | the small label before and after the swap | in the reel's language |
| `T_IN` | when the plaque opens | a word or slot second; `None` = 85 frames before the exit |
| `RAW_SECONDS`, `FINAL_SECONDS` | the two lengths | `None` measures them |
| `PLACE` | where the small frame goes | `None` measures it |
| `LEVELS` | copies inside each other | 4 |
| `SOUND` | a faint bell when it lands | 0.08, 0 = silent |

STYLE block: digit and label type, plaque, cell, digit, label and border colours. Raw lengths from 10 minutes up get a fourth digit, so the plaque is wider.
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
In a reel: the reel's captions stay on. They are drawn over the slot, so the blur does not touch them.

## What to look at in the final frames
- The digits land square in their cells on the real numbers.
- The small frame stays clear of the face.
- The dive: the blur peaks on the cut and clears in the next shot.
