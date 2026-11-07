# script-page

**What it does:** cream paper rises over the shot in five frames and the reel becomes a screenplay page in typewriter type, built from the speaker's own lines: the end of the line before, a transition, a scene heading, the name, the direction, this line, the next heading and the next line dimmed. The page drifts up slowly and a tan marker runs over each word exactly as it is said.
**Job:** a line that talks about a plan, a script or a process; a change of texture in the middle of a reel.
**Trigger phrases:** "turn this line into a screenplay page", "show it as a movie script", "highlight my words on a script".

## Footage it needs, and where it fails
- Any footage: the page covers the frame. Good word timings, because the marker follows them. One line of the reel, 2 to 6 s.
- Stops when `NAME` is empty, when the slot has no words, or when the line is too long for the safe zone at this size.

## Adapting to the footage
- Start the slot in the middle of a line and the words already said before it stand dimmed above the marker. Inside a reel the lines around it come from the reel's words and cuts; on a loose clip the page holds only the slot's words.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the page is opaque, `hf render` writes `renders/<slot>.webm`. `words.json`, `clip.json`, the reel's `words.json` and `segments.json`. No cutout. Type files in `fonts/` (Courier Prime, OFL, with č ć š ž đ, no Cyrillic: for a Cyrillic reel set `font` to a shipped face).

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `NAME` | name over the dialogue | required, ask the buyer or use the name they give |
| `PAREN`, `SCENE`, `SCENE_NEXT`, `CUT_LABEL` | direction, scene headings, transition | write them in the reel's language |
| `T_IN`, `T_OUT` | when it rises and leaves | `None` = 0.1 s before the first word / after the last word, or stays when the slot ends on a cut |
| `SIZE`, `COLUMN`, `DRIFT` | type size, letters a line, rise speed | 41, 25, 16 |
| `SOUND` | soft whoosh on the way in | 0 (silent by default) |

STYLE block: `font`, `font_file`, `bold_file`, `paper`, `said`, `slug`, `ink`, `mark`.
**Switches:** `SAFE=1`, `PREVIEW=1`, `SFX=0`.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: NAME and the page labels in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the times and the snapshot list
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
In a reel: `fx_add.py` hides the reel's captions only while the page is up (`work/reel_captions.json`).

## What to look at in the final frames
- The marker runs in step with the voice, bridging the spaces between words; no jump where a line wraps.
- The current lines stay inside the safe zone. č ć š ž đ are in the typewriter face.
