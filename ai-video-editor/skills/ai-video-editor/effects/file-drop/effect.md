# file-drop

**What it does:** a forest green drop-zone card with a dashed line appears above the head. A file card with the raw clip's real name and length falls in from the top, tilted, and lands in it. The card and the zone go glassy and open into a small player of the real raw clip, sped up, with its length on a pill. Red rubber stamps slam on, then it fades. About 2.5 to 3 s.
**Job:** explain. A line about handing over a raw clip.
**Trigger phrases:** "show my raw file dropping in", "drop the clip in", "stamp my takes".

## Footage it needs, and where it fails
- Any camera. About 240 px of wall above the head (y 228 down to the top of the head); declines with less. Declines under about 2.3 s.

## Adapting to the footage
- The zone's height comes from the room above the head. The player opens on the side with more wall beside the head (it would cover the face if it sat in the middle on a medium shot); with no room there it stays small above the head.
- The file name, length, size and picture are the real raw clip's, from the reel's `sources.json` and `segments.json`, or `RAW_FILE`.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots. `build.py` cuts `assets/raw.mp4` and `assets/raw_thumb.jpg` from the raw clip.

## CLIP block (top of build.py)
| Field | What it is | Default |
|---|---|---|
| `DROP_TEXT`, `PILL_TEXT`, `STAMPS` | words, in the buyer's language | English placeholders: replace them |
| `RAW_FILE`, `FILE_NAME` | the clip and its name | the raw clip of this slot, its real name |
| `SPEED` | the player's speed | 2.3 |
| `T_IN`, `T_FILE`, `T_OPEN`, `T_STAMP`, `T_OUT` | the beats | 0.1 s, then +0.55, +0.5, +0.45; fade 0.2 s before the end |

STYLE block: `zone`, `dash`, `zone_font`, `file_bg`, `file_ink`, `file_dim`, `name_font`, `name_weight`, `mono`, `pill_bg`, `pill_ink`, `pill_num`, `stamp_bg`, `stamp_ink`.
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
- Nothing on the face. The zone's lower edge clears the head, the player sits on the wall beside it.
- The name, length and size are true. No real app's screen or logo.
- The stamp word fits inside the player's width (shorter word or smaller `STAMPS` when not).
