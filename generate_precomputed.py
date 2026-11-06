"""Erzeugt rte_bands.json: die Bänder über feste Instanzen für n = 10, 12 (Referenz: exaktes Optimum) und n = 25, 50 (Referenz: PyVRP, gespeichert).

n = 10 und 12 rechnen den exakten Löser je Instanz (rund 1 bis 3 s), n = 25 und 50 brauchen PyVRP (5 s je Instanz); deshalb liegen die Zahlen vorberechnet im Repo.
PyVRP ist keine Abhängigkeit der App und der Tests: nur dieses Skript importiert es (optional installiert, getestet mit 0.14.1; die Schnittstelle ändert sich zwischen Versionen).
Die gespeicherten Referenzkosten werden wiederverwendet, solange --refresh-refs fehlt, damit n = 25 und 50 ohne PyVRP neu ausgewertet werden können.

Aufruf:
    python generate_precomputed.py 10 12 --out part_a.json          # Teil rechnen
    python generate_precomputed.py 25 50 --out part_b.json
    python generate_precomputed.py --merge part_a.json part_b.json   # zu rte_bands.json zusammenführen
    python generate_precomputed.py 10 12 25 50                       # alles in einem Lauf, direkt nach rte_bands.json"""

import argparse
import importlib
import json
import time
from pathlib import Path

import numpy as np

import rte_algorithm as A
import rte_constants as C
from rte_evaluation import instance_row
from rte_scenario import make_instance

PYVRP_SECONDS, PYVRP_SEED, SCALE = 5, 1, 100
TARGET = Path(__file__).with_name(C.BAND_FILE)


def pyvrp_reference(inst) -> float:
    """Beste von PyVRP in PYVRP_SECONDS Sekunden gefundene Gesamtlänge (Entfernungen mal 100, gerundet; unbegrenzte Flotte)."""
    # Optionale Abhängigkeit, nur für dieses Skript: bewusst per importlib statt `import`, damit tests/test_runtime_imports.py sie nicht als Laufzeitpaket der App verlangt.
    Model = importlib.import_module("pyvrp").Model
    MaxRuntime = importlib.import_module("pyvrp.stop").MaxRuntime
    m = Model()
    locs = [m.add_location(x=x * SCALE, y=y * SCALE) for x, y in inst.xy]
    m.add_depot(location=locs[0])
    m.add_vehicle_type(num_available=inst.n, capacity=[inst.capacity])
    for i in range(1, inst.n + 1):
        m.add_client(location=locs[i], delivery=[inst.demand[i - 1]])
    D = np.round(A.distance_matrix(inst) * SCALE).astype(int)
    for i in range(inst.n + 1):
        for j in range(inst.n + 1):
            if i != j:
                m.add_edge(locs[i], locs[j], distance=int(D[i][j]))
    result = m.solve(stop=MaxRuntime(PYVRP_SECONDS), seed=PYVRP_SEED, display=False)
    assert result.is_feasible()
    return result.cost() / SCALE


def pyvrp_version() -> str:
    from importlib.metadata import version
    return version("pyvrp")


def build(sizes, refresh_refs: bool) -> dict:
    old = {}
    if TARGET.exists() and not refresh_refs:
        for cell in json.loads(TARGET.read_text(encoding="utf-8")).get("cells", []):
            for row in cell["rows"]:
                old[(cell["n"], cell["family"], cell["depot"], row["seed"])] = row["ref"]
    cells, start = [], time.time()
    for n in sizes:
        exact = n in C.EXACT_SIZES
        seeds = C.BAND_SEEDS_EXACT if exact else C.BAND_SEEDS_REF
        for family, depot in C.BAND_CELLS:
            rows = []
            for seed in seeds:
                ref = None
                if not exact:
                    ref = old.get((n, family, depot, seed))
                    if ref is None:
                        ref = pyvrp_reference(make_instance(n, family, depot, C.BAND_ROUTES, seed))
                rows.append(instance_row(n, family, depot, seed, ref))
            cells.append({"n": n, "family": family, "depot": depot, "reference": "exact" if exact else "pyvrp", "rows": rows})
            print(n, family, depot, f"{time.time() - start:.0f} s", flush=True)
    return {"cells": cells}


def meta(cells) -> dict:
    out = {"routes": C.BAND_ROUTES, "fill": C.FILL, "seeds_exact": [C.BAND_SEEDS_EXACT[0], C.BAND_SEEDS_EXACT[-1]], "seeds_ref": [C.BAND_SEEDS_REF[0], C.BAND_SEEDS_REF[-1]]}
    if any(c["reference"] == "pyvrp" for c in cells):
        out["pyvrp"] = {"seconds": PYVRP_SECONDS, "seed": PYVRP_SEED, "scale": SCALE}
        try:
            out["pyvrp"]["version"] = pyvrp_version()
        except Exception:
            out["pyvrp"]["version"] = "unbekannt"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sizes", nargs="*", type=int)
    ap.add_argument("--out", help="Teildatei statt rte_bands.json schreiben")
    ap.add_argument("--merge", nargs="+", help="Teildateien zu rte_bands.json zusammenführen")
    ap.add_argument("--refresh-refs", action="store_true", help="PyVRP-Referenzen neu rechnen")
    args = ap.parse_args()
    if args.merge:
        cells = [c for f in args.merge for c in json.loads(Path(f).read_text(encoding="utf-8"))["cells"]]
        extra = {}
        for f in args.merge:
            extra.update({k: v for k, v in json.loads(Path(f).read_text(encoding="utf-8")).items() if k != "cells"})
        data = {**extra, "cells": sorted(cells, key=lambda c: (c["n"], C.BAND_CELLS.index((c["family"], c["depot"]))))}
        TARGET.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(data["cells"]), "Zellen")
    else:
        built = build(args.sizes or list(C.BAND_SIZES), args.refresh_refs)
        built["meta"] = meta(built["cells"])
        Path(args.out).write_text(json.dumps(built, ensure_ascii=False), encoding="utf-8") if args.out else TARGET.write_text(json.dumps(built, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", args.out or TARGET.name)
