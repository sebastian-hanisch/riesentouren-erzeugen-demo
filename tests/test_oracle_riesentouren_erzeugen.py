"""Orakel-Tests riesentouren-erzeugen-demo: die Erzeuger und der kopierte Kern gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

- Jeder Erzeuger noch einmal in reinem Python (math.hypot, kein numpy, keine Instanzmatrix), das Argmin je Schritt über alle Kandidaten neu gesucht.
- Der Split der Teilfolgen über die Aufzählung aller 2^(k-1) Schnittmengen der Folge.
- Kern: Split gegen Schnittmengen, exakter Löser gegen Aufzählung aller Zerlegungen und Reihenfolgen, kürzeste Rundreise gegen alle Permutationen, vektorisierter Split gegen Einzel-Split.
Mini-Instanzen mit festen Seeds (range), insgesamt wenige Sekunden."""

import itertools
import math

import numpy as np
import pytest

import rte_algorithm as A
import rte_construct as K
from rte_scenario import make_instance

CELLS = [(f, d, r) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3)]


def _dist(inst, a, b):
    (xa, ya), (xb, yb) = inst.xy[a], inst.xy[b]
    return math.hypot(xa - xb, ya - yb)


def _route(inst, customers):
    path = (0, *customers, 0)
    return sum(_dist(inst, u, v) for u, v in zip(path, path[1:]))


def _split_by_cuts(inst, order):
    """Alle Schnittmengen: zwischen je zwei aufeinanderfolgenden Kunden schneiden oder nicht."""
    best, n = math.inf, len(order)
    for mask in range(1 << (n - 1)):
        routes, current = [], [order[0]]
        for t in range(1, n):
            if (mask >> (t - 1)) & 1:
                routes.append(current)
                current = []
            current.append(order[t])
        routes.append(current)
        if all(sum(inst.demand[c - 1] for c in r) <= inst.capacity for r in routes):
            best = min(best, sum(_route(inst, r) for r in routes))
    return best


def _far(inst):
    return max(range(1, inst.n + 1), key=lambda c: (_dist(inst, 0, c), -c))


def oracle_nn(inst):
    left, cur, order = set(range(1, inst.n + 1)), 0, []
    while left:
        c = min(left, key=lambda c: (round(_dist(inst, cur, c), 9), c))
        order.append(c)
        left.remove(c)
        cur = c
    return tuple(order)


def _added(inst, tour, c, k):
    a, b = tour[k], tour[(k + 1) % len(tour)]
    return _dist(inst, a, c) + _dist(inst, c, b) - _dist(inst, a, b)


def oracle_cheapest(inst):
    far = _far(inst)
    tour, left = [0, far], set(range(1, inst.n + 1)) - {far}
    while left:
        _, c, k = min((round(_added(inst, tour, c, k), 9), c, k) for c in left for k in range(len(tour)))
        tour.insert(k + 1, c)
        left.remove(c)
    return tuple(tour[1:])


def oracle_farthest(inst):
    far = _far(inst)
    tour, left = [0, far], set(range(1, inst.n + 1)) - {far}
    while left:
        c = max(left, key=lambda c: (round(min(_dist(inst, c, t) for t in tour), 9), -c))
        _, k = min((round(_added(inst, tour, c, k), 9), k) for k in range(len(tour)))
        tour.insert(k + 1, c)
        left.remove(c)
    return tuple(tour[1:])


def oracle_nn_split(inst):
    left, order = set(range(1, inst.n + 1)), ()
    while left:
        _, c = min((round(_split_by_cuts(inst, order + (c,)), 9), c) for c in left)
        order += (c,)
        left.remove(c)
    return order


def oracle_insert_split(inst):
    order = ()
    for c in sorted(range(1, inst.n + 1), key=lambda c: (-round(_dist(inst, 0, c), 9), c)):
        _, p = min((round(_split_by_cuts(inst, order[:p] + (c,) + order[p:]), 9), p) for p in range(len(order) + 1))
        order = order[:p] + (c,) + order[p:]
    return order


ORACLES = {"nn": oracle_nn, "cheapest": oracle_cheapest, "farthest": oracle_farthest, "nn_split": oracle_nn_split, "insert_split": oracle_insert_split}


@pytest.mark.parametrize("key", list(ORACLES))
@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_constructor_matches_an_independent_reimplementation(key, family, depot, routes):
    for seed in range(5):
        inst = make_instance(7, family, depot, routes, seed)
        assert K.construct(key, inst, seed).order == ORACLES[key](inst), (key, seed)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_recorded_split_cost_of_every_step_matches_the_enumeration_of_all_cuts(family, depot, routes):
    inst = make_instance(6, family, depot, routes, 3)
    for key in ("nn", "cheapest", "insert_split", "nn_split"):
        for step in K.construct(key, inst, 3).steps:
            assert step.split_cost == pytest.approx(_split_by_cuts(inst, step.order)), (key, step.order)
            assert step.length == pytest.approx(_route(inst, step.order)), (key, step.order)


# --- Kern (aus Stück 1 kopiert, hier mit denselben Orakeln wie dort geprüft) ------------------------------------------------------------------------

def _exact(inst):
    cust = list(range(1, inst.n + 1))
    cache = {}

    def best(group):
        if group not in cache:
            cache[group] = min(_route(inst, p) for p in itertools.permutations(group))
        return cache[group]

    def partitions(rest):
        if not rest:
            yield []
            return
        first, others = rest[0], rest[1:]
        for k in range(len(others) + 1):
            for comb in itertools.combinations(others, k):
                group = (first, *comb)
                if sum(inst.demand[c - 1] for c in group) <= inst.capacity:
                    for tail in partitions(tuple(c for c in others if c not in comb)):
                        yield [group, *tail]

    return min(sum(best(g) for g in part) for part in partitions(tuple(cust)))


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_kernel_split_exact_tour_and_vectorised_split(family, depot, routes):
    for seed in range(4):
        inst = make_instance(6, family, depot, routes, seed)
        rng = np.random.default_rng(seed)
        order = tuple(int(c) + 1 for c in rng.permutation(6))
        assert A.split(inst, order).cost == pytest.approx(_split_by_cuts(inst, order))
        ex = A.exact_cvrp(inst)
        assert ex.cost == pytest.approx(_exact(inst)) and A.is_feasible_plan(inst, ex.routes)
        length, tour = A.tsp_tour(inst)
        assert length == pytest.approx(min(_route(inst, p) for p in itertools.permutations(range(1, 7))))
        perms = np.array(list(itertools.permutations(range(1, 7))))[::41]
        assert A.split_all(inst, perms) == pytest.approx([A.split(inst, tuple(int(c) for c in p)).cost for p in perms])


@pytest.mark.parametrize("family,depot,routes", CELLS[::3])
def test_lengths_and_costs_of_all_orders_match_the_single_functions(family, depot, routes):
    inst = make_instance(5, family, depot, routes, 2)
    lengths, costs = A.all_lengths_and_costs(inst)
    assert len(lengths) == len(costs) == 120
    expected = [(_route(inst, p), A.split(inst, p).cost) for p in itertools.permutations(range(1, 6))]
    assert np.allclose(np.array(sorted(zip(lengths, costs))), np.array(sorted(expected)))      # gleiche Paare (Länge, Split); gespiegelte Folgen haben gleiche Länge und gleichen Split
    assert float(costs.min()) == pytest.approx(A.exact_cvrp(inst).cost)       # Dominanz aus Stück 1
