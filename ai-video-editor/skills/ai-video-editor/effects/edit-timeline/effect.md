# edit-timeline

**What it does:** a dark editing panel opens above the head from a thin line and builds this reel's own timeline layer by layer: real shots with real frames and cut lengths, the real voice waveform, a block for every spoken word. A playhead tears across, the time code rolls to the reel's real length, then the panel flattens to a line, flipping light for two frames, and is gone.
**Job:** explain. A line about how the video was made.
**Trigger phrases:** "build this reel's timeline above my head", "show the edit on screen".

## Footage it needs, and where it fails
- About 250 px between the safe zone top (y 222) and the top of the head. Declines without it.
- A reel project: `segments.json`, `words.json`, `assets/aroll.mp4`. Declines on a loose clip, because there is no edit to show.
- Any camera, any number of cuts: it is an overlay.

## Where the rows come from
| Row | What it shows | Real? |
|---|---|---|
| V1 | one clip per shot, real frames | real cut lengths |
| A1 | the reel's voice | real waveform |
| T1 | one block per spoken word | real word times |
| V2 | one block per spoken phrase (split on punctuation) | real times, the `fxNN` labels are row numbers |
| V3 | effect slots from `plan.json`, else the words holding a number, or `MOMENTS` | real times |
| A2 | the voice's smoothed level, in two parts around the middle shot | a stand-in: it is not a music track. The reel's music is not read |
| A3 | a tick on every word start | real times, not real sound effects |

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage for the snapshots. Standard library and ffmpeg only. build.py writes `assets/tl_strip.jpg`.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `TITLE` | the word in the panel's corner | in the reel's language |
| `T_IN`, `T_OUT` | when it opens and when it starts flattening | a word or a slot second; `None` = 0.1 s, and 1.37 s later |
| `MOMENTS` | reel seconds of the gold blocks | `None` reads them from the plan or the words |
| `SOUND` | a soft whoosh in and out | 0 |

STYLE block: title and mono type, and every row's colour.
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

## What to look at in the final frames
- The panel stops above the head and inside the safe zone.
- Short reel, few cuts: the clips get wide, which is correct.
- No real editing app's logo or layout: plain rows only.
