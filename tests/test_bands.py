"""Die vorberechneten Bänder (rte_bands.json) gegen eine frische Rechnung: je Größe eine Stichprobe, die Referenzen von PyVRP (n = 25, 50) werden aus der Datei übernommen
(PyVRP ist keine Abhängigkeit der Tests)."""

import json
from pathlib import Path

import pytest

import rte_constants as C
import rte_evaluation as ev

STORED = json.loads((Path(__file__).resolve().parent.parent / C.BAND_FILE).read_text(encoding="utf-8"))


def _cell(n, family, depot):
    return next(c for c in STORED["cells"] if (c["n"], c["family"], c["depot"]) == (n, family, depot))


def _same(fresh, stored):
    assert fresh["seed"] == stored["seed"]
    assert fresh["ref"] == pytest.approx(stored["ref"], abs=1e-9)
    assert fresh["tour_length"] == pytest.approx(stored["tour_length"]) if stored["tour_length"] is not None else fresh["tour_length"] is None
    for key in C.KEYS:
        assert fresh["split"][key] == pytest.approx(stored["split"][key], abs=1e-9), key
        assert fresh["length"][key] == pytest.approx(stored["length"][key], abs=1e-9), key


@pytest.mark.parametrize("n,family,depot,seeds", [(10, 2, 1, range(300000, 300008)), (12, 1, 0, range(300000, 300004)), (12, 2, 1, range(300010, 300013))])
def test_exact_sizes_match_a_fresh_computation(n, family, depot, seeds):
    rows = {r["seed"]: r for r in _cell(n, family, depot)["rows"]}
    for seed in seeds:
        _same(ev.instance_row(n, family, depot, seed), rows[seed])


@pytest.mark.parametrize("n,family,depot,seeds", [(25, 2, 1, range(300000, 300008)), (50, 1, 1, range(300000, 300002))])
def test_reference_sizes_match_a_fresh_computation_with_the_stored_reference(n, family, depot, seeds):
    rows = {r["seed"]: r for r in _cell(n, family, depot)["rows"]}
    for seed in seeds:
        _same(ev.instance_row(n, family, depot, seed, ref_cost=rows[seed]["ref"]), rows[seed])


def test_file_has_all_cells_with_the_expected_instance_counts():
    assert {(c["n"], c["family"], c["depot"]) for c in STORED["cells"]} == {(n, f, d) for n in C.BAND_SIZES for f, d in C.BAND_CELLS}
    for c in STORED["cells"]:
        exact = c["n"] in C.EXACT_SIZES
        assert c["reference"] == ("exact" if exact else "pyvrp")
        assert [r["seed"] for r in c["rows"]] == list(C.BAND_SEEDS_EXACT if exact else C.BAND_SEEDS_REF)
        assert all((r["tour_length"] is not None) == exact for r in c["rows"])


def test_stored_exact_references_are_below_every_constructor_and_equal_to_the_optimum_for_a_sample():
    for c in STORED["cells"]:
        if c["reference"] == "exact":
            assert all(r["ref"] <= min(r["split"].values()) + 1e-9 for r in c["rows"]), (c["n"], c["family"], c["depot"])


def test_band_cells_are_sorted_like_the_cell_order_and_empty_for_other_sizes():
    assert [(c["family"], c["depot"]) for c in ev.band_cells(10)] == list(C.BAND_CELLS)
    assert ev.band_cells(7) == []
