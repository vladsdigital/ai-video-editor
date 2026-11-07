# hook-stack

**What it does:** the whole opening. The first line lands letter by letter in a big serif behind the head, the room flips to a solid forest green backdrop behind the cutout on the second line, heavy sans lines push through a two-line stack word by word with a small running timecode, then a serif italic line lands with a coloured last word, the speaker jumps a little closer on it, and the room cuts back.
**Job:** hook. The reel's opening line, about 3 to 6 s.
**Trigger phrases:** "give my opening the serif and green backdrop stack", "kinetic opening", "flip the background to green on the hook".

## Footage it needs, and where it fails
- One continuous shot, a still or nearly still camera, room above the head. Wide or medium.
- The clean cutout. Anything it loses vanishes against the backdrop: LOOK at hands and hair.
- Declines when the head starts too high for the lines, or when a line's first word is not said in the slot.

## Adapting to the footage
- Every size is measured: serif and stack fit the width and stop at the top of the head, the italic line rests on the head after the jump. Long words get smaller type.
- A speaker at a desk: without `KEEP` the desk is gone and the arms end in the backdrop. Put the desk in `KEEP` and whatever is in front of the speaker (laptop) in `KEEP_FRONT`, read in full-size px off one frame. Still camera only.

## Slot inputs
`assets/aroll.mp4`, `assets/subject.webm`, `words.json`, `clip.json`, the reel's `layout.json`. Not an overlay: it renders the slot's full picture to `renders/<slot>.mp4`.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `SERIF` | two lines in capitals; the second flips the room | the speaker's first words |
| `STACK` | 1 to 3 (top, bottom) pairs in capitals | the next words, in order |
| `ITALIC` | (first words, last word in the accent colour) | the line's landing |
| `TIMES` | seconds by line text, to overrule the lookup | `{}` = when the line's first word is said |
| `KEEP`, `KEEP_FRONT` | real picture kept behind / in front of the speaker | `[]`, or (x, y) points closed along the bottom |
| `T_OUT` | when the room cuts back | `None` = slot end |
| `PUNCH` | how much closer on the coloured word | 1.12, 1 = off |
| `PLATE_Y`, `SOUND` | small caption plate, low hit under the italic line | 1360, 0.34 |

STYLE block: fonts and font files, `backdrop`, `ink`, `accent`, `dim`. The reel's style wins.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` (no small plate: the reel's captions run. The default in a reel).

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: SERIF, STACK, ITALIC in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints sizes, times and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- Letters behind the head, never on the face. Each word still reads with the head in front of it.
- Lines stay out of the top red area, carons and accents too.
- The backdrop flip and the cut back are hard cuts on a word.
- Cutout edge against the flat green, full size, on hair and fingers.
