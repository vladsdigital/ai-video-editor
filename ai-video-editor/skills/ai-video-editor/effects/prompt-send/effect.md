# prompt-send

**What it does:** a cream bar opens from a dot at the top of the frame, what the speaker tells the AI types itself in as it is said, the send button presses and spins while the words dim, the result rolls in over them in a serif italic with a check and a small ping, and the bar collapses back into a dot and is gone.
**Job:** explain. Any line where the speaker tells an AI what to do and says what comes back.
**Trigger phrases:** "show my prompt being typed and sent", "prompt bar at the top with the result", "send button then the result".

## Footage it needs, and where it fails
- A spoken instruction of up to about 60 characters and a short result said right after. Any camera.
- Room above the head for a 150 px bar. Declines on a tight close-up, and when the slot ends less than about 0.5 s after the result word.

## Adapting to the footage
- Each word of `TEXT` types while it is said; a word not found in the slot types right after the one before. The bar moves up when the head is high. Long text gets a smaller size.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): transparent graphics, `hf render` writes `renders/<slot>.webm`, the reel lays it over its own footage. `assets/aroll.mp4` only for SAFE snapshots, `words.json`, `clip.json`, `layout.json`.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `TEXT` | what types in | the speaker's own words, required |
| `RESULT` | what rolls in | short, required; lands when its first word is said |
| `LABELS` | small label while typing, waiting, done | in the reel's language |
| `TIMES` | seconds for: open, send, result, close | `{}` = from the words |
| `TOP`, `SOUND` | place, ping when the result lands | `None`, 0.3 |

STYLE block: `font`, `weight`, `result_font`, `label_font` and the colours. The reel's style wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: TEXT, RESULT, LABELS in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the times, the place and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Typing keeps up with the speech, and the caret stays on the last letter.
- The result is up long enough to read before the bar collapses. If not, end the slot later.
- Clear of the face and the red area. No real product's logo or interface: a plain bar.
