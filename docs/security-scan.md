# Saugumo skenavimas — 3 savaitė

Laikas (UTC): 2026-10-26T19:30:03.367950+00:00

| Vaizdas | HIGH | CRITICAL |
|---|---:|---:|
| mlops-cpu:local | 44 | 0 |
| mlops-onnx:local | 44 | 0 |

Žali JSON ir SBOM: `docs/week3/`. HIGH radinius peržiūrėti prieš viešinant. Kiekvieną išimtį pagrįsti, o ne pakeisti skaičių į nulį.

CRITICAL vartas: PASS

## HIGH radinių analizė

- Visi HIGH radiniai yra Debian bazinio vaizdo (`python:3.12-slim-trixie`) OS paketuose;
  Python paketuose (sklearn, FastAPI, onnxruntime) radinių nėra — todėl cpu ir onnx skaičiai sutampa.
- Visiems radiniams pataisymo dar nėra (NO FIX); `apt-get upgrade` Dockerfile jau pritaikytas.
   - Skaičius išpūstas paketų šeimų: util-linux (9 paketai), ncurses (4), systemd (2) — realiai 8 skirtingi CVE (44 radiniai).
- Rizika vertinama kaip žema: paketai yra sistemos įrankiai (mount, login, terminalas), kurių API nenaudoja;
  konteineris veikia kaip ne-root vartotojas (UID 1000), shell/login neeksponuojami.
- Planas: periodiškai perbuildinti vaizdus (apt-get upgrade pritaikys pataisymus, kai Debian juos išleis);
  ateityje svarstyti distroless bazinį vaizdą, kuriame šių įrankių nėra.
