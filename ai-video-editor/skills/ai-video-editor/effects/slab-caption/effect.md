# slab-caption

**What it does:** the key word springs up from below into a big slab at the top of the frame, a second word in serif italic opens under it from the right, small tags pop in one by one under the chin, and the payoff lands on a tilted paper strip. At the end the pieces fold shut one after the other.
**Job:** turn one spoken line into a headline. Hook or key line.
**Trigger phrases:** "big slab caption at the top", "put the word X in a slab and land the payoff under my chin".

## Footage it needs, and where it fails
- One line: a key word, optionally a second word, a few words, a short payoff.
- Room above the head (110 px or more in the safe zone) and under the chin (about 200 px). Without them it declines. The slab shrinks with the room above the head: the full size needs about 410 px.

## Slot inputs
An OVERLAY effect: the final build is transparent, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage, so the span may cross a cut. `words.json`, `clip.json`, the reel's `layout.json`. Pillow from the skill's own Python, to measure the words.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `SLAB`, `SECOND` | the key word and the word under it | required; `''` = no second box |
| `TAGS` | the small words under the chin | `[]` |
| `PAYOFF` | the last words, up to about 12 letters | required |
| `TIMES` | by hand, any of `slab`, `second`, `tags`, `payoff` | when each is said |
| `T_OUT` | the last piece has folded shut | 0.95 s after the payoff |
| `TILT` | tilt of the payoff strip | -3 degrees |
| `SOUND` | a soft tick on each piece | 0 (the look is silent) |

STYLE block: `font`, `weight`, `tag_weight`, `tracking`, `serif_font`, `serif_weight`, `serif_italic`, `case`, `serif_case`, `card`, `ink`, `accent`, `paper`, `paper_ink`. The reel's look wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder)
```
# edit: SLAB, SECOND, TAGS, PAYOFF in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The stack clears the head, the tags clear the beard, the strip's low corner stays above the red area.
- Every word said in the window has a place on screen.
