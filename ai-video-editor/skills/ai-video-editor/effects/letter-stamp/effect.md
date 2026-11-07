# letter-stamp

**What it does:** one huge serif word lands letter by letter behind the speaker's head, across the top of the frame. `MODE = 'stamp'`: each letter fades up a touch too big and settles in four frames, two frames after the one before it. `MODE = 'drop'`: each letter hits the line squashed, springs past its height and settles. Optional: a thin rule through the tops of the letters (`RULE`), a first line stamped above the word (`LEAD`), the whole room cutting to one flat colour on the word's first letter (`GROUND`).
**Job:** hook or emphasis, on one word that matters.
**Trigger phrases:** "stamp the word X letter by letter behind my head", "drop the letters of X behind me".

## Footage it needs, and where it fails
- One word the speaker says, best 4 to 7 letters. One continuous shot, one person, clean cutout.
- Room above the head: the letters must be at least 110 px tall inside the safe zone, or it declines.
- Where the room is really bright behind the word (a ceiling, a white wall) the word turns deep green there. It is one picture of the room, so on a camera that travels set `TWO_TONE = False`.

## Adapting to the footage
- The head is read from the cutout on every 14th or so of the slot's frames. The word is as wide as `WIDTH` allows, smaller when the height above the head runs out.
- `GROUND`: when the cutout stops above the frame edge (a desk, a laptop in front), the real picture fades back in under the body so hands never float on the flat colour.

## Slot inputs
`assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`. numpy and Pillow from the skill's own Python.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `WORD` | the word, required | |
| `MODE` | `'stamp'` or `'drop'` | `'stamp'` |
| `RULE` | thin rule through the letter tops (stamp only) | off |
| `LEAD`, `T_LEAD` | first line above the word, and when it starts | none; when its first word is said |
| `GROUND` | flat room colour from the word's first letter | none. `'#163127'` deep forest green |
| `T_IN`, `T_OUT` | first letter; word gone | when said; the cut at the slot end, else 1.4 s after landing |
| `STAGGER` | frames between letters | 2 (3 reads slower and heavier) |
| `WIDTH`, `TUCK` | word width, share of letter height behind the head | 0.90; 0.14 stamp, 0.26 drop |
| `TWO_TONE`, `LIGHT` | dark word over bright room, and how bright is bright | on, 172 |
| `SOUND` | tick per letter | 0 (the look is silent) |

STYLE block: `font`, `weight`, `italic`, `case`, `tracking`, `ink`, `ink_dark`. The reel's look wins.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder)
```
# edit: WORD and MODE in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`. The reel's captions keep running under the chin.

## What to look at in the final frames
- Letters inside the safe zone, behind the head and any raised hand, clean cutout edge where they meet the hair.
- Soft projected light on the wall is not bright enough to flip the word: only a hard bright surface should. Patchy dark letters mean `LIGHT` is too low.
