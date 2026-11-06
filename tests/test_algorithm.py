"""Erzeuger und Kern an der Handinstanz: jede Zahl ist hier aus Wurzeln von Hand zusammengesetzt, nicht aus dem Code abgeschrieben."""

import pytest

import rte_algorithm as A
import rte_construct as K
from conftest import OPTIMUM, S2, S18, S20, S29, S32, S37, S41, S45, S53, S72, S74, S148, S185, TOUR_LENGTH


def test_kernel_optimum_tour_and_split_from_stueck_1(hand):
    assert A.exact_cvrp(hand).cost == pytest.approx(OPTIMUM)
    assert A.exact_cvrp(hand).routes == ((1, 4), (2, 6, 3, 5))
    length, order = A.tsp_tour(hand)
    assert length == pytest.approx(TOUR_LENGTH) and order == (2, 6, 3, 4, 1, 5)
    assert A.split(hand, order).cost == pytest.approx(2 * S2 + (S72 + S37 + 7) + (S32 + S53 + S20 + S29))   # 47,19


# Zeilen der Handtabelle: Schlüssel -> (Reihenfolge, Länge, Split, Routen des Splits)
TABLE = {
    "nn": ((5, 3, 4, 1, 2, 6), S2 + S18 + 5 + S37 + S185 + S20 + S45, (S2 + S18 + S32) + (7 + S37 + S72) + (S29 + S20 + S45), ((5, 3), (4, 1), (2, 6))),
    "cheapest": ((5, 2, 6, 3, 4, 1), S2 + S37 + S20 + S53 + 5 + S37 + S72, (S2 + S37 + S20 + S53 + S32) + (7 + S37 + S72), ((5, 2, 6, 3), (4, 1))),
    "farthest": ((2, 6, 3, 4, 1, 5), TOUR_LENGTH, 2 * S2 + (S72 + S37 + 7) + (S32 + S53 + S20 + S29), ((2, 6, 3), (4, 1), (5,))),
    "nn_split": ((5, 3, 6, 2, 4, 1), S2 + S18 + S53 + S20 + S148 + S37 + S72, OPTIMUM, ((5, 3, 6, 2), (4, 1))),
    "insert_split": ((5, 3, 6, 2, 4, 1), S2 + S18 + S53 + S20 + S148 + S37 + S72, OPTIMUM, ((5, 3, 6, 2), (4, 1))),
}


@pytest.mark.parametrize("key", list(TABLE))
def test_the_five_constructors_on_the_hand_instance(hand, key):
    order, length, split_cost, routes = TABLE[key]
    c = K.construct(key, hand)
    assert c.order == order
    assert A.route_length(hand, c.order) == pytest.approx(length)
    result = A.split(hand, c.order)
    assert result.cost == pytest.approx(split_cost) and result.routes == routes


def test_random_constructor_is_a_seeded_permutation(hand):
    assert K.construct("random", hand, 3).order == K.construct("random", hand, 3).order == (2, 3, 1, 6, 5, 4)
    assert K.construct("random", hand, 4).order != K.construct("random", hand, 3).order
    assert K.construct("random", hand, 3).evaluated == 0


def test_cheapest_insertion_steps_by_hand(hand):
    """Start: Kunde 1 (am weitesten vom Depot, sqrt72). Dann je Längenzunahme: 5 vorn (sqrt2 + sqrt74 - sqrt72), 4 hinter die 5 (2 sqrt37 - sqrt74), 3 zwischen 5 und 4
    (sqrt18 + 5 - sqrt37), 6 zwischen 5 und 3 (sqrt41 + sqrt53 - sqrt18), 2 zwischen 5 und 6 (sqrt37 + sqrt20 - sqrt41)."""
    steps = K.construct("cheapest", hand).steps
    assert [(s.customer, s.position) for s in steps] == [(1, 0), (5, 0), (4, 1), (3, 1), (6, 1), (2, 1)]
    expected = [S72, S2 + S74 - S72, 2 * S37 - S74, S18 + 5 - S37, S41 + S53 - S18, S37 + S20 - S41]
    assert [s.value for s in steps] == pytest.approx(expected)
    assert [s.order for s in steps][-1] == (5, 2, 6, 3, 4, 1)


def test_insert_split_steps_by_hand(hand):
    """Einfügereihenfolge nach Entfernung vom Depot: 1, 4, 6, 3, 2, 5. Teilfolge-Split je Schritt aus Wurzeln:
    (1): 2 sqrt72; (4 1): eine Route sqrt72 + sqrt37 + 7; (6 4 1): Route (6) + Route (4 1); (3 6 4 1): Route (3 6) + Route (4 1); (3 6 2 4 1): Route (3 6 2) + Route (4 1)."""
    steps = K.construct("insert_split", hand).steps
    assert [(s.customer, s.position) for s in steps] == [(1, 0), (4, 0), (6, 0), (3, 0), (2, 2), (5, 0)]
    r41 = S72 + S37 + 7
    assert steps[0].value == pytest.approx(2 * S72)
    assert steps[1].value == pytest.approx(r41)
    assert steps[2].value == pytest.approx(2 * S45 + r41)
    assert steps[3].value == pytest.approx((S32 + S53 + S45) + r41)
    assert steps[4].value == pytest.approx((S32 + S53 + S20 + S29) + r41)
    assert steps[5].value == pytest.approx(OPTIMUM)
    assert [len(s.alternatives) for s in steps] == [1, 2, 3, 4, 5, 5]           # höchstens fünf sichtbar, 6 Stellen im letzten Schritt
    assert [s.evaluated for s in steps] == [1, 2, 3, 4, 5, 6]


def test_counts_of_evaluated_candidates_by_hand(hand):
    """n = 6: Nächster Nachbar 6 + 5 + ... + 1 = 21; Nach Split und Einfügen nach Split ebenso 21; fernstes Einfügen 6 (Start) + 2 + 3 + 4 + 5 + 6 Stellen = 26;
    billigstes Einfügen 6 + 5·2 + 4·3 + 3·4 + 2·5 + 1·6 = 56 (Kunden mal Stellen der wachsenden Rundreise)."""
    counts = {key: K.construct(key, hand).evaluated for key in ("nn", "nn_split", "insert_split", "farthest", "cheapest")}
    assert counts == {"nn": 21, "nn_split": 21, "insert_split": 21, "farthest": 26, "cheapest": 56}


def test_nearest_neighbour_alternatives_are_the_five_nearest(hand):
    first = K.construct("nn", hand).steps[0]
    assert first.customer == 5 and first.value == pytest.approx(S2)
    assert [label for label, _ in first.alternatives] == ["Kunde 5", "Kunde 2", "Kunde 3", "Kunde 6", "Kunde 4"]   # 1,41 / 5,39 / 5,66 / 6,71 / 7,00; Kunde 1 (8,49) fällt heraus


def test_step_records_split_and_length_of_the_partial_order(hand):
    c = K.construct("nn", hand)
    assert c.steps[0].split_cost == pytest.approx(2 * S2) and c.steps[0].length == pytest.approx(2 * S2)
    assert c.steps[-1].split_cost == pytest.approx(TABLE["nn"][2]) and c.steps[-1].length == pytest.approx(TABLE["nn"][1])


def test_unknown_constructor_is_an_error(hand):
    with pytest.raises(KeyError):
        K.construct("savings", hand)
