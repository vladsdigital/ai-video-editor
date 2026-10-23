# Reel Lab

Ti snimiš klipove. Claude montira rils.

Reel Lab je dodatak (plugin) za Claude koji od sirovih klipova pravi gotov Instagram rils u tvom stilu montaže:
bira najbolje snimke, izbacuje pauze, pravi titlove na srpskom, hrvatskom, bosanskom ili engleskom (latinicom ili
ćirilicom), dodaje efekte, pravi varijacije za trial reels i može sam da objavi umesto tebe.

## Instalacija u Claude aplikaciji

1. Otvori Claude aplikaciju na računaru i idi na karticu **Code**.
2. Klikni **+** pored polja za poruku, pa **Plugins**, pa **Browse plugins**.
3. Gore desno klikni **Add**, pa **Add marketplace**, pa **Add from a repository**.
4. Nalepi ovaj link i klikni **Sync**:

```
https://github.com/vladsdigital/reel-lab
```

5. Sa liste instaliraj **Reel Lab**.
6. Otvori novi čet i ukucaj:

```
/reel-lab setup
```

Podešavanje te pita gde ti stižu klipovi, na kom jeziku pričaš i da li titlovi idu latinicom ili ćirilicom. Onda
zajedno pravimo tvoj stil montaže: pošalješ linkove do rilsova čija ti se montaža sviđa (ili opišeš izgled, ili
izabereš neki od ugrađenih stilova) i daš mu ime. Dok to radiš, alati se skidaju u pozadini (oko 3,2 GB, samo
jednom). Na prvoj montaži doterujemo stil, a posle samo ubaciš klipove i kažeš: montiraj u [ime tvog stila].

## Instalacija iz terminala (ako ti je tako lakše)

Samo ako koristiš Claude Code u Terminalu (Mac) ili PowerShell-u (Windows). Ove komande pokrećeš sam, ne unutar
Claude-a. Svaki red nalepi posebno.

```bash
claude plugin marketplace add vladsdigital/reel-lab
```

```bash
claude plugin install reel-lab@reel-lab
```

Na Windowsu za ovaj put prvo treba da instaliraš [Git for Windows](https://git-scm.com/downloads).

Onda otvori Claude Code i ukucaj `/reel-lab setup`.

## Tačniji titlovi uz Soniox (opciono)

Reel Lab pravi transkript besplatno, na tvom računaru, bez interneta. Ako hoćeš primetno tačnije titlove na našem
jeziku (imena, padeži, naši izrazi), možeš da povežeš Soniox. Plaća se po korišćenju, oko par centi po rilsu.

1. Napravi nalog na [console.soniox.com](https://console.soniox.com).
2. U delu **API Keys** napravi novi ključ i kopiraj ga.
3. U četu reci Claude-u: "poveži Soniox". Ključ uzima direktno iz kopiranog, ne moraš da ga lepiš u čet.

Ključ ostaje samo na tvom računaru. Ako se predomisliš, reci: "vrati besplatno prepoznavanje govora".

## Karuseli

Reel Lab pravi i karusele, u tvom izgledu. U bilo kom četu reci:

```
napravi karusel o [tvoja tema]
```

ili

```
napravi karusel od mog poslednjeg rilsa
```

Prvi put te pita za tvoj Instagram nalog i izgled: pošalješ skrinšotove karusela koji ti se sviđaju pa Claude
napravi taj stil, ili izabereš jedan od 3 gotova izgleda. Onda napiše tekst za svaki slajd, sačeka tvoje "može",
dizajnira slajdove i otvori pregled koji listaš kao pravu objavu. Slajdovi završe u folderu Carousels u tvom
korisničkom folderu, spremni za objavu.

## Objavljivanje

Kad je rils gotov, reci "objavi ovo" ili "objavi moje trial rilsove". Reel Lab objavljuje na Instagram (kao običan
rils ili trial reel), TikTok, YouTube Shorts i Facebook: odmah, u vreme koje izabereš, ili sa razmakom od par
minuta. Ide preko servisa Zernio, besplatno za prva 2 povezana naloga. Ništa ne ide napolje dok ne kažeš "može".

## Ažuriranja

Popravke i novi efekti stižu kao ažuriranja. Tvoji izbori i tvoji stilovi ostaju sačuvani.

**Lakši način:** kad izađe nova verzija, Claude ti javi i pita da li hoćeš da je instalira. Reci da. Možeš i sam
da kažeš bilo kad:

```
ažuriraj Reel Lab
```

**Iz terminala:** svaki red nalepi posebno.

```bash
claude plugin marketplace update reel-lab
```

```bash
claude plugin update reel-lab@reel-lab
```

Posle ažuriranja otvori novi čet, da Claude učita novu verziju.

## Pomoć

Piši na podrska@vladsdigital.com. Napiši šta si radio ili radila i šta se desilo. Snimak ekrana mnogo pomaže.

---

© Vladsdigital. Zasnovano na Creator Studio (Marc Cleroux), uz dozvolu autora. Nije povezano sa Anthropic-om ni Instagramom.
