# note-thread (Note Thread)

**What it does:** at the top of the frame a small forest-green card fades in with two stills of the clip and a quoted line, and a round name badge pops on its edge. A cream card rises over it, a note types itself out under a name, the time stamp lands, and the card grows to let a reply line slide in. Then it all fades.
**Job:** explain / proof. A line about asking for a change or a follow-up and getting an answer.
**Trigger phrases:** "show a note and a reply at the top", "a comment typing out with a reply under it", "a comment thread above my head".

## Footage it needs, and where it fails
- A name, a note and a reply of up to about 110 characters each (two lines).
- Room above the head: about 200 px between the safe zone (y 220) and the head. With less, the cards sit on the chest under the chin instead. No room there either: it stops with one line saying so.
- Any camera: the cards are fixed to the screen, placed from `layout.json`.

## Adapting to the footage
- The cards scale as one piece to fit above the head (cream card 1000 px wide at full size), centred in the frame.
- The two stills on the green card come from the slot's own clip, cut at build time. Nothing ships with the pack.

## Slot inputs
An OVERLAY effect (`"layer": "overlay"`): the final build is transparent graphics, `hf render` writes `renders/<slot>.webm`, and the reel lays it over its own footage. `SAFE=1` builds show the footage under it for the snapshots.
`assets/aroll.mp4`, `words.json`, `clip.json`, the reel's `layout.json`. Optional `avatars/`. No cutout, no extra packages.

## CLIP block (top of build.py)
| Field | What it is | How to get it |
|---|---|---|
| `NAME`, `NOTE` | who writes, what types out | required, the buyer's words |
| `REPLY_NAME`, `REPLY` | who answers, the reply line | required. Never a real product's name unless the buyer asks |
| `QUOTE`, `STAMP` | line on the green card, word beside the name | `''` = `NOTE`; `'now'` in the reel's language |
| `AVATAR`, `REPLY_AVATAR` | badge pictures in `avatars/` | `None` = first letter of the name |
| `T_IN`, `T_TYPE`, `T_REPLY`, `T_OUT` | timing | a word or seconds, `None` = worked out |
| `TYPE_RATE` | seconds per letter | .024 |
| `Y`, `SCALE` | bottom of the grown card, size | `None`, `None` |
| `SOUND` | keys and card volume | .3, 0 = silent |

STYLE block: `font`, `weight`, `name_weight`, `quote_font`, `quote_italic`, `mono_font`, `card`, `ink`, `dim`, `back`, `back_ink`, `badge`, `badge_ink`, `reply_badge`, `reply_ink`.
**Switches:** `SAFE=1`, `SFX=0`, `CAPTIONS=0` accepted and ignored.

## Run order (PY and SK as in SKILL.md, <slot> = the slot folder; no cd, no shell variables)
```
# edit: NAME, NOTE, REPLY_NAME and REPLY in the CLIP block
PY "SK/scripts/fx_run.py" "<slot>" build.py SAFE=1      # prints the card size, the timing and the snapshot times
PY "SK/scripts/fx_run.py" "<slot>" hf lint
PY "SK/scripts/fx_run.py" "<slot>" hf snapshot --at <times build.py printed>
PY "SK/scripts/fx_run.py" "<slot>" build.py      # guide off
PY "SK/scripts/fx_run.py" "<slot>" hf render
PY "SK/scripts/fx_run.py" "<slot>" check.py      # frame count, work/check/sheet.jpg, phone copy
```
`fx_new.py` prints these commands with the real paths filled in and saves them as `RUN.txt` in the slot. Last step in a reel: `PY "SK/scripts/fx_add.py" "<project>" "<slot>"`.

## What to look at in the final frames
- The grown card stays clear of the head and inside the safe zone.
- The caret follows the last typed letter and leaves when the note is done.
- Plain cards and lettered badges: no real product's name or interface.
