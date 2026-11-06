"""Aufbau der App: Abschnitte, Diagramme, Verdikte; Erzeuger-Auswahl, Schritt-Regler, Vergleich, Band-Auswahl, Permalink und PDF (AppTest, DEMO-PLAYBOOK §5).

Expander werden per Titel gesucht, nie per Index (neue Expander verschieben sonst die Positionen)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rte_constants as C
import rte_evaluation as ev
from rte_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SUBHEADERS = ["🔬 Ein Erzeuger Schritt für Schritt", "🔬 Die Erzeuger im Vergleich", "🔬 Länge gegen Split", "🔬 Wie gut sind die Erzeuger?", "🚧 Wo die Annahmen enden"]


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    """Alle Verdikt-Texte der Seite (Erfolg, Info, Warnung) in einem String."""
    return " ".join(m.value for group in (at.success, at.info, at.warning) for m in group)


def _messages(at) -> int:
    return len(at.success) + len(at.info) + len(at.warning) + len(at.error)


def test_sections_charts_and_verdicts_are_all_there():
    at = _app()
    assert [s.value for s in at.subheader] == SUBHEADERS
    assert len(at.get("plotly_chart")) == 7                    # zwei Karten im Ergebnis, Schritt-Karte, zwei Vergleichskarten, Streudiagramm, Bänder
    assert _messages(at) == 6                                  # gewählter Erzeuger, Kernfrage, Schritte, Vergleich, Streudiagramm, Bänder
    labels = [e.label for e in at.expander]
    for wanted in ("So bauen die Erzeuger eine Riesentour", "⚠️ Annahmen, Grenzen und bekannte Probleme", "📐 Mathematische Formulierung"):
        assert wanted in labels


def test_metrics_show_optimum_and_the_two_splits_with_consistent_deltas():
    at = _app()
    assert [m.value for m in at.metric][:3] == ["450,33", "450,33", "467,81"]       # Voreinstellung: Optimum, Einfügen nach Split, Split der kürzesten Rundreise
    assert at.metric[1].delta == "+0,00 gegen Optimum" and at.metric[2].delta == "+17,48 gegen Optimum"   # 467,81 - 450,33 aus den angezeigten Werten


@pytest.mark.parametrize("index", range(len(C.KEYS)))
def test_every_constructor_runs_and_is_named_in_the_metric(index):
    at = _app()
    at.sidebar.selectbox(key="constructor_select").set_value(index).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.metric[1].label == f"Split: {C.NAMES[C.KEYS[index]]}"
    assert _messages(at) == 6


def test_step_slider_walks_through_the_trace_and_resets_with_the_instance():
    at = _app()
    at.slider(key="step_slider_8_5").set_value(8).run()
    assert not at.exception
    assert any("Schritt 8 von 8" in m.value for m in at.markdown)
    at.sidebar.slider(key="n_slider").set_value(7).run()
    assert not at.exception and any("Schritt 1 von 7" in m.value for m in at.markdown)      # neuer Regler mit eigenem Schlüssel: kein Wert außerhalb der Grenzen


def test_comparison_selectboxes_change_the_verdict():
    at = _app()
    at.selectbox(key="cmp_first").set_value("random").run()
    at.selectbox(key="cmp_second").set_value("nn").run()
    assert not at.exception
    assert "Zufall: Länge" in _texts(at) and "Nächster Nachbar: Länge" in _texts(at)


def test_larger_instances_replace_the_scatter_by_a_hint():
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(9).run()
    assert not at.exception
    assert len(at.get("plotly_chart")) == 6 and "Ab n = 9" in _texts(at)
    assert _messages(at) == 6


def test_band_selection_switches_between_the_four_sizes():
    at = _app()
    assert "Bei n = 10" in _texts(at)
    for n in (12, 25, 50):
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception and f"Bei n = {n}" in _texts(at)
    assert any("PyVRP" in c.value for c in at.caption)
    assert "zur Referenz PyVRP" in _texts(at)


def test_permalink_sets_the_controls_from_the_address():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["n"] = "6"
    at.query_params["seed"] = "3"
    at.query_params["constructor"] = "2"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="n_slider").value == 6 and at.sidebar.number_input(key="seed_input").value == 3
    assert at.sidebar.selectbox(key="constructor_select").value == 2


def test_pdf_export_has_a_pdf_header():
    s = ev.Settings()
    data = build_pdf(s, ev.analyse(s))
    assert data[:5] == b"%PDF-" and len(data) > 1500
