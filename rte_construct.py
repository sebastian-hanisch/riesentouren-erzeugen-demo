"""Die sechs Erzeuger von Riesentouren, jeder mit einer Spur (Schritt für Schritt), nur numpy/Standardbibliothek.

Längenorientiert (die Rundreise durch Depot und alle Kunden soll kurz werden):
  nn        Nächster Nachbar: vom letzten Kunden (am Anfang vom Depot) zum nächsten noch nicht besuchten
  cheapest  Billigstes Einfügen: Kunde und Stelle mit der kleinsten Längenzunahme; Start mit dem Kunden am weitesten vom Depot
  farthest  Fernstes Einfügen: der Kunde am weitesten von der bisherigen Rundreise, an der Stelle mit der kleinsten Längenzunahme; gleicher Start
Nach Split bewertet (dieselben Bausteine, aber gemessen an den Split-Kosten der Teilfolge, siehe rte_algorithm.split):
  nn_split      Nächster Nachbar nach Split: hängt den Kunden an, der die Split-Kosten der Teilfolge am wenigsten erhöht
  insert_split  Einfügen nach Split: Kunden in absteigender Entfernung vom Depot, jeder an der Stelle mit den kleinsten Split-Kosten
Maßstab: random, eine zufällige Reihenfolge (Seed).

Gleichstände: bei Kunden die kleinere Nummer, bei Stellen die kleinere Stelle. Eine Stelle p heißt: vor den p-ten Kunden der bisherigen Folge (0 = ganz vorn,
Länge der Folge = ganz hinten). Beim Einfügen zählt ein Kandidat nur dann als besser, wenn er um mehr als TIE besser ist; beim Anhängen nach Split gewinnt der kleinste Wert,
bei exakt gleichem Wert der kleinere Kunde."""

from dataclasses import dataclass

import rte_algorithm as A
import rte_constants as C
from rte_scenario import Instance, distance_matrix

SHOWN = 5   # so viele Kandidaten (die billigsten) bleiben in der Spur sichtbar


@dataclass(frozen=True)
class Step:
    customer: int                                   # der in diesem Schritt gesetzte Kunde
    position: int                                   # Stelle in der Folge VOR dem Schritt (0 = vorn, len = hinten)
    value: float                                    # Wert des gewählten Kandidaten (Maß: Construction.metric)
    alternatives: tuple[tuple[str, float], ...]     # die bis zu SHOWN billigsten Kandidaten (Beschriftung, Wert), der gewählte steht darunter
    evaluated: int                                  # Zahl der bewerteten Kandidaten in diesem Schritt
    order: tuple[int, ...]                          # Folge nach dem Schritt
    split_cost: float                               # Split-Kosten dieser Teilfolge
    length: float                                   # Länge der Rundreise Depot - Teilfolge - Depot


@dataclass(frozen=True)
class Construction:
    key: str
    metric: str
    order: tuple[int, ...]
    steps: tuple[Step, ...]

    @property
    def evaluated(self) -> int:
        return sum(s.evaluated for s in self.steps)


def _step(inst: Instance, customer, position, value, alternatives, evaluated, order) -> Step:
    top = tuple(sorted(alternatives, key=lambda t: t[1])[:SHOWN])
    return Step(customer, position, float(value), tuple((label, float(v)) for label, v in top), evaluated, tuple(order),
                A.split(inst, order).cost, A.route_length(inst, order))


def _farthest_first(inst: Instance):
    D = distance_matrix(inst)
    far = max(range(1, inst.n + 1), key=lambda c: (D[0][c], -c))
    alternatives = [(f"Kunde {c}", float(D[0][c])) for c in range(1, inst.n + 1)]
    return far, D[0][far], sorted(alternatives, key=lambda t: -t[1])[:SHOWN], inst.n


# ----------------------------------------------------------------------------------------------------------------------------------- Erzeuger

def construct_random(inst: Instance, seed: int) -> Construction:
    order = A.random_order(inst, seed)
    steps = tuple(_step(inst, c, k, 0.0, [], 0, order[:k + 1]) for k, c in enumerate(order))
    return Construction("random", "Zufall (kein Maß)", order, steps)


def construct_nn(inst: Instance) -> Construction:
    D = distance_matrix(inst)
    left = set(range(1, inst.n + 1))
    current, order, steps = 0, (), []
    while left:
        cand = [(f"Kunde {c}", float(D[current][c]), c) for c in sorted(left)]
        label, value, c = min(cand, key=lambda t: (t[1], t[2]))
        order += (c,)
        steps.append(_step(inst, c, len(order) - 1, value, [(a, b) for a, b, _ in cand], len(cand), order))
        left.remove(c)
        current = c
    return Construction("nn", "Abstand zum letzten Kunden", order, tuple(steps))


def _insertion(inst: Instance, key: str) -> Construction:
    """Gemeinsamer Rumpf von billigstem und fernstem Einfügen: eine Rundreise 0 - Kunden - 0, in die der Reihe nach Kunden gesetzt werden."""
    D = distance_matrix(inst)
    far, d_far, alts, evaluated = _farthest_first(inst)
    tour = [0, far]
    steps = [_step(inst, far, 0, d_far, alts, evaluated, tour[1:])]
    left = set(range(1, inst.n + 1)) - {far}
    while left:
        def added(c):  # (Längenzunahme, Stelle) für jede Stelle
            out = []
            for k in range(len(tour)):
                a, b = tour[k], tour[(k + 1) % len(tour)]
                out.append((float(D[a][c] + D[c][b] - D[a][b]), k))
            return out
        if key == "cheapest":
            best = None
            cand = []
            for c in sorted(left):
                for value, k in added(c):
                    cand.append((f"Kunde {c} an Stelle {k}", value))
                    if best is None or value < best[0] - C.TIE:
                        best = (value, c, k)
            value, pick, pos = best
            evaluated = len(cand)
        else:
            pick = max(sorted(left), key=lambda c: (min(D[c][t] for t in tour), -c))
            best = None
            cand = []
            for value, k in added(pick):
                cand.append((f"Kunde {pick} an Stelle {k}", value))
                if best is None or value < best[0] - C.TIE:
                    best = (value, k)
            value, pos = best
            evaluated = len(cand)
        tour.insert(pos + 1, pick)
        left.remove(pick)
        steps.append(_step(inst, pick, pos, value, cand, evaluated, tour[1:]))
    metric = "Längenzunahme der Rundreise" if key == "cheapest" else "Längenzunahme der Rundreise (fernster Kunde)"
    return Construction(key, metric, tuple(tour[1:]), tuple(steps))


def construct_nn_split(inst: Instance) -> Construction:
    left = set(range(1, inst.n + 1))
    order, steps = (), []
    while left:
        cand = [(f"Kunde {c}", A.split(inst, order + (c,)).cost, c) for c in sorted(left)]
        label, value, c = min(cand, key=lambda t: t[1])
        steps.append(_step(inst, c, len(order), value, [(a, b) for a, b, _ in cand], len(cand), order + (c,)))
        order += (c,)
        left.remove(c)
    return Construction("nn_split", "Split-Kosten der Teilfolge", order, tuple(steps))


def construct_insert_split(inst: Instance) -> Construction:
    D = distance_matrix(inst)
    sequence = sorted(range(1, inst.n + 1), key=lambda c: (-D[0][c], c))
    order, steps = (), []
    for c in sequence:
        best = None
        cand = []
        for p in range(len(order) + 1):
            trial = order[:p] + (c,) + order[p:]
            cost = A.split(inst, trial).cost
            cand.append((f"Stelle {p}", cost))
            if best is None or cost < best[0] - C.TIE:
                best = (cost, p, trial)
        value, pos, order = best
        steps.append(_step(inst, c, pos, value, cand, len(cand), order))
    return Construction("insert_split", "Split-Kosten der Teilfolge", order, tuple(steps))


def construct(key: str, inst: Instance, seed: int = 0) -> Construction:
    if key == "random":
        return construct_random(inst, seed)
    if key == "nn":
        return construct_nn(inst)
    if key in ("cheapest", "farthest"):
        return _insertion(inst, key)
    if key == "nn_split":
        return construct_nn_split(inst)
    if key == "insert_split":
        return construct_insert_split(inst)
    raise KeyError(key)
