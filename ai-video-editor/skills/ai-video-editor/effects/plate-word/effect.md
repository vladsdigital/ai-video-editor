# plate-word

**What it does:** the words before the payoff stack up under the chin in small dark boxes, each bigger than the last, each new one popping in at the bottom and pushing the stack up. On the payoff word the picture cuts to a paper plate with that word cut out of it, slamming down from huge, and the live video plays through the letters.
**Job:** payoff. One line that ends on one word or number.
**Trigger phrases:** "stack my captions and cut to a plate with the word X", "giant word with my video inside the letters".

## Footage it needs, and where it fails
- A spoken line of 2 to 5 short words, then the payoff word. Any framing, any camera.
- The stack needs about 120 px under the chin inside the safe zone. No room: it declines, and `CAPTIONS=0` builds the plate alone.

## Slot inputs
An OVERLAY effect: the final build is transparent (also inside the letters), `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `assets/aroll.mp4` only for `SAFE=1` snapshots. `words.json`, `clip.json`, the reel's `layout.json`. Pillow from the skill's own Python, to measure the word.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `WORD` | the payoff word, required | |
| `STACK`, `MAX_BOXES` | the boxes as `[text, second]` rows | the words said before WORD, last 4 boxes |
| `LINES` | one or two lines | two from 4 letters up |
| `T_WORD`, `HOLD` | the cut to the plate, how long it stays | when said, 0.70 s |
| `WIDTH`, `STRETCH` | width of the widest line, letter height | 0.88; 1 on two lines, 1.3 on one |
| `SOUND` | a low hit on the plate | 0 (the look is silent) |

STYLE block: `font`, `weight`, `italic`, `word_case`, `stack_case`, `tracking`, `box`, `box_ink`, `paper`. The reel's look wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder)
```
# edit: WORD in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. The reel's captions are hidden from the first box to the end of the plate.

## What to look at in the final frames
- The stack's top stays under the chin; every spoken word has a box or a caption.
- The video reads through the letters: the face or a hand should cross them while the plate is up.
