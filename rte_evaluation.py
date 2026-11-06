"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import itertools
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import numpy as np

import rte_algorithm as A
import rte_construct as K
import rte_constants as C
from rte_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    seed: int = C.DEFAULT_SEED
    constructor: int = C.DEFAULT_CONSTRUCTOR


@dataclass(frozen=True)
class Result:
    key: str
    order: tuple[int, ...]
    split: A.SplitResult
    length: float
    split_gap: float                    # Prozent über dem Optimum
    length_gap: float                   # Prozent über der kürzesten Rundreise
    optimal: bool


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    exact: A.ExactResult
    tour_length: float
    tour_order: tuple[int, ...]
    tour_split: A.SplitResult           # Split der kürzesten Rundreise
    constructions: dict                 # Schlüssel -> rte_construct.Construction
    results: dict                       # Schlüssel -> Result


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(n):,}".replace(",", " ")


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def gap_percent(cost: float, reference: float) -> float:
    """Abstand zur Referenz in Prozent der Referenz; unter der Toleranz oder ohne Referenzkosten gibt es keinen Abstand; nie negativ (eine Referenz, die nicht bewiesen optimal ist, darf unterboten werden)."""
    if reference <= 0 or cost - reference <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def order_text(order) -> str:
    return " ".join(str(c) for c in order)


# ----------------------------------------------------------------------------------------------------------------------------------- Analyse

def make_result(inst: Instance, key: str, order, optimum: float, tour_length: float) -> Result:
    split = A.split(inst, order)
    length = A.route_length(inst, order)
    gap = gap_percent(split.cost, optimum)
    return Result(key, tuple(order), split, length, gap, gap_percent(length, tour_length), gap == 0.0)


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed)
    exact = A.exact_cvrp(inst)
    tour_length, tour_order = A.tsp_tour(inst)
    constructions = {key: K.construct(key, inst, settings.seed) for key in C.KEYS}
    results = {key: make_result(inst, key, c.order, exact.cost, tour_length) for key, c in constructions.items()}
    return Analysis(settings, inst, exact, tour_length, tour_order, A.split(inst, tour_order), constructions, results)


def best_length_key(a: Analysis) -> str:
    """Der längenorientierte Erzeuger mit dem billigsten Split (bei Gleichstand der erste in KEYS)."""
    return min(C.LENGTH_KEYS, key=lambda k: (a.results[k].split.cost, C.KEYS.index(k)))


def scatter_data(settings: Settings) -> dict:
    """Experiment 3: Länge und Split-Kosten aller n! Reihenfolgen (nur n <= ENUM_MAX), Rangkorrelation, Länge-Perzentil der optimalen Reihenfolgen."""
    inst = make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed)
    lengths, costs = A.all_lengths_and_costs(inst)
    optimum = A.exact_cvrp(inst).cost
    ranks = A._ranks(lengths)
    hit = costs <= optimum + C.TOL
    rng = np.random.default_rng(settings.seed)
    sample = rng.choice(len(lengths), size=min(C.SCATTER_POINTS, len(lengths)), replace=False)
    return {
        "n_orders": len(lengths), "rho": A.rank_correlation(lengths, costs), "n_opt": int(hit.sum()),
        "percentile": 100.0 * float(np.median(ranks[hit])) / max(len(lengths) - 1, 1),
        "sample_length": lengths[sample], "sample_cost": costs[sample], "optimum": optimum,
    }


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def instance_row(n: int, family: int, depot: int, seed: int, ref_cost: float | None = None) -> dict:
    """Eine feste Instanz: Referenz (exakt oder vorgegeben), kürzeste Rundreise (nur n <= 12) und Länge und Split-Kosten aller Erzeuger."""
    inst = make_instance(n, family, depot, C.BAND_ROUTES, seed)
    exact = n in C.EXACT_SIZES
    ref = A.exact_cvrp(inst).cost if exact else ref_cost
    row = {"seed": seed, "ref": ref, "tour_length": A.tsp_tour(inst)[0] if exact else None, "split": {}, "length": {}}
    for key in C.KEYS:
        order = K.construct(key, inst, seed).order
        row["split"][key] = A.split(inst, order).cost
        row["length"][key] = A.route_length(inst, order)
    return row


def band_stats(cell: dict) -> dict:
    """Aus den gespeicherten Kosten einer Zelle: je Erzeuger Abstand (Min, Median, Max, Mittel), Optimum-Zahl, Länge über der kürzesten Rundreise (nur n <= 12), Paar-Einigkeit."""
    rows = cell["rows"]
    out = {"n": cell["n"], "count": len(rows), "reference": cell["reference"], "by_key": {}, "agree": 0, "disagree": 0}
    for key in C.KEYS:
        gaps = [gap_percent(r["split"][key], r["ref"]) for r in rows]
        entry = {"min": min(gaps), "median": median(gaps), "max": max(gaps), "mean": mean(gaps), "optimal": sum(g == 0.0 for g in gaps)}
        if rows[0]["tour_length"] is not None:
            lg = [gap_percent(r["length"][key], r["tour_length"]) for r in rows]
            entry.update({"length_median": median(lg), "length_max": max(lg)})
        out["by_key"][key] = entry
    for r in rows:
        for a, b in itertools.combinations(C.KEYS, 2):
            dl, ds = r["length"][a] - r["length"][b], r["split"][a] - r["split"][b]
            if abs(dl) > C.TOL and abs(ds) > C.TOL:
                out["agree"] += (dl > 0) == (ds > 0)
                out["disagree"] += (dl > 0) != (ds > 0)
    return out


def merge_stats(cells: list[dict]) -> dict:
    """Alle Zellen einer Größe zusammen: die Instanzen werden vereinigt (Zeilen konkateniert) und dann wie eine Zelle ausgewertet."""
    return band_stats({"n": cells[0]["n"], "reference": cells[0]["reference"], "rows": [r for c in cells for r in c["rows"]]})


@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_cells(n: int) -> list[dict]:
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    return sorted((c for c in load_bands().get("cells", []) if c["n"] == n), key=lambda c: order[(c["family"], c["depot"])])


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_constructor(a: Analysis) -> tuple[str, str]:
    """Der in der Seitenleiste gewählte Erzeuger gegen das Optimum."""
    r = a.results[C.KEYS[a.settings.constructor]]
    name = C.NAMES[r.key]
    if r.optimal:
        return "success", (f"{name}: Der Split der Reihenfolge ergibt {de(r.split.cost)} in {routes_word(len(r.split.routes))}, das Optimum. "
                           f"Die Rundreise ist {pct(r.length_gap)} länger als die kürzeste.")
    kind = "info" if r.split_gap < C.GAP_WARN else "warning"
    return kind, (f"{name}: Der Split der Reihenfolge ergibt {de(r.split.cost)} in {routes_word(len(r.split.routes))}, {pct(r.split_gap)} über dem Optimum {de(a.exact.cost)} "
                  f"({routes_word(len(a.exact.routes))}). Die Rundreise ist {pct(r.length_gap)} länger als die kürzeste.")


def verdict_core(a: Analysis) -> tuple[str, str]:
    """Kernfrage: nach Split oder nach Länge bauen? Einfügen nach Split gegen den besten längenorientierten Erzeuger dieser Instanz."""
    bk = best_length_key(a)
    best, split = a.results[bk], a.results["insert_split"]
    head = (f"Einfügen nach Split ergibt {de(split.split.cost)} ({pct(split.split_gap)} über dem Optimum {de(a.exact.cost)}), "
            f"der beste längenorientierte Erzeuger ({C.NAMES[bk]}) {de(best.split.cost)} ({pct(best.split_gap)}). ")
    tail = f"Die Rundreise ist beim Einfügen nach Split {pct(split.length_gap)} länger als die kürzeste, beim längenorientierten {pct(best.length_gap)}."
    if split.split.cost < best.split.cost - C.TOL:
        return "success", head + tail
    if split.split.cost > best.split.cost + C.TOL:
        return "warning", head + "Hier ist es umgekehrt: Das Maß „Split“ hilft bei dieser Instanz nicht. " + tail
    return "info", head + "Beide sind gleich gut. " + tail


def verdict_trace(a: Analysis) -> tuple[str, str]:
    """Experiment 1: Aufwand und Ergebnis des gewählten Erzeugers."""
    key = C.KEYS[a.settings.constructor]
    c, r = a.constructions[key], a.results[key]
    if key == "random":
        return "info", f"Der Zufall bewertet keine Kandidaten: die Folge {order_text(c.order)} ergibt nach dem Split {de(r.split.cost)} ({pct(r.split_gap)} über dem Optimum)."
    return "info", (f"{C.NAMES[key]} bewertet in {len(c.steps)} Schritten insgesamt {num(c.evaluated)} Kandidaten (Maß: {c.metric}). "
                    f"Die Folge {order_text(c.order)} ergibt nach dem Split {de(r.split.cost)} ({pct(r.split_gap)} über dem Optimum).")


def verdict_compare(a: Analysis, first: str, second: str) -> tuple[str, str]:
    """Experiment 2: zwei Erzeuger nebeneinander; geht die Länge der Rundreise einen anderen Weg als der Split?"""
    x, y = a.results[first], a.results[second]
    text = (f"{C.NAMES[first]}: Länge {de(x.length)}, Split {de(x.split.cost)} ({pct(x.split_gap)} über dem Optimum). "
            f"{C.NAMES[second]}: Länge {de(y.length)}, Split {de(y.split.cost)} ({pct(y.split_gap)}). ")
    dl, ds = x.length - y.length, x.split.cost - y.split.cost
    if abs(dl) <= C.TOL or abs(ds) <= C.TOL:
        return "info", text + "Mindestens eines der beiden Maße ist gleich."
    if (dl > 0) == (ds > 0):
        return "info", text + "Länge und Split sind sich einig: Die kürzere Rundreise ergibt auch den billigeren Split."
    return "warning", text + "Länge und Split gehen auseinander: Die kürzere Rundreise ergibt den teureren Split."


def verdict_scatter(data: dict) -> tuple[str, str]:
    """Experiment 3: Rangkorrelation und Lage der optimalen Reihenfolgen im Längen-Ranking."""
    rho = data["rho"]
    strength = "eng" if rho >= 0.8 else ("mittel" if rho >= 0.5 else "schwach")
    kind = "warning" if rho < 0.5 else "info"
    return kind, (f"Über alle {num(data['n_orders'])} Reihenfolgen ist der Zusammenhang zwischen Länge und Split-Kosten {strength} (Rangkorrelation {de(rho)}). "
                  f"Die {num(data['n_opt'])} optimalen Reihenfolgen liegen mit ihrer Länge im Median unter den kürzesten {pct(data['percentile'])} aller Reihenfolgen.")


def verdict_bands(stats: dict) -> tuple[str, str]:
    """Experiment 4: Bänder einer Größe (alle vier Zellen zusammen)."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    by = stats["by_key"]
    best = min(C.KEYS, key=lambda k: (by[k]["median"], C.KEYS.index(k)))
    split, farthest = by["insert_split"], by["farthest"]
    ref = "zum exakten Optimum" if stats["reference"] == "exact" else "zur Referenz PyVRP (nicht bewiesen optimal)"
    text = (f"Bei n = {stats['n']} ({stats['count']} Instanzen, Abstand {ref}): Einfügen nach Split im Median {pct(split['median'])} "
            f"(Maximum {pct(split['max'])}), fernstes Einfügen {pct(farthest['median'])} (Maximum {pct(farthest['max'])}); "
            f"Nächster Nachbar nach Split {pct(by['nn_split']['median'])}, Nächster Nachbar {pct(by['nn']['median'])}.")
    if best != "insert_split":
        return "warning", text + f" Der beste Erzeuger im Median ist hier {C.NAMES[best]}."
    return "info", text
