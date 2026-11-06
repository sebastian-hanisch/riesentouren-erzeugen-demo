"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt eine Analyse mit gesetzten Zahlen, nicht Seeds. Optimum 100, kürzeste Rundreise 80."""

import rte_algorithm as A
import rte_construct as K
import rte_constants as C
import rte_evaluation as ev
from rte_scenario import Instance

INST = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (1, 1, 1), 2)
OPT, TOUR = 100.0, 80.0


def _res(key, split, length, routes=((1, 2), (3,))):
    gap = ev.gap_percent(split, OPT)
    return ev.Result(key, (1, 2, 3), A.SplitResult(split, routes), length, gap, ev.gap_percent(length, TOUR), gap == 0.0)


def _a(splits=None, lengths=None, constructor=5, constructions=None) -> ev.Analysis:
    splits = {"random": 150.0, "nn": 110.0, "cheapest": 104.0, "farthest": 108.0, "nn_split": 112.0, "insert_split": 100.0, **(splits or {})}
    lengths = {"random": 160.0, "nn": 88.0, "cheapest": 84.0, "farthest": 80.0, "nn_split": 96.0, "insert_split": 100.0, **(lengths or {})}
    return ev.Analysis(ev.Settings(constructor=constructor), INST, A.ExactResult(OPT, ((1, 2, 3),)), TOUR, (1, 2, 3), A.SplitResult(105.0, ((1, 2, 3),)),
                       constructions or {}, {k: _res(k, splits[k], lengths[k]) for k in C.KEYS})


# ----------------------------------------------------------------------------------------------------------------------------------- gewählter Erzeuger

def test_constructor_verdict_success_when_the_split_hits_the_optimum():
    kind, text = ev.verdict_constructor(_a())
    assert kind == "success"
    assert text == "Einfügen nach Split: Der Split der Reihenfolge ergibt 100,00 in 2 Routen, das Optimum. Die Rundreise ist 25,0 % länger als die kürzeste."


def test_constructor_verdict_threshold_is_inclusive_at_five_percent():
    kind, text = ev.verdict_constructor(_a(splits={"insert_split": 104.9}, constructor=5))
    assert kind == "info" and "104,90" in text and "4,9 % über dem Optimum 100,00 (1 Route)" in text
    kind, text = ev.verdict_constructor(_a(splits={"nn": 105.0}, constructor=1))
    assert kind == "warning" and text.startswith("Nächster Nachbar:") and "5,0 % über dem Optimum" in text and "10,0 % länger als die kürzeste" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Kernfrage

def test_best_length_key_is_the_cheapest_split_among_the_three_and_ties_go_to_the_first():
    assert ev.best_length_key(_a()) == "cheapest"
    assert ev.best_length_key(_a(splits={"nn": 104.0, "cheapest": 104.0, "farthest": 104.0})) == "nn"


def test_core_verdict_split_insertion_wins():
    kind, text = ev.verdict_core(_a())
    assert kind == "success"
    assert "Einfügen nach Split ergibt 100,00 (0,0 % über dem Optimum 100,00)" in text
    assert "(Billigstes Einfügen) 104,00 (4,0 %)" in text
    assert "beim Einfügen nach Split 25,0 % länger als die kürzeste, beim längenorientierten 5,0 %" in text


def test_core_verdict_equal_and_reversed():
    kind, text = ev.verdict_core(_a(splits={"insert_split": 104.0}))
    assert kind == "info" and "Beide sind gleich gut" in text
    kind, text = ev.verdict_core(_a(splits={"insert_split": 109.0}))
    assert kind == "warning" and "Hier ist es umgekehrt" in text and "ergibt 109,00 (9,0 % über dem Optimum 100,00)" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Spur

def _construction(key, evaluated_per_step):
    steps = tuple(K.Step(c + 1, 0, 1.0, (), e, tuple(range(1, c + 2)), 1.0, 1.0) for c, e in enumerate(evaluated_per_step))
    return K.Construction(key, "Split-Kosten der Teilfolge", tuple(range(1, len(steps) + 1)), steps)


def test_trace_verdict_counts_the_evaluated_candidates():
    a = _a(constructions={"insert_split": _construction("insert_split", [1, 2, 3])})
    kind, text = ev.verdict_trace(a)
    assert kind == "info"
    assert "Einfügen nach Split bewertet in 3 Schritten insgesamt 6 Kandidaten (Maß: Split-Kosten der Teilfolge)" in text and "Die Folge 1 2 3 ergibt nach dem Split 100,00 (0,0 % über dem Optimum)" in text


def test_trace_verdict_of_the_random_constructor_evaluates_nothing():
    a = _a(constructor=0, constructions={"random": K.Construction("random", "Zufall (kein Maß)", (1, 2, 3), (K.Step(1, 0, 0.0, (), 0, (1,), 1.0, 1.0),) * 3)})
    kind, text = ev.verdict_trace(a)
    assert kind == "info" and "Der Zufall bewertet keine Kandidaten: die Folge 1 2 3 ergibt nach dem Split 150,00 (50,0 % über dem Optimum)" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Vergleich

def test_compare_verdict_agree_disagree_and_equal():
    kind, text = ev.verdict_compare(_a(), "nn", "farthest")          # nn: Länge 88, Split 110; farthest: Länge 80, Split 108: die kürzere Rundreise ergibt den billigeren Split
    assert kind == "info" and "Länge und Split sind sich einig" in text
    assert "Nächster Nachbar: Länge 88,00, Split 110,00 (10,0 % über dem Optimum)" in text and "Fernstes Einfügen: Länge 80,00, Split 108,00 (8,0 %)" in text
    kind, text = ev.verdict_compare(_a(), "farthest", "insert_split")  # farthest ist kürzer (80 gegen 100), aber teurer (108 gegen 100)
    assert kind == "warning" and "Länge und Split gehen auseinander: Die kürzere Rundreise ergibt den teureren Split" in text
    kind, text = ev.verdict_compare(_a(lengths={"nn": 84.0}), "nn", "cheapest")
    assert kind == "info" and "Mindestens eines der beiden Maße ist gleich" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Streudiagramm

def _scatter(rho, n_opt=48, pct=2.5, n=40320):
    return {"rho": rho, "n_orders": n, "n_opt": n_opt, "percentile": pct}


def test_scatter_verdict_thresholds_at_eight_tenths_and_one_half():
    assert ev.verdict_scatter(_scatter(0.8))[0] == "info" and "eng (Rangkorrelation 0,80)" in ev.verdict_scatter(_scatter(0.8))[1]
    assert "mittel (Rangkorrelation 0,79)" in ev.verdict_scatter(_scatter(0.79))[1]
    assert ev.verdict_scatter(_scatter(0.5))[0] == "info" and "mittel" in ev.verdict_scatter(_scatter(0.5))[1]
    kind, text = ev.verdict_scatter(_scatter(0.49))
    assert kind == "warning" and "schwach (Rangkorrelation 0,49)" in text


def test_scatter_verdict_names_orders_optimal_ones_and_percentile():
    kind, text = ev.verdict_scatter(_scatter(0.92, n_opt=48, pct=2.49))
    assert "alle 40 320 Reihenfolgen" in text and "Die 48 optimalen Reihenfolgen" in text and "unter den kürzesten 2,5 % aller Reihenfolgen" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def _stats(medians, reference="exact", n=12, count=80):
    by = {k: {"min": 0.0, "median": medians[k], "max": medians[k] + 10.0, "mean": medians[k] + 1.0, "optimal": 3} for k in C.KEYS}
    return {"n": n, "count": count, "reference": reference, "by_key": by, "agree": 7, "disagree": 3}


MEDIANS = {"random": 52.5, "nn": 8.2, "cheapest": 4.7, "farthest": 3.8, "nn_split": 9.8, "insert_split": 0.6}


def test_band_verdict_names_the_medians_and_maxima():
    kind, text = ev.verdict_bands(_stats(MEDIANS))
    assert kind == "info"
    assert "Bei n = 12 (80 Instanzen, Abstand zum exakten Optimum)" in text
    assert "Einfügen nach Split im Median 0,6 % (Maximum 10,6 %), fernstes Einfügen 3,8 % (Maximum 13,8 %)" in text
    assert "Nächster Nachbar nach Split 9,8 %, Nächster Nachbar 8,2 %" in text


def test_band_verdict_warns_when_another_constructor_is_best_and_names_the_reference_of_larger_n():
    kind, text = ev.verdict_bands(_stats({**MEDIANS, "insert_split": 5.0, "farthest": 4.0}, reference="pyvrp", n=50, count=32))
    assert kind == "warning" and "zur Referenz PyVRP (nicht bewiesen optimal)" in text and "Der beste Erzeuger im Median ist hier Fernstes Einfügen" in text


def test_band_verdict_without_the_precomputed_file():
    kind, text = ev.verdict_bands({})
    assert kind == "warning" and C.BAND_FILE in text


def test_band_stats_from_stored_rows_by_hand():
    row = lambda ref, tour, split, length: {"ref": ref, "tour_length": tour, "split": {k: split for k in C.KEYS}, "length": {k: length for k in C.KEYS}}
    cell = {"n": 10, "reference": "exact", "rows": [{**row(100.0, 80.0, 100.0, 80.0)}, {**row(100.0, 80.0, 110.0, 88.0)}, {**row(100.0, 80.0, 120.0, 96.0)}]}
    by = ev.band_stats(cell)["by_key"]["nn"]
    assert (by["min"], by["median"], by["max"], by["optimal"]) == (0.0, 10.0, 20.0, 1) and abs(by["mean"] - 10.0) < 1e-9
    assert abs(by["length_median"] - 10.0) < 1e-9 and abs(by["length_max"] - 20.0) < 1e-9
    stats = ev.band_stats(cell)
    assert stats["agree"] == 0 and stats["disagree"] == 0                  # alle Erzeuger haben je Instanz dieselben Werte: keine Paare mit Unterschied


def test_pair_agreement_counts_by_hand():
    rows = [{"ref": 100.0, "tour_length": 80.0, "split": {"random": 120.0, "nn": 110.0, "cheapest": 105.0, "farthest": 108.0, "nn_split": 112.0, "insert_split": 100.0},
             "length": {"random": 160.0, "nn": 90.0, "cheapest": 85.0, "farthest": 80.0, "nn_split": 96.0, "insert_split": 100.0}}]
    stats = ev.band_stats({"n": 10, "reference": "exact", "rows": rows})
    # Nach Länge geordnet: farthest 80 (Split 108), cheapest 85 (105), nn 90 (110), nn_split 96 (112), insert_split 100 (100), random 160 (120).
    # Je Paar (kürzer vor länger): gleichgerichtet, wenn der Split des kürzeren kleiner ist: 3 + 3 + 2 + 1 + 1 = 10; gegenläufig 2 + 1 + 1 + 1 + 0 = 5; zusammen 15 Paare.
    assert (stats["agree"], stats["disagree"]) == (10, 5)
