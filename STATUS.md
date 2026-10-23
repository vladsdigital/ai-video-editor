# Status: Reel Lab
Ažurirano: 23.10.2026.
Faza: razvoj

## Gde smo stali
- Reel Lab 1.0 radi od početka do kraja na Vladimirovom Macu: setup, preuzimanja, ingest, rez, transkript, glava u kadru, titlovi, render (14 s rils za 19 s), provere, telefonska kopija, glasnija kopija.
- Transkripcija: `scripts/speech.py`. Soniox (glavni; ključ iz ~/.config/soniox/api_key ili `speech.py key --clipboard`) i offline Whisper (small + large-v3-turbo za sr/hr/bs). Na probi: Soniox 0 grešaka, Whisper 2.
- Jezik: `engine/lang.py` (sr/hr/bs/en: slabe reči, poštapalice, poziv na akciju, brojevi), ćirilica kao opcija (`speech.py script cyrillic`), sa automatskim zamenskim fontovima za ćirilična slova.
- Fontovi: 66 postojećih ponovo napravljeno sa č ć š ž đ (+ ćirilica gde postoji), 32 nova fonta (Montserrat, Unbounded, Oswald, Lora, Pacifico...).
- Prevedeno na srpski: SKILL.md (poruke kupcu), reference, poruke skripti, Picker, karuseli, README, manifesti (verzija 1.0.0).
- Zvuk: provera u LUFS, `check_cuts.py --loud` pravi kopiju na -14 LUFS.

## Sledeći korak
1. Vladimir snima materijal sa spiska (preview klipovi za 20 stilova titlova, 9 stilova, 46 efekata; sada prikazuju originalnog autora na engleskom).
2. Od tog materijala renderovati nove preview klipove i postere za Picker.
3. GitHub repo `vladsdigital/reel-lab` (javan) + push, pa test instalacije iz Claude aplikacije.
4. Ugrađeni stil "Vladsdigital" (Archivo Black + Inter, boje iz reel-animacije).

## Šta fali od Vladimira
- Snimci i materijal (spisak u poslednjoj poruci u chatu).
- Da li repo sme da bude javan.
- Pismena dozvola autora.

## Otvorena pitanja / rizici
- Efekti ne prebacuju SVOJ tekst na ćirilicu (titlovi da); ui-world limit 15 znakova nije proširen za srpski.
- 7 fontova nema sva naša slova upstream (Elsie Swash Caps, Mrs Saint Delafield, Permanent Marker, Covered By Your Grace, Nothing You Could Do, Nanum Pen Script, La Belle Aurore delimično).
- RVM model je GPL-3.0; Pixabay zvuci se ne smeju deliti; proveriti licencu HyperFrames-a.
- Svaki slot efekta sada nosi 4,4 MB fontova (kopija engine/fonts).
