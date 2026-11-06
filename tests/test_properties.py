"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für JEDE Instanz und jeden Erzeuger gelten müssen, auf festen Zufallsinstanzen."""

import dataclasses

import numpy as np
import pytest

import rte_algorithm as A
import rte_constants as C
import rte_construct as K
from rte_scenario import Instance, make_instance

CASES = [(f, d, r, s) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3) for s in range(3)]
NO_TIE_KEYS = ("nn", "cheapest", "farthest", "nn_split", "insert_split")


def _inst(f, d, r, s, n=8):
    return make_instance(n, f, d, r, s)


@pytest.mark.parametrize("key", C.KEYS)
@pytest.mark.parametrize("f,d,r,s", CASES)
def test_every_constructor_returns_a_permutation_with_one_step_per_customer(key, f, d, r, s):
    inst = _inst(f, d, r, s)
    c = K.construct(key, inst, s)
    assert sorted(c.order) == list(range(1, inst.n + 1))
    assert len(c.steps) == inst.n and c.steps[-1].order == c.order
    assert all(0 <= x.position <= len(x.order) - 1 for x in c.steps)
    assert K.construct(key, inst, s).order == c.order                       # deterministisch


@pytest.mark.parametrize("key", C.KEYS)
@pytest.mark.parametrize("f,d,r,s", CASES)
def test_the_split_of_the_partial_orders_never_decreases_while_customers_are_added(key, f, d, r, s):
    """Ein Kunde mehr kann die Zerlegung nie billiger machen: Wegnehmen verkürzt jede Route (Dreiecksungleichung) und senkt die Last."""
    costs = [x.split_cost for x in K.construct(key, _inst(f, d, r, s), s).steps]
    assert all(b >= a - 1e-9 for a, b in zip(costs, costs[1:]))


@pytest.mark.parametrize("key", C.KEYS)
@pytest.mark.parametrize("f,d,r,s", CASES)
def test_split_and_length_are_never_below_optimum_and_shortest_tour(key, f, d, r, s):
    inst = _inst(f, d, r, s)
    c = K.construct(key, inst, s)
    assert A.split(inst, c.order).cost >= A.exact_cvrp(inst).cost - 1e-9
    assert A.route_length(inst, c.order) >= A.tsp_tour(inst)[0] - 1e-9


@pytest.mark.parametrize("f,d,r,s", CASES)
def test_cheapest_insertion_is_at_most_twice_the_shortest_tour(f, d, r, s):
    """Laut Rosenkrantz u. a. (Abstract; Dreiecksungleichung): nächstes und billigstes Einfügen höchstens doppelt so lang wie die kürzeste Rundreise. Hier an den Instanzen geprüft."""
    inst = _inst(f, d, r, s)
    assert A.route_length(inst, K.construct("cheapest", inst).order) <= 2 * A.tsp_tour(inst)[0] + 1e-9


@pytest.mark.parametrize("key", NO_TIE_KEYS)
@pytest.mark.parametrize("f,d,r,s", [c for c in CASES if c[0] > 0][::2])
def test_shifting_and_scaling_the_map_changes_no_order(key, f, d, r, s):
    inst = _inst(f, d, r, s)
    moved = dataclasses.replace(inst, xy=tuple((3.0 * x + 7.0, 3.0 * y - 2.0) for x, y in inst.xy))
    assert K.construct(key, moved, s).order == K.construct(key, inst, s).order


@pytest.mark.parametrize("key", NO_TIE_KEYS)
@pytest.mark.parametrize("f,d,r,s", [c for c in CASES if c[0] > 0][::3])
def test_renumbering_the_customers_renumbers_the_order(key, f, d, r, s):
    """Ohne Gleichstände hängt der Erzeuger nicht von den Nummern ab: die Folge des umnummerierten Problems ist die umnummerierte Folge."""
    inst = _inst(f, d, r, s)
    perm = list(np.random.default_rng(s + 1).permutation(inst.n))                  # neuer Kunde t ist alter Kunde perm[t - 1] + 1
    renamed = Instance((inst.xy[0],) + tuple(inst.xy[p + 1] for p in perm), tuple(inst.demand[p] for p in perm), inst.capacity)
    back = {t + 1: int(p) + 1 for t, p in enumerate(perm)}
    assert tuple(back[c] for c in K.construct(key, renamed, s).order) == K.construct(key, inst, s).order


@pytest.mark.parametrize("f,d,r,s", CASES[::2])
def test_split_insertion_is_never_worse_than_a_random_order(f, d, r, s):
    inst = _inst(f, d, r, s)
    assert A.split(inst, K.construct("insert_split", inst).order).cost <= A.split(inst, A.random_order(inst, s)).cost + 1e-9


def test_with_capacity_for_everyone_split_equals_the_length_of_the_tour_for_all_constructors(hand):
    roomy = dataclasses.replace(hand, capacity=sum(hand.demand))
    for key in C.KEYS:
        order = K.construct(key, roomy, 3).order
        assert A.split(roomy, order).routes == (order,)
        assert A.split(roomy, order).cost == pytest.approx(A.route_length(roomy, order))


def test_rank_correlation_of_identical_reversed_and_constant_data():
    x = np.arange(10.0)
    assert A.rank_correlation(x, x) == pytest.approx(1.0)
    assert A.rank_correlation(x, -x) == pytest.approx(-1.0)
    assert A.rank_correlation(x, np.ones(10)) == 0.0


def test_the_correlation_of_a_known_ranking_by_hand():
    """Ränge 0 1 2 3 gegen 0 2 1 3: Differenzen 0, -1, 1, 0; Spearman = 1 - 6·2 / (4·15) = 0,8."""
    assert A.rank_correlation(np.array([1.0, 2.0, 3.0, 4.0]), np.array([10.0, 30.0, 20.0, 40.0])) == pytest.approx(0.8)
