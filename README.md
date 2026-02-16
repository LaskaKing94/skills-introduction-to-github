# Kalkulator palety (wysokość + masa)

Prosta aplikacja CLI w Pythonie do planowania ułożenia kartonów na palecie.

## Co robi aplikacja

- bierze listę kartonów i ich ilości,
- układa kartony warstwami na wybranej palecie (kartony zawsze leżą na płasko),
- liczy łączną wysokość palety,
- po uzupełnieniu wag kartonów liczy też masę całkowitą palety.

## Dane startowe

### Kartony

- `KARTON L` – 50x60x27 cm
- `KARTON GRATIA` – 50x47x20 cm
- `KARTON OLYMPIA` – 50x60x27 cm
- `KARTON GAIA` – 30x39x20 cm
- `KARTON GAIA MINI` – 29x30x20 cm
- `KARTON SCULPTOR` – 65x19x19 cm
- `AKCESORIA` – 30x50x20 cm

### Palety

- `80x120`
- `100x120`
- `80x60`

## Uruchomienie

```bash
python pallet_calculator.py list
```

## Ustawienie wag kartonów (zapisywane do bazy JSON)

```bash
python pallet_calculator.py set-weight "KARTON L" 18.5
python pallet_calculator.py set-weight "KARTON GAIA" 9.2
```

Wagi zapisywane są w pliku `carton_catalog.json`.

## Obliczenie wysokości i masy palety

```bash
python pallet_calculator.py calculate \
  --pallet 80x120 \
  --item "KARTON L=4" \
  --item "KARTON GAIA=6" \
  --item "AKCESORIA=2" \
  --pallet-base-height 14 \
  --pallet-tare 25
```

### Wynik

Program pokaże:

- liczbę warstw,
- wysokość każdej warstwy,
- wysokość całkowitą palety,
- masę całkowitą (jeśli każda użyta pozycja ma wpisaną wagę).

## Uwaga praktyczna

Algorytm używa heurystyki pakowania 2D (obrót kartonu tylko w płaszczyźnie podstawy). Daje dobry, szybki wynik operacyjny, ale nie gwarantuje matematycznie idealnego optimum dla każdego zestawu.
