"""Jede Zahl der README („Befunde“) und der Preset-Hilfen, nachgerechnet mit denselben Funktionen wie die App (DEMO-PLAYBOOK §4).

Die Bänder kommen aus rte_bands.json (tests/test_bands.py rechnet Stichproben davon frisch nach); Kosten werden auf eine Stelle verglichen."""

import numpy as np
import pytest

import rte_algorithm as A
import rte_constants as C
import rte_evaluation as ev
from conftest import OPTIMUM

ORDER = list(C.KEYS)   # random, nn, cheapest, farthest, nn_split, insert_split


def _stats(n):
    return ev.merge_stats(ev.band_cells(n))


def _col(n, field):
    return [round(_stats(n)["by_key"][k][field], 1) for k in C.KEYS]


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def test_bands_have_the_expected_instances():
    for n, count in ((10, 80), (12, 80), (25, 32), (50, 32)):
        cells = ev.band_cells(n)
        assert len(cells) == 4 and _stats(n)["count"] == count
        assert _stats(n)["reference"] == ("exact" if n in C.EXACT_SIZES else "pyvrp")


def test_bands_median_of_the_gap():
    assert _col(10, "median") == [37.3, 5.4, 3.2, 2.3, 7.8, 0.0]
    assert _col(12, "median") == [52.5, 8.2, 4.7, 3.8, 9.8, 0.6]
    assert _col(25, "median") == [126.9, 14.0, 9.2, 6.8, 24.3, 3.3]
    assert _col(50, "median") == [275.7, 19.7, 15.9, 10.4, 36.9, 8.3]


def test_bands_maximum_and_mean_of_the_gap():
    assert _col(10, "max") == [80.1, 28.1, 26.1, 28.7, 29.0, 10.0]
    assert _col(12, "max") == [132.2, 23.7, 28.1, 30.7, 34.1, 15.3]
    assert _col(25, "max") == [227.7, 26.2, 17.8, 16.9, 37.7, 18.8]
    assert _col(50, "max") == [395.5, 38.9, 24.8, 19.3, 60.9, 17.4]
    assert _col(10, "mean") == [38.6, 7.3, 5.4, 4.7, 9.0, 1.1]
    assert _col(12, "mean") == [56.5, 8.5, 6.3, 6.1, 11.2, 1.8]
    assert _col(25, "mean") == [133.2, 13.8, 8.9, 7.7, 23.4, 5.1]
    assert _col(50, "mean") == [274.6, 19.9, 16.3, 11.3, 35.9, 9.1]


def test_bands_optimum_counts_and_minimum_of_split_insertion():
    assert [_stats(10)["by_key"][k]["optimal"] for k in C.KEYS] == [0, 1, 6, 6, 0, 40]
    assert [_stats(12)["by_key"][k]["optimal"] for k in C.KEYS] == [0, 3, 5, 3, 0, 32]
    assert [_stats(25)["by_key"][k]["optimal"] for k in C.KEYS] == [0] * 6          # die Referenz von PyVRP erreicht keiner
    assert round(_stats(50)["by_key"]["insert_split"]["min"], 1) == 1.5


def test_bands_length_over_the_shortest_tour_for_the_exact_sizes():
    assert _col(10, "length_median") == [83.6, 7.1, 1.6, 0.0, 20.4, 22.6]
    assert _col(12, "length_median") == [111.4, 9.5, 3.6, 0.0, 24.1, 20.2]
    assert _col(10, "length_max") == [194.8, 27.5, 12.9, 10.5, 54.1, 77.7]
    assert _col(12, "length_max") == [199.3, 33.5, 17.1, 12.9, 64.9, 93.0]


def test_bands_agreement_of_length_and_split_over_all_pairs():
    assert (_stats(10)["agree"], _stats(10)["disagree"]) == (791, 352) and round(100 * 791 / (791 + 352), 1) == 69.2
    assert (_stats(12)["agree"], _stats(12)["disagree"]) == (818, 344) and round(100 * 818 / (818 + 344), 1) == 70.4


def test_no_constructor_beats_the_pyvrp_reference():
    for n in (25, 50):
        for cell in ev.band_cells(n):
            for row in cell["rows"]:
                assert all(row["split"][k] >= row["ref"] - 1e-9 for k in C.KEYS), (n, row["seed"])


def test_bands_metadata_names_the_reference_solver():
    meta = ev.load_bands()["meta"]
    assert meta["pyvrp"] == {"seconds": 5, "seed": 1, "scale": 100, "version": meta["pyvrp"]["version"]} and meta["pyvrp"]["version"] == "0.14.1"
    assert meta["routes"] == 3 and meta["fill"] == 0.9


# ----------------------------------------------------------------------------------------------------------------------------------- Korrelation über alle Reihenfolgen

def test_rank_correlation_over_forty_instances_with_eight_customers():
    """n = 8, vier Zellen mal Seeds 300000 bis 300009, Zielroutenzahl 3: Länge gegen Split über alle 40 320 Reihenfolgen je Instanz."""
    per_cell, rho_all, pct_all = [], [], []
    for family, depot in C.BAND_CELLS:
        rhos = []
        for seed in range(300000, 300010):
            d = ev.scatter_data(ev.Settings(8, family, depot, 3, seed, 5))
            rhos.append(d["rho"])
            pct_all.append(d["percentile"])
        per_cell.append((round(min(rhos), 2), round(float(np.median(rhos)), 2), round(max(rhos), 2)))
        rho_all += rhos
    assert per_cell == [(0.77, 0.91, 0.97), (0.49, 0.85, 0.91), (0.46, 0.62, 0.79), (0.33, 0.54, 0.87)]
    assert (round(min(rho_all), 2), round(float(np.median(rho_all)), 2), round(max(rho_all), 2)) == (0.33, 0.74, 0.97)
    assert (round(min(pct_all), 1), round(float(np.median(pct_all)), 1), round(max(pct_all), 1)) == (0.2, 2.3, 26.5)


# ----------------------------------------------------------------------------------------------------------------------------------- Presets

def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_preset_help_numbers():
    a = _preset("Länge gegen Split (n = 8)")
    r = a.results
    assert round(r["farthest"].split_gap, 1) == 3.9 and r["farthest"].length_gap == 0.0 and r["insert_split"].optimal and round(r["insert_split"].length_gap, 1) == 12.8
    a = _preset("Länge und Split gehen auseinander (n = 8)")
    assert round(a.results["farthest"].split_gap, 1) == 19.7 and round(ev.scatter_data(ev.Settings(**C.PRESETS["Länge und Split gehen auseinander (n = 8)"]))["rho"], 2) == 0.14
    a = _preset("Anhängen nach Split scheitert (n = 10)")
    assert round(a.results["nn_split"].split_gap, 1) == 23.2 and round(a.results["nn"].split_gap, 1) == 4.3
    a = _preset("Alle Erzeuger nahe beieinander (n = 8)")
    assert round(max(a.results[k].split_gap for k in C.KEYS if k != "random"), 1) == 1.0
    a = _preset("Einfügen nach Split verliert (n = 8)")
    assert round(a.results["insert_split"].split_gap, 1) == 15.0 and a.results["farthest"].optimal
    a = _preset("Größere Instanz (n = 12)")
    assert a.results["insert_split"].optimal and [round(a.results[k].split_gap) for k in ("nn", "cheapest", "farthest")] == [21, 21, 21]


def test_default_preset_numbers():
    s = ev.Settings()
    a = ev.analyse(s)
    d = ev.scatter_data(s)
    assert a.inst.n == 8 and round(a.exact.cost, 2) == 450.33 and a.exact.routes == a.exact.routes and len(a.exact.routes) == 3
    assert round(a.tour_length, 2) == 317.63 and round(a.tour_split.cost, 2) == 467.81
    assert [round(a.results[k].split_gap, 1) for k in C.KEYS] == [20.6, 3.9, 5.5, 3.9, 7.1, 0.0]
    assert [round(a.results[k].length_gap, 1) for k in C.KEYS] == [64.5, 0.5, 7.8, 0.0, 33.5, 12.8]
    assert (d["n_orders"], d["n_opt"]) == (40320, 48) and round(d["rho"], 2) == 0.92 and round(d["percentile"], 1) == 2.5
    assert a.constructions["insert_split"].evaluated == 36 and a.constructions["nn_split"].evaluated == 36 and a.constructions["nn"].evaluated == 36


# ----------------------------------------------------------------------------------------------------------------------------------- Handinstanz (Fixture)

def test_hand_example_table_of_the_plan(hand):
    """PLAN-02: die fünf Zeilen der Handtabelle in den gerundeten Zahlen, die die README nennt."""
    import rte_construct as K
    opt = A.exact_cvrp(hand).cost
    assert round(opt, 2) == 44.36 and opt == pytest.approx(OPTIMUM)
    rows = {}
    for key in ("nn", "cheapest", "farthest", "nn_split", "insert_split"):
        order = K.construct(key, hand).order
        split = A.split(hand, order).cost
        rows[key] = (order, round(A.route_length(hand, order), 2), round(split, 2), round(ev.gap_percent(split, opt), 1))
    assert rows == {
        "nn": ((5, 3, 4, 1, 2, 6), 41.52, 49.45, 11.5), "cheapest": ((5, 2, 6, 3, 4, 1), 38.82, 46.47, 4.8), "farthest": ((2, 6, 3, 4, 1, 5), 38.24, 47.19, 6.4),
        "nn_split": ((5, 3, 6, 2, 4, 1), 44.14, 44.36, 0.0), "insert_split": ((5, 3, 6, 2, 4, 1), 44.14, 44.36, 0.0),
    }
    assert round(100 * (44.1426 / 38.2367 - 1), 1) == 15.4 and round(100 * (44.1426 / 41.5214 - 1), 1) == 6.3      # Länge der Split-Folge gegen Rundreise und Nächsten Nachbarn
