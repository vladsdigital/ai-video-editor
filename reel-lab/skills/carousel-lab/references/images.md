# Pictures the buyer does not have: generating them

Use this when a carousel needs photos and the buyer has none (no video frames, no pictures of their own).
`IG` = `PY "CS/scripts/imagegen.py"`. Never show the buyer STATUS lines, model ids or JSON: plain words only.

## 1. Which generator

In this order:
1. **An image tool you already have.** Look at your own tools for one that generates images (a connector or MCP
   tool: "generate_image", "create image", Nano Banana, GPT Image, Seedream, Flux, Ideogram, Canva and the like).
   If there is one, use it: no key needed. Save its result into the carousel's `assets/` (below).
2. **A key on this computer.** `IG check`:
   - `STATUS imagegen <provider> READY`: that one works. `STATUS imagegen default ...` is the one `make` uses.
   - More than one READY and the default says "not picked yet": ask the buyer ONCE ("Za slike imaš podešene i OpenAI i
     Google. Koji da koristim? OpenAI je oko 1 cent po fotki i daje najprirodnije slike.") and remember it:
     `IG default <provider>`. Never ask again unless they bring it up.
3. **None.** Offer to set one up, in a few lines:
   > "Da bih pravio fotke, treba mi ključ za slike. Preporučujem OpenAI: oko 1 do 2 centa po fotki, najprirodniji
   > rezultati. 1. Idi na platform.openai.com/api-keys i prijavi se. 2. Settings > Billing: dodaj 5 $ kredita.
   > 3. Klikni Create new secret key i kopiraj ga. Onda mi napiši 'kopirano' (nemoj da ga lepiš ovde)."

   Then `IG key set openai --clipboard` (reads what they copied; the key never appears in the chat or a command).
   It checks the key with a free call and saves it to the Studio's private key file.
   - If they paste the key into the chat anyway, send it on stdin, never as an argument:
     Mac/Linux `IG key set openai <<'EOF'` / the key / `EOF`; Windows PowerShell `'<key>' | & PY "CS/scripts/imagegen.py" key set openai`.
     Never repeat the key back, never write it anywhere else.
   - In a terminal of their own, `IG key set openai` asks for it with a hidden prompt.
   - Other choices if they prefer: Google (aistudio.google.com/apikey, then turn on billing: the free plan makes no
     pictures; about 3 to 5 cents a photo), fal.ai (fal.ai/dashboard/keys, add credit; Seedream 5 Lite, about
     3.5 cents a photo). Same `key set gemini` / `key set fal`.

Errors come back in plain words (`STATUS image FAILED (auth|credit|verify|refused|transient|other): ...`). Pass
them on simply. `verify` = OpenAI wants a one-time organization check on their site before its image models work.
`refused` = the generator's content rules: change the description, do not argue with it. Busy/timeouts are retried
once by the script.

## 2. Before spending

- One or two pictures: just make them (say roughly what they cost if it is their first time).
- More than 2: show the list first and wait for an OK:
  ```
  Slike koje bih napravio (ukupno oko 0,04 $, OpenAI):
    Slajd 1: sunčan sto pored prozora, kafa i otvorena sveska
    Slajd 4: ruke drže late u mirnom kafiću
    Slajd 7: miran ugao dnevne sobe sa foteljom za čitanje
  Da ih napravim?
  ```
  `IG cost --count 3` gives the estimate. Then a plan file and `IG batch plan.json --yes` (without `--yes` it only
  prints the count and total, never spends).
- Redo of one picture = one more picture's cost. Say so if they ask for many redos.

## 3. Making them

```
IG make "<prompt>" --out "<carousel folder>" --size 3:4 [--ref "<picture>"]     -> <carousel folder>/assets/gen-NN.png
IG batch "<carousel folder>/work/pictures.json" --yes
   [{"prompt": "...", "out": "../assets/gen-01.png", "size": "3:4"},
    {"prompt": "...", "out": "../assets/gen-02.png", "size": "3:4", "ref": "../assets/gen-01.png"}]
```
(`out` and `ref` in a plan are relative to the plan file.) `--size` = the carousel's size (3:4 default, 4:5, 1:1;
9:16 / 16:9 for other uses). `--dry-run` shows what would be sent, with no key and no cost.

LOOK at every picture before using it (open the file). Wrong hands, warped objects, text that slipped in, a face
that is not right: make that one again with a sharper prompt, or drop it.

Then use it like any photo in carousel.json:
`"image": {"src": "assets/gen-01.png", "fit": "bleed"}` (full slide behind the text, dimmed by the look),
`{"src": ..., "fit": "half", "side": "top", "share": 0.5}` (photo on one part, text on the other),
`{"src": ..., "fit": "frame"}` / `"cover"` (a picture in the middle). Render and check as usual.

## 4. Prompts that work for carousel pictures

Write the prompts to the generator in English (the models follow English best), even when the buyer and the slides
are in Serbian; show the buyer the list of pictures in their language. The slide sets every word. So, in every
prompt:
- **No text.** No words, letters, numbers, signs, logos, watermarks, labels on products, screens with writing.
  (The script adds a "no text" line by itself; still describe blank notebooks, plain mugs, unbranded things.)
- **Room for the headline.** Say where the calm space goes, matching where the look puts the headline:
  "plain wall / soft sky / empty tabletop in the top third" for most covers; "subject in the lower half". For
  `half`, keep the subject well inside the photo's half.
- **The look's mood.** Read the look's `look.json` "about". Horizon (dark, warm sun): low warm golden-hour or
  lamp light, deep shadows, warm amber tones. Paper (cream, earthy): soft diffused daylight, warm neutrals, linen,
  wood, matte. Poster (bold, bright): crisp light, strong contrast, clean saturated colour. Their own look: its
  colours as the palette ("muted sage and cream tones").
- **One set, one shoot.** Same light, palette, lens and time of day on every picture of a carousel: write one
  "style line" and end every prompt with it. For more consistency, make picture 1 first, then pass it as `--ref`
  for the rest ("same light and colours as the reference").
- **Real, not AI-looking.** "Editorial photo, natural light, 35mm or 50mm lens, shallow depth of field, natural
  skin texture, real-world imperfections, candid." Avoid: perfect symmetry, glossy plastic skin, glowing edges,
  "8k, ultra detailed, masterpiece". Prefer hands, backs, silhouettes and objects over full faces: fewer things
  can go wrong. Keep hands simple (holding one thing).
- **Shape.** Say "vertical photo" for 3:4 / 4:5 / 9:16.

Templates (fill the brackets, then the set's style line):
- **Desk / work:** "Vertical editorial photo of a tidy wooden desk by a window: an open blank notebook, a plain
  ceramic mug of coffee, a pen, a small plant. Soft morning daylight from the left. Calm plain wall in the top
  third. 35mm, shallow depth of field."
- **Café:** "Vertical photo, a plain latte with simple foam art on a small marble café table, a hand resting
  beside it, blurred café interior behind, warm window light. Empty soft-focus background in the top third."
- **Gym / pilates studio:** "Vertical photo of a bright minimal pilates studio, reformer machines in a row,
  pale wood floor, large windows, one person in neutral activewear seen from behind stretching. Clean white wall
  in the upper part. Natural light, candid."
- **Flat lay:** "Top-down vertical flat lay on [linen / travertine / warm paper]: [3 to 5 objects], arranged
  loosely with space between them, soft shadow from window light. Bare surface across the top third."
- **City walk:** "Vertical street photo, a person in a [camel coat] walking away from the camera on a quiet
  [European] street at golden hour, soft background blur. Open sky between the buildings in the top third."
- **Product on a plinth:** "Vertical studio photo of [plain unbranded product] on a [travertine / plaster]
  plinth, soft single light from the side, gentle shadow, seamless [colour] backdrop with lots of empty space
  above."
- **Cozy home:** "Vertical photo of a cozy living room corner: a reading chair with a knit throw, a side table
  with a plain mug and a closed book, warm lamp light at dusk, plants. Calm wall space in the top third."

## 5. Hard rules

1. Never generate a real person other than the buyer. The buyer only from their own photo (`--ref`), only when
   they ask for it. No celebrities, no "looks like <name>", no other creators.
2. Never fake proof: no screenshots of results, dashboards, bank or sales numbers, follower counts, DMs,
   testimonials, reviews, awards or "as seen on". A generated picture is mood, never evidence.
3. No brand logos, trademarks or recognisable branded products, no copied artwork or characters.
4. Nothing meant to deceive (fake news photos, fake events, a fake "me at" scene presented as real).
5. Keys: never printed, pasted into a command, written into carousel files or shown back to the buyer.
