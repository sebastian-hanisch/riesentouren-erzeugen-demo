"""Randfälle, an denen Erzeuger und Kern erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1 und n = 2, Kunden am selben Ort, Kunde auf dem Depot,
Nachfrage gleich Kapazität, Gleichstände, Reglergrenzen, Abstände an der Null."""

import dataclasses

import numpy as np
import pytest

import rte_algorithm as A
import rte_constants as C
import rte_construct as K
import rte_evaluation as ev
from rte_scenario import Instance, make_instance


def test_one_customer_for_every_constructor():
    inst = Instance(((0.0, 0.0), (3.0, 4.0)), (2,), 2)
    for key in C.KEYS:
        c = K.construct(key, inst, 0)
        assert c.order == (1,) and len(c.steps) == 1 and c.steps[0].position == 0
        assert A.split(inst, c.order).cost == pytest.approx(10.0)
    assert A.exact_cvrp(inst).cost == pytest.approx(10.0) and A.tsp_tour(inst)[0] == pytest.approx(10.0)
    lengths, costs = A.all_lengths_and_costs(inst)
    assert lengths.tolist() == [pytest.approx(10.0)] and costs.tolist() == [pytest.approx(10.0)]


def test_exactly_two_customers_everything_agrees():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0)), (1, 1), 2)       # Last 2 passt: eine Route 5 + 5 + 10
    for key in C.KEYS:
        order = K.construct(key, inst, 0).order
        assert sorted(order) == [1, 2] and A.split(inst, order).cost == pytest.approx(20.0)
    tight = dataclasses.replace(inst, capacity=1)                           # zwei Fahrten 10 + 20
    for key in C.KEYS:
        assert A.split(tight, K.construct(key, tight, 0).order).cost == pytest.approx(30.0)


def test_all_customers_on_one_point():
    inst = Instance(((0.0, 0.0),) + ((3.0, 4.0),) * 4, (1, 1, 1, 1), 2)
    for key in C.KEYS:
        order = K.construct(key, inst, 1).order
        assert sorted(order) == [1, 2, 3, 4]
        assert A.split(inst, order).cost == pytest.approx(20.0)             # zwei Routen zu je 10, die Reihenfolge ist gleichgültig
    assert A.exact_cvrp(inst).cost == pytest.approx(20.0)


def test_a_customer_on_the_depot_costs_nothing():
    inst = Instance(((0.0, 0.0), (0.0, 0.0), (3.0, 4.0), (-3.0, 4.0)), (1, 1, 1), 2)
    assert A.exact_cvrp(inst).cost == pytest.approx(16.0)                  # (1) kostet 0, (2 3) kostet 5 + 6 + 5
    for key in C.KEYS:
        order = K.construct(key, inst, 0).order
        assert sorted(order) == [1, 2, 3] and A.split(inst, order).cost >= 16.0 - 1e-9


def test_demand_equal_to_capacity_forces_single_routes():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0), (-3.0, 4.0)), (4, 4, 4), 4)
    for key in C.KEYS:
        order = K.construct(key, inst, 0).order
        assert A.split(inst, order).routes == tuple((c,) for c in order)
        assert A.split(inst, order).cost == pytest.approx(2 * (5 + 10 + 5))


def test_ties_choose_the_smaller_customer_and_the_smaller_place():
    """Alle Kunden gleich weit vom Depot (auf einem Kreis): Nächster Nachbar und die Einfüge-Startwahl nehmen die kleinere Nummer."""
    inst = Instance(((0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (-5.0, 0.0), (0.0, -5.0)), (1, 1, 1, 1), 4)
    assert K.construct("nn", inst).order[0] == 1
    assert K.construct("cheapest", inst).steps[0].customer == 1 and K.construct("farthest", inst).steps[0].customer == 1
    assert K.construct("insert_split", inst).steps[0].customer == 1


def test_generator_is_deterministic_and_respects_capacity_and_bounds():
    for family in range(len(C.FAMILIES)):
        for depot in range(2):
            a = make_instance(8, family, depot, 4, 123)
            assert a == make_instance(8, family, depot, 4, 123) and a != make_instance(8, family, depot, 4, 124)
            assert a.capacity >= max(a.demand) and a.n == 8
            xs = [p[0] for p in a.xy[1:]]
            assert 0 <= min(xs) and max(xs) <= (16 if family == 0 else 100)


def test_every_control_limit_gives_a_valid_analysis():
    for n in (C.N_MIN, C.N_MAX):
        for routes in (C.ROUTES_MIN, C.ROUTES_MAX):
            for constructor in (0, len(C.KEYS) - 1):
                a = ev.analyse(ev.Settings(n, 2, 1, routes, C.SEED_MAX, constructor))
                assert all(r.split.cost >= a.exact.cost - 1e-9 for r in a.results.values())
                assert a.tour_split.cost >= a.exact.cost - 1e-9


def test_gap_helpers_at_their_edges():
    assert ev.gap_percent(10.0, 0.0) == 0.0                                  # keine Referenzkosten
    assert ev.gap_percent(5.0 + 1e-12, 5.0) == 0.0                           # unter der Toleranz kein Abstand
    assert ev.gap_percent(4.0, 5.0) == 0.0                                   # unter der Referenz zählt als null (Referenz nicht bewiesen optimal)
    assert ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.num(40320) == "40 320" and ev.de(3.14159) == "3,14" and ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen"
    assert ev.pct(4.26) == "4,3 %" and ev.pct(4.24) == "4,2 %"


def test_scatter_data_for_the_smallest_instance_has_all_orders():
    d = ev.scatter_data(ev.Settings(C.N_MIN, 1, 0, 3, 1, 5))
    assert d["n_orders"] == 720 and len(d["sample_length"]) == min(C.SCATTER_POINTS, 720) and d["n_opt"] >= 1
    assert -1.0 <= d["rho"] <= 1.0 and 0.0 <= d["percentile"] <= 100.0
