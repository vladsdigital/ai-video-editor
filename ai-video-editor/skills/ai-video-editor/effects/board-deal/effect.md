# board-deal

**What it does:** cream cards made from real shots of this reel, each with the line that shot says under it, deal out one by one onto a 4 x 2 board behind the speaker, spinning in edge-on from beside the head. They gather into a deck beside the head, the top card flips over to a note page, and the note underlines itself. About 5.5 s.
**Job:** proof. A line about the plan, the storyboard, what is behind the work.
**Trigger phrases:** "deal my storyboard out behind me", "storyboard cards", "show the shots as cards".

## Footage it needs, and where it fails
- One continuous shot of about 5.5 s or more with the clean cutout, inside a reel project with 4 shots or more (`segments.json`), or `CARDS` typed in.
- Declines with under about 300 px of wall beside the head, without a cutout, and without `NOTE_TITLE`.

## Adapting to the footage
- The deck takes the side with more wall and its size from the room there. Cards behind the head are hidden by the speaker on purpose: the speaker stays in front through the cutout.

## Slot inputs
`assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, the reel's `layout.json`, `segments.json`. `build.py` pulls the frames into `assets/board/`.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `CARDS` | (reel frame, line under the card), at most 8 | the reel's own shots and lines |
| `NOTE_TITLE` | the note's title, the speaker's words | required |
| `NOTE_LINES` | the note's text; `*` at the start = underlined | none |
| `NOTE_ROWS` | up to 2 (label, value) rows, true facts only | none |
| `NOTE_TAG` | the band on the note | the card number |
| `NOTE_PILL` | short label in an outlined pill at the foot | none |
| `T_IN`, `T_GATHER`, `T_FLIP`, `T_OUT` | the beats | worked out from the deal; out 0.3 s before the end |
| `DEAL`, `SIDE` | spacing of the cards, side of the deck | 0.3 s; the side with more wall |

STYLE block: `paper`, `ink`, `dim`, `band`, `band_ink`, `mark`, `serif`, `serif_title`, `mono`.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The cutout edge against the cards behind the head and hands.
- Each card's line is what that shot says; every word of the note is the speaker's own, every number true.
- The deck stays off the face. First and last frames are the plain shot.
