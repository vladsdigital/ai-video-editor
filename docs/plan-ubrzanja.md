# Plan ubrzanja AI Video Editora

Napisano: 09.11.2026. Mereno na Macu M5 (24 GB) sa tvojim klipovima.

## Gde ide vreme danas

Merenje iz tvoja dva prava četa sa montažom (28.10):

| Montaža | Ukupno | Alati (skripte) | Claude razmišlja i piše | Čeka tebe | Koraka |
|---|---|---|---|---|---|
| Prvi rils, 2 efekta | 15 min | 7 min | 6 min | 2 min | 71 alat, 125 koraka |
| Rils + 3 trial verzije | 28 min | 10 min | 16 min | 2 min | 62 alata, 113 koraka |
| Ponovo, sa svim efektima | 34 min | 19 min | 15 min | 0 | 76 alata, 132 koraka |

Pola vremena odlazi na skripte, a pola na Claudea. Claude u jednoj montaži prođe 110 do 130 koraka, napiše 80 do 100 hiljada tokena koda i podešavanja (otprilike 60 hiljada reči) i pogleda 12 do 22 slike. Svaki korak traje nekoliko sekundi. Zato montaža deluje kao da „stoji”, iako nijedna komanda nije pukla.

Merenje pojedinačnih koraka na klipu „svi 7” (60 s):

| Korak | Danas | Napomena |
|---|---|---|
| Transkript (Soniox) | par sekundi | nije problem |
| Render celog rilsa | oko 1,5 min za 60 s (procena iz rendera efekta) | brz, ide na video čip |
| Render jednog efekta | 7 s | brz |
| Čisti izrez osobe | 0,5 s po frejmu | 1 min za efekat od 4 s; **15 min za ceo rils od 60 s** |
| Sam model izreza na procesoru | 0,30 s po frejmu | |
| Isti model na grafičkom čipu (CoreML) | 0,14 s po frejmu | 2x brže, ista slika (razlika 1%) |
| Na procesoru, pola rezolucije | 0,08 s po frejmu | 4x brže |

Čisti izrez osobe je jedini zaista spor alat. Kad stil traži izrez celog rilsa (Bold captions, Chalk Talk, Show and Tell), samo on traje 15 minuta. Kad rils ima 5 efekata, svaki pravi svoj izrez jedan za drugim, oko 5 minuta ukupno.

## Plan, po redu koristi

### 1. Jedna komanda za celu montažu (najveća ušteda, oko 10 min)
Danas Claude ručno pokreće 10 koraka (ingest, assemble, transcribe, marks, layout, init, build, lint, snapshot, render, check) i posle svakog čita izlaz. Nova skripta `montaza.py` radi sve to sama, u pozadini, sa trakom napretka u fajlu. Claude radi samo dve stvari koje traže pamet:
- bira najbolje uzimanje svake rečenice (edl.json),
- na kraju pogleda **jednu** kontrolnu sliku i pusti rils.

Očekivano: sa 120 koraka na oko 25, sa 15 minuta Claudeovog rada na 3 do 4.

### 2. Efekti se popunjavaju sami (oko 5 min)
Danas Claude za svaki efekat otvara build.py, piše CLIP blok, pokreće build, render i proveru, i gleda slike. Za većinu efekata tekst dolazi iz izgovorenih reči, pa skripta može sama da popuni CLIP blok iz words.json i da izabere trenutak. Claude samo potvrdi listu: „efekat X na rečenici Y”. Svi efekti se renderuju odjednom, paralelno, a ne jedan po jedan.

### 3. Brži izrez osobe (sa 15 min na 3 do 4 min za ceo rils)
- Model ide na grafički čip (CoreML) umesto na procesor: 2x.
- Model gleda sliku u pola rezolucije, a ivica se vraća na punu: još oko 2x.
- Jedan izrez celog rilsa umesto posebnog izreza za svaki efekat. Efekti posle samo isecaju svoj deo.
- Izrez kreće odmah posle sečenja klipova, u pozadini, dok Claude radi titlove.
- Pre puštanja proveravam kvalitet ivica (kosa, ruke) na tvom klipu i na klipu „svi 7”, da ne bude lošije nego sad.

### 4. Manje gledanja slika (oko 2 min)
Danas Claude pogleda 12 do 22 slike po montaži. Sve provere (raspored glave, bezbedna zona, titlovi, rezovi, efekti) idu u **jednu** kontrolnu sliku. Dodatne slike Claude otvara samo kad skripta prijavi problem.

### 5. Bez probnog kruga pre rendera (oko 1 min)
Danas se rils gradi dva puta: jednom sa crvenom zonom za snimke, pa ponovo za render. Pošto je render brz (1,5 min), radi se odmah pravi render. Skripta automatski proverava zonu i lice iz rendera.

### 6. Ništa ne sme da „zabode”
- Svaki dugi korak ide u pozadinu i piše napredak („izrez 640/1800, još 2 min”). Claude to javi tebi, umesto da ćuti.
- Svaki korak ima rok. Ako HyperFrames ili izrez zastane, skripta ga prekine, pokuša još jednom, pa jasno kaže šta nije uspelo.

## Očekivani rezultat

| | Danas | Posle |
|---|---|---|
| Rils bez izreza (titlovi + 2 do 3 efekta) | 15 min | **4 do 6 min** |
| Rils sa 5 efekata | 30 do 35 min | **7 do 9 min** |
| Stil sa izrezom celog rilsa | 30+ min | **8 do 10 min** |

## Redosled rada

1. Brži izrez (tačka 3), jer je mali i odmah se meri. Oko pola dana.
2. `montaza.py` i jedna kontrolna slika (tačke 1, 4, 5, 6). Oko 1 do 2 dana.
3. Automatsko popunjavanje efekata (tačka 2), počevši od 10 najčešće biranih. Oko 2 dana.
4. Merenje na 3 prava rilsa pre i posle, pa nova verzija na GitHubu.

## Šta treba od tebe
- Odluka da li počinjemo i kojim redom.
- 2 do 3 sirova klipa koja inače montiraš, za merenje pre i posle (može i „svi 7”).
