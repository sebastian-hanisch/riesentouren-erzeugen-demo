"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import rte_constants as C
from rte_evaluation import Analysis, Settings, de, order_text, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Riesentouren erzeugen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Seed {s.seed}. "
                            f"Kapazität {a.inst.capacity}, Gesamtnachfrage {sum(a.inst.demand)}. Optimum {de(a.exact.cost)}, kürzeste Rundreise {de(a.tour_length)}. Alles simuliert."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (52, 40, 22, 28, 22, 26)
    pdf.set_font("Helvetica", "B", 8)
    for w, h in zip(widths, ("Erzeuger", "Folge", "Länge", "Länge über", "Split", "Split über")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for key in C.KEYS:
        r = a.results[key]
        for w, v in zip(widths, (C.NAMES[key], order_text(r.order), de(r.length), pct(r.length_gap), de(r.split.cost), pct(r.split_gap))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Länge über: Prozent über der kürzesten Rundreise; Split über: Prozent über dem Optimum. Der Split zerlegt eine Reihenfolge per kürzestem Weg im Hilfsgraphen "
                            "optimal in Routen. Quelle: riesentouren-erzeugen-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
