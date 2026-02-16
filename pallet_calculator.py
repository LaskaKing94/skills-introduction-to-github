#!/usr/bin/env python3
"""Kalkulator wysokości i masy palety dla kartonów leżących na płasko."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

CATALOG_PATH = Path("carton_catalog.json")
PALLETS: Dict[str, Tuple[int, int]] = {
    "80x120": (80, 120),
    "100x120": (100, 120),
    "80x60": (80, 60),
}


@dataclass
class Carton:
    name: str
    length: int
    width: int
    height: int
    weight_kg: Optional[float] = None

    @property
    def area(self) -> int:
        return self.length * self.width


DEFAULT_CARTONS: Dict[str, Carton] = {
    "KARTON L": Carton("KARTON L", 50, 60, 27),
    "KARTON GRATIA": Carton("KARTON GRATIA", 50, 47, 20),
    "KARTON OLYMPIA": Carton("KARTON OLYMPIA", 50, 60, 27),
    "KARTON GAIA": Carton("KARTON GAIA", 30, 39, 20),
    "KARTON GAIA MINI": Carton("KARTON GAIA MINI", 29, 30, 20),
    "KARTON SCULPTOR": Carton("KARTON SCULPTOR", 65, 19, 19),
    "AKCESORIA": Carton("AKCESORIA", 30, 50, 20),
}


@dataclass
class Placement:
    name: str
    x: int
    y: int
    length: int
    width: int
    height: int


class Layer:
    def __init__(self, pallet_length: int, pallet_width: int) -> None:
        self.pallet_length = pallet_length
        self.pallet_width = pallet_width
        self.free_rects: List[Tuple[int, int, int, int]] = [(0, 0, pallet_length, pallet_width)]
        self.placements: List[Placement] = []

    @property
    def layer_height(self) -> int:
        return max((p.height for p in self.placements), default=0)

    def try_place(self, carton: Carton) -> bool:
        best_choice = None
        best_score = None

        for idx, (fx, fy, fl, fw) in enumerate(self.free_rects):
            for l, w in ((carton.length, carton.width), (carton.width, carton.length)):
                if l <= fl and w <= fw:
                    score = (fl - l) * (fw - w)
                    if best_score is None or score < best_score:
                        best_score = score
                        best_choice = (idx, fx, fy, fl, fw, l, w)

        if best_choice is None:
            return False

        idx, fx, fy, fl, fw, l, w = best_choice
        self.placements.append(Placement(carton.name, fx, fy, l, w, carton.height))

        self.free_rects.pop(idx)
        right = (fx + l, fy, fl - l, w)
        top = (fx, fy + w, fl, fw - w)

        for rect in (right, top):
            if rect[2] > 0 and rect[3] > 0:
                self.free_rects.append(rect)

        self._prune_free_rects()
        return True

    def _prune_free_rects(self) -> None:
        pruned: List[Tuple[int, int, int, int]] = []
        for rect in self.free_rects:
            if not self._is_contained(rect, self.free_rects):
                pruned.append(rect)
        self.free_rects = pruned

    @staticmethod
    def _is_contained(target: Tuple[int, int, int, int], rects: Iterable[Tuple[int, int, int, int]]) -> bool:
        tx, ty, tl, tw = target
        for rx, ry, rl, rw in rects:
            if (rx, ry, rl, rw) == target:
                continue
            if tx >= rx and ty >= ry and tx + tl <= rx + rl and ty + tw <= ry + rw:
                return True
        return False


def load_catalog(path: Path = CATALOG_PATH) -> Dict[str, Carton]:
    if not path.exists():
        save_catalog(DEFAULT_CARTONS, path)
        return DEFAULT_CARTONS.copy()

    raw = json.loads(path.read_text(encoding="utf-8"))
    catalog: Dict[str, Carton] = {}
    for entry in raw:
        carton = Carton(**entry)
        catalog[carton.name] = carton
    return catalog


def save_catalog(catalog: Dict[str, Carton], path: Path = CATALOG_PATH) -> None:
    payload = [asdict(c) for c in catalog.values()]
    payload.sort(key=lambda x: x["name"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_items(items: List[str]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for token in items:
        if "=" not in token:
            raise ValueError(f"Niepoprawny format pozycji: '{token}'. Użyj NAZWA=ILOŚĆ")
        name, qty_str = token.split("=", 1)
        qty = int(qty_str)
        if qty <= 0:
            raise ValueError(f"Ilość dla '{name}' musi być > 0")
        result[name.strip()] = result.get(name.strip(), 0) + qty
    return result


def calculate_plan(
    catalog: Dict[str, Carton],
    pallet: Tuple[int, int],
    quantities: Dict[str, int],
    pallet_base_height_cm: int = 14,
    pallet_tare_weight_kg: float = 0.0,
) -> Dict[str, object]:
    boxes: List[Carton] = []
    total_box_weight = 0.0

    for name, qty in quantities.items():
        if name not in catalog:
            raise KeyError(f"Nie znaleziono kartonu: {name}")
        carton = catalog[name]
        boxes.extend([carton] * qty)
        if carton.weight_kg is not None:
            total_box_weight += carton.weight_kg * qty

    pallet_len, pallet_wid = pallet
    for box in boxes:
        if not (
            (box.length <= pallet_len and box.width <= pallet_wid)
            or (box.width <= pallet_len and box.length <= pallet_wid)
        ):
            raise ValueError(
                f"Karton '{box.name}' ({box.length}x{box.width}) nie mieści się na palecie {pallet_len}x{pallet_wid}"
            )

    boxes.sort(key=lambda c: c.area, reverse=True)
    layers: List[Layer] = []

    for box in boxes:
        placed = False
        for layer in layers:
            if layer.try_place(box):
                placed = True
                break
        if not placed:
            new_layer = Layer(pallet_len, pallet_wid)
            if not new_layer.try_place(box):
                raise RuntimeError(f"Nie udało się ułożyć kartonu '{box.name}'")
            layers.append(new_layer)

    layer_heights = [layer.layer_height for layer in layers]
    total_height = pallet_base_height_cm + sum(layer_heights)

    weight_known_for_all = all(catalog[name].weight_kg is not None for name in quantities)
    total_weight = total_box_weight + pallet_tare_weight_kg if weight_known_for_all else None

    return {
        "layers": layers,
        "layers_count": len(layers),
        "layer_heights": layer_heights,
        "total_height_cm": total_height,
        "total_weight_kg": total_weight,
        "weight_complete": weight_known_for_all,
    }


def cmd_list(catalog: Dict[str, Carton]) -> None:
    print("Dostępne kartony:")
    for c in sorted(catalog.values(), key=lambda x: x.name):
        w = f"{c.weight_kg} kg" if c.weight_kg is not None else "brak"
        print(f"- {c.name}: {c.length}x{c.width}x{c.height} cm, waga: {w}")

    print("\nDostępne palety:")
    for name, size in PALLETS.items():
        print(f"- {name} ({size[0]}x{size[1]} cm)")


def cmd_set_weight(catalog: Dict[str, Carton], name: str, weight: float) -> None:
    if name not in catalog:
        raise KeyError(f"Nie znaleziono kartonu '{name}'")
    catalog[name].weight_kg = weight
    save_catalog(catalog)
    print(f"Zapisano wagę {weight} kg dla: {name}")


def cmd_calculate(
    catalog: Dict[str, Carton],
    pallet_name: str,
    items: List[str],
    pallet_base_height_cm: int,
    pallet_tare_weight_kg: float,
) -> None:
    if pallet_name not in PALLETS:
        raise KeyError(f"Nieznana paleta '{pallet_name}'. Dostępne: {', '.join(PALLETS)}")

    quantities = parse_items(items)
    plan = calculate_plan(
        catalog,
        PALLETS[pallet_name],
        quantities,
        pallet_base_height_cm=pallet_base_height_cm,
        pallet_tare_weight_kg=pallet_tare_weight_kg,
    )

    print("=== PODSUMOWANIE ===")
    print(f"Paleta: {pallet_name}")
    print(f"Liczba warstw: {plan['layers_count']}")
    print(f"Wysokości warstw [cm]: {plan['layer_heights']}")
    print(f"Wysokość całkowita [cm]: {plan['total_height_cm']}")

    if plan["weight_complete"]:
        print(f"Masa całkowita [kg]: {plan['total_weight_kg']:.2f}")
    else:
        print("Masa całkowita: brak pełnych danych (uzupełnij wagi kartonów)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kalkulator wysokości i masy palety")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Lista kartonów i palet")

    set_weight = sub.add_parser("set-weight", help="Zapisz wagę kartonu do bazy JSON")
    set_weight.add_argument("name", help="Nazwa kartonu")
    set_weight.add_argument("weight", type=float, help="Waga kartonu [kg]")

    calc = sub.add_parser("calculate", help="Oblicz wysokość i masę palety")
    calc.add_argument("--pallet", required=True, choices=list(PALLETS.keys()))
    calc.add_argument(
        "--item",
        action="append",
        required=True,
        help="Pozycja w formacie NAZWA=ILOŚĆ, można podać wiele razy",
    )
    calc.add_argument("--pallet-base-height", type=int, default=14, help="Wysokość samej palety [cm]")
    calc.add_argument("--pallet-tare", type=float, default=0.0, help="Masa własna palety [kg]")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    catalog = load_catalog()

    if args.cmd == "list":
        cmd_list(catalog)
    elif args.cmd == "set-weight":
        cmd_set_weight(catalog, args.name, args.weight)
    elif args.cmd == "calculate":
        cmd_calculate(catalog, args.pallet, args.item, args.pallet_base_height, args.pallet_tare)


if __name__ == "__main__":
    main()
