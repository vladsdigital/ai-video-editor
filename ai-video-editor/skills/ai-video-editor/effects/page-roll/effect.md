# page-roll

**What it does:** a dark page panel slides up and the picture drops under it, so the face stays in view. The page scrolls like a screen recording through rows of the reel's real frames and lines, flicks to one row, zooms in on it and dims everything else, and its lines light up one by one as the speaker names them. Then it drops away and the picture comes back.
**Job:** explain. A line that lists things.
**Trigger phrases:** "scroll a page above me", "light up these lines as I name them".

## Footage it needs, and where it fails
- One continuous shot of about 4 s or more. The first named word about 1.6 s after the start, or the scroll gets cut short (build.py says so).
- A face that fits under the panel: declines when less than 480 px of panel is left, or when the face would leave the frame.
- The top 220 px of the picture stay still while the rest drops. A wall or ceiling is invisible; something moving up there would show a seam.
- The panel crosses the face for about 3 frames on the way up and down, then rests clear of it.

## Slot inputs
`assets/aroll.mp4`, `words.json`, `clip.json`, and from the reel project `words.json`, `segments.json`, `assets/aroll.mp4`, `layout.json`. build.py writes `assets/pr_*.jpg`. Standard library and ffmpeg only. The rows are the reel's own: each row is a spoken phrase, with its real times, real frames and real words.

**A buyer's page:** one long picture in the slot's `page/` folder (`fx_new.py --buyer-files <folder>`). It replaces the built page. Limit: it scrolls but does not zoom, and `LIT` does nothing on it.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `BAR_LEFT` | text on the cream bar | in the reel's language, no real product's name |
| `TITLE` | the page's italic title | a word or two from the reel |
| `LIT` | (word that lights it, small label, the line), 1 to 4 | the speaker's own words |
| `T_IN`, `T_OUT` | when it comes up and goes down | a word or slot second; `None` = 0.1 s, and 0.5 s after the last line |
| `PAGE_FILE` | a named picture in `page/` | `None` = the first one there |
| `PANEL_BOTTOM` | lower edge of the panel | `None` measures it from the face |
| `SOUND` | soft whoosh up and down | 0 |

STYLE block: serif, sans and mono type, page, bar and gold colours.
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
Last step in a reel: `fx_add.py "<project>" "<slot>" --caption-y <the value build.py prints>`.

## What to look at in the final frames
- At rest, the panel ends above the hairline and the face is clear.
- Lit text stays readable at the zoom and the row's words are correct.
- No real app's name or logo on the bar.
