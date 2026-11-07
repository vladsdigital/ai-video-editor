# marked-sheet

**What it does:** a cream paper sheet with two film strips of real frames from this reel drops in from the top, tilted, and settles above the speaker. The frames develop from black one after the other, a red pencil circles and crosses some of them and writes a short word above them, then the sheet flies back off the top. About 2.7 s.
**Job:** explain. A line about choosing, weak takes, a problem, what gets cut.
**Trigger phrases:** "mark up my takes on a film strip", "contact sheet with red pencil", "circle my takes in red".

## Footage it needs, and where it fails
- One continuous shot of about 3 s, medium or wide. The shot slides down while the sheet is up (the wall above it is a blurred mirror, nearly all under the paper), so the sheet stays off the face.
- Declines when the chin would land under y 1500 after the slide (a tight close-up), and on a slot too short for the pencil.

## Adapting to the footage
- The slide is worked out from layout.json. Frames come from across the whole reel with their real times; the foot line carries the real file name, length and size of the raw clip.

## Slot inputs
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`, `segments.json` and `sources.json` for the foot line. No cutout, no extra packages.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `MARKS` | pencil marks in order: (cell 0 to 11, 'circle' or 'cross', word, time). A word only above the top strip | two circles, three crosses, no words |
| `TAG` | word before the length in the foot line | none |
| `FILE_NAME` | name in the foot line | the real raw clip |
| `T_IN`, `T_DEVELOP`, `T_MARKS`, `T_OUT` | drop, first frame develops, first mark, fly off | from the first word; 0.55 s later; 0.45 s after developing; 0.3 s before the slot ends |
| `DROP` | length of the drop | 0.3 s |

STYLE block: `paper`, `film`, `hole`, `hand` (the pencil), `hand_font`, `hand_italic`, `hand_size`, `tc`, `foot`, `mono`. The words in `MARKS` are the speaker's own.
**Switches:** `SAFE=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the slide and the --caption-y value
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py
```
Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>" --caption-y <the printed value>`.

## What to look at in the final frames
- The paper is off the eyes and the nose; only hair may lie under its lower edge.
- First and last frames are the plain shot, with no jump where the slide starts and ends.
- The strips hold real frames, the words are the speaker's own, the foot line is true.
