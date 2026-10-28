# Status: AI Video Editor
Ažurirano: 27.10.2026.
Faza: razvoj

## Gde smo stali
- 27.10: svi preview klipovi u Pickeru zamenjeni Vladimirovim snimcima iz studija (Movies/Ai profit lab reels): 20 titlova + 9 stilova (klip 15-23-59, projekat ~/reel-edits/primeri-studio), 46 efekata (8 klipova, ~/reel-edits/efekti-studio), sa posterima (oči otvorene). Grana `primeri-vladimir`, nije spojena ni pushovana. Slabiji: inside-out (nema pravog b-rolla), clone, orbit, spatial-glass, vertigo.
- AI Video Editor 1.0 radi od početka do kraja na Vladimirovom Macu: setup, preuzimanja, ingest, rez, transkript, glava u kadru, titlovi, render (14 s rils za 19 s), provere, telefonska kopija, glasnija kopija.
- Transkripcija: `scripts/speech.py`. Soniox (glavni; ključ iz ~/.config/soniox/api_key ili `speech.py key --clipboard`) i offline Whisper (small + large-v3-turbo za sr/hr/bs). Na probi: Soniox 0 grešaka, Whisper 2.
- Jezik: `engine/lang.py` (sr/hr/bs/en: slabe reči, poštapalice, poziv na akciju, brojevi), ćirilica kao opcija (`speech.py script cyrillic`), sa automatskim zamenskim fontovima za ćirilična slova.
- Ukrasni fontovi bez naših slova: Permanent Marker, Covered By Your Grace i Nothing You Could Do dobili slova u samom fontu; Elsie Swash Caps, Mrs Saint Delafield i Nanum Pen Script dobijaju samo ta slova iz sličnog fonta (engine/fonts/standins.json).
- Fontovi: 66 postojećih ponovo napravljeno sa č ć š ž đ (+ ćirilica gde postoji), 32 nova fonta (Montserrat, Unbounded, Oswald, Lora, Pacifico...).
- Prevedeno na srpski: SKILL.md (poruke kupcu), reference, poruke skripti, Picker, karuseli, README, manifesti (verzija 1.0.0).
- Zvuk: provera u LUFS, `check_cuts.py --loud` pravi kopiju na -14 LUFS.

## Sledeći korak
1. Vladimir pregleda nove primere u Pickeru, pa spojiti granu `primeri-vladimir` u main.
2. Po želji: pravi b-roll za Inside Out i Green Screen, širi kadar za Clone.
3. Repo `vladsdigital/ai-video-editor` je napravljen kao PRIVATAN; javan tek kad preview klipovi budu zamenjeni, pa test instalacije iz Claude aplikacije.
4. Ugrađeni stil "Vladsdigital" (Archivo Black + Inter, boje iz reel-animacije).

## Šta fali od Vladimira
- Snimci i materijal (spisak u poslednjoj poruci u chatu).
- Pismena dozvola autora.

## Otvorena pitanja / rizici
- Efekti ne prebacuju SVOJ tekst na ćirilicu (titlovi da); ui-world limit 15 znakova nije proširen za srpski.
- RVM model je GPL-3.0; Pixabay zvuci se ne smeju deliti; proveriti licencu HyperFrames-a.
- Svaki slot efekta sada nosi 4,4 MB fontova (kopija engine/fonts).
