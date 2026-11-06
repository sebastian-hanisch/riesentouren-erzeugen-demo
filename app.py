"""Riesentouren erzeugen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 2 der Reihe „Tourenbildung“: Sechs Erzeuger bauen eine Riesentour (eine Reihenfolge aller Kunden), die der Split aus Stück 1 optimal in Routen zerlegt.
Die Demo vergleicht, ob man beim Bauen die Länge der Rundreise oder die Split-Kosten der Teilfolge messen sollte.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rte_algorithm as A
import rte_constants as C
from rte_evaluation import (
    Settings,
    analyse,
    band_cells,
    de,
    merge_stats,
    num,
    order_text,
    pct,
    routes_word,
    scatter_data,
    verdict_bands,
    verdict_compare,
    verdict_constructor,
    verdict_core,
    verdict_scatter,
    verdict_trace,
)
from rte_layout import dunkles_design, kopf_css
from rte_pdf_export import build_pdf
from rte_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from rte_visualization import build_bands, build_map, build_scatter

st.set_page_config(page_title="Riesentouren erzeugen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _scatter(settings):
    return scatter_data(settings)


@st.cache_data(show_spinner=False)
def _bands(n):
    return merge_stats(band_cells(n)) if band_cells(n) else {}


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in rte_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🏗️ Riesentouren erzeugen")
st.markdown(
    """
**Wie baut man eine gute Reihenfolge?** Eine **Riesentour** ist eine Reihenfolge aller Kunden; der **Split** aus Stück 1 zerlegt sie optimal in Routen.
Sechs **Erzeuger** bauen solche Reihenfolgen: der Zufall als Maßstab, drei Verfahren, die die **Länge der Rundreise** kurz halten (Nächster Nachbar, billigstes und fernstes Einfügen),
und zwei, die an den **Split-Kosten** der Teilfolge messen. Die Demo zeigt, was der Split aus jeder Reihenfolge macht, und fragt, ob man beim Bauen die Länge oder den Split messen sollte.

Weiter unten: **🔬 Ein Erzeuger Schritt für Schritt**, **🔬 Die Erzeuger im Vergleich**, **🔬 Länge gegen Split**, **🔬 Wie gut sind die Erzeuger?**,
**🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So bauen die Erzeuger eine Riesentour", expanded=True):
    st.markdown(
        """
1. **Anhängen oder Einfügen:** Der **Nächste Nachbar** hängt immer den nächsten Kunden hinten an. Die **Einfügeverfahren** setzen die Kunden einen nach dem anderen an die beste Stelle einer wachsenden Folge:
   das **billigste Einfügen** wählt Kunde und Stelle mit der kleinsten Längenzunahme der Rundreise, das **fernste Einfügen** den Kunden, der am weitesten von der bisherigen Rundreise liegt.
2. **Länge oder Split als Maß:** Die drei genannten Verfahren messen die **Länge** der Rundreise. **Nächster Nachbar nach Split** und **Einfügen nach Split** messen stattdessen die **Split-Kosten der Teilfolge**:
   Wie billig lassen sich die bisherigen Kunden in Routen zerlegen?
3. **Der Maßstab** ist das exakte Optimum über alle Tourenpläne; **Länge über Rundreise** zeigt, wie viel länger die Reihenfolge ist als die kürzeste Rundreise (Held–Karp).
4. **Was zu sehen sein soll:** Eine kürzere Rundreise ergibt nicht von selbst den billigeren Split, und das Maß allein genügt nicht: Es kommt darauf an, ob die Stelle frei wählbar ist.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.N_MAX} rechnet die App das exakte Optimum; alle Reihenfolgen werden nur bis n = {C.ENUM_MAX} aufgezählt.")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider",
                       help=f"Legt die Kapazität fest: Gesamtnachfrage geteilt durch (Zielroutenzahl mal {C.FILL}), aufgerundet. Die optimale Lösung kann mehr Routen fahren.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1,
                           help="Beim Erzeuger „Zufall“ bestimmt der Seed auch die Reihenfolge.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Erzeuger**")
    constructor = st.selectbox("Gewählter Erzeuger", list(range(len(C.KEYS))), key="constructor_select", format_func=lambda i: C.NAMES[C.KEYS[i]],
                               help="Bestimmt die Reihenfolge im Ergebnis oben und die Schritte in Experiment 1; die Tabelle der Erzeuger zeigt immer alle sechs.")

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "seed_input": int(seed), "constructor_select": int(constructor)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(seed), int(constructor))
a = _analysis(settings)
inst = a.inst
key = C.KEYS[settings.constructor]
chosen = a.results[key]

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: der Split der gebauten Reihenfolge gegen das Optimum")
m1, m2, m3 = st.columns(3)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Optimum (kürzester Plan)", de(a.exact.cost), delta="Referenz", delta_color="off")
m2.metric(f"Split: {C.NAMES[key]}", de(chosen.split.cost), delta=f"{round(chosen.split.cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m3.metric("Split der kürzesten Rundreise", de(a.tour_split.cost), delta=f"{round(a.tour_split.cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")

left, right = st.columns(2)
with left:
    st.markdown(f"**{C.NAMES[key]}: Folge {order_text(chosen.order)}**")
    st.plotly_chart(build_map(inst, chosen.split.routes, chain=chosen.order), width="stretch", key="map_chosen")
with right:
    st.markdown("**Optimum über alle Tourenpläne**")
    st.plotly_chart(build_map(inst, a.exact.routes), width="stretch", key="map_opt")
st.caption(f"Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}, mindestens {inst.min_routes} Routen. Depot: Quadrat; Kunden: Kreise, je größer, desto mehr Nachfrage; "
           "gepunktet die Folge (Rundreise), farbig die Routen des Splits.")
kind, text = verdict_constructor(a)
getattr(st, kind)(text)
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="riesentouren-erzeugen.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Sollte man beim Bauen die Länge oder den Split messen?")
kind, text = verdict_core(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Ein Erzeuger Schritt für Schritt")
construction = a.constructions[key]
st.caption("Welcher Kandidat wird in jedem Schritt gewählt, und woran gemessen? Die Tabelle zeigt die billigsten Kandidaten; „Stelle p“ heißt: vor den p-ten Kunden der bisherigen Folge (0 = ganz vorn).")
step_no = st.slider("Schritt", 1, inst.n, 1, key=f"step_slider_{inst.n}_{settings.constructor}")
step = construction.steps[step_no - 1]
t1, t2 = st.columns([1, 1])
with t1:
    st.markdown(f"**Schritt {step_no} von {inst.n}: Kunde {step.customer} an Stelle {step.position}** (Maß: {construction.metric}, Wert {de(step.value)})")
    if step.alternatives:
        rows = ["| Kandidat | Wert | |", "|---|---|---|"]
        marked = False
        for label, value in step.alternatives:
            mark = "◀ gewählt" if (not marked and abs(value - step.value) < 1e-9) else ""
            marked = marked or bool(mark)
            rows.append(f"| {label} | {de(value)} | {mark} |")
        st.markdown("\n".join(rows))
        st.caption(f"In diesem Schritt wurden {num(step.evaluated)} Kandidaten bewertet; gezeigt sind die {len(step.alternatives)} billigsten.")
    else:
        st.markdown("Der Zufall bewertet nichts: Der Kunde steht an dieser Stelle der zufälligen Reihenfolge.")
    s1, s2 = st.columns(2)
    s1.metric("Split der Teilfolge", de(step.split_cost))
    s2.metric("Länge der Teilfolge", de(step.length))
with t2:
    st.plotly_chart(build_map(inst, A.split(inst, step.order).routes, placed=step.order, chain=step.order), width="stretch", key="map_step")
st.caption("Blass: noch nicht gesetzte Kunden. Gepunktet die Folge als Rundreise, farbig die Routen des Splits der Teilfolge.")
kind, text = verdict_trace(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Die Erzeuger im Vergleich")
st.caption("Alle sechs Erzeuger auf dieser Instanz. „Länge über Rundreise“: Prozent über der kürzesten Rundreise durch Depot und alle Kunden; „Split über Optimum“: Prozent über dem exakten Optimum.")
table = ["| Erzeuger | Folge | Länge | Länge über Rundreise | Split | Split über Optimum | Routen |", "|---|---|---|---|---|---|---|"]
for k in C.KEYS:
    r = a.results[k]
    table.append(f"| **{C.NAMES[k]}** | {order_text(r.order)} | {de(r.length)} | {pct(r.length_gap)} | {de(r.split.cost)} | {pct(r.split_gap)}{' ✅' if r.optimal else ''} | {len(r.split.routes)} |")
st.markdown("\n".join(table))
st.caption(f"Kürzeste Rundreise: Länge {de(a.tour_length)}, Folge {order_text(a.tour_order)}, Split {de(a.tour_split.cost)}. Optimum {de(a.exact.cost)} in {routes_word(len(a.exact.routes))}. ✅: Der Split trifft das Optimum.")
c1, c2 = st.columns(2)
first = c1.selectbox("Erzeuger links", C.KEYS, index=3, key="cmp_first", format_func=lambda k: C.NAMES[k])
second = c2.selectbox("Erzeuger rechts", C.KEYS, index=5, key="cmp_second", format_func=lambda k: C.NAMES[k])
c1.plotly_chart(build_map(inst, a.results[first].split.routes, chain=a.results[first].order), width="stretch", key="map_cmp_first")
c2.plotly_chart(build_map(inst, a.results[second].split.routes, chain=a.results[second].order), width="stretch", key="map_cmp_second")
kind, text = verdict_compare(a, first, second)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Länge gegen Split")
if inst.n > C.ENUM_MAX:
    st.info(f"Ab n = {C.ENUM_MAX + 1} werden nicht mehr alle Reihenfolgen aufgezählt ({num(362880)} bei n = 9). Setzen Sie n in der Seitenleiste auf höchstens {C.ENUM_MAX}; "
            "die vorberechneten Bänder unten decken größere Instanzen ab.")
else:
    data = _scatter(settings)
    st.caption(f"Jeder Punkt ist eine der {num(data['n_orders'])} Reihenfolgen (gezeichnet wird eine Stichprobe von {num(C.SCATTER_POINTS)}, die Zahlen nutzen alle): "
               "nach rechts eine längere Rundreise, nach oben ein teurerer Split. Die Marken sind die sechs Erzeuger und die kürzeste Rundreise.")
    marks = [(C.NAMES[k], a.results[k].length, a.results[k].split.cost, C.KEY_COLORS[k], "circle") for k in C.KEYS]
    marks.append(("Kürzeste Rundreise", a.tour_length, a.tour_split.cost, C.COLOR_TSP, "star"))
    st.plotly_chart(build_scatter(data, marks), width="stretch", key="scatter_chart")
    kind, text = verdict_scatter(data)
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Wie gut sind die Erzeuger?")
band_n = st.radio("Kunden n", list(C.BAND_SIZES), horizontal=True, key="band_n",
                  help="Feste Instanzen, vorberechnet (generate_precomputed.py): n = 10 und 12 gegen das exakte Optimum, n = 25 und 50 gegen eine Lösung von PyVRP.")
stats = _bands(int(band_n))
if stats:
    st.caption(f"Je {stats['count'] // 4} feste Instanzen je Zelle (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke, drei Zielrouten), alle vier Zellen zusammen ({stats['count']} Instanzen). "
               + ("Referenz: das exakte Optimum." if stats["reference"] == "exact" else "Referenz: PyVRP, 5 Sekunden je Instanz, keine bewiesene Untergrenze; ein Abstand unter null zählt als null.")
               + " Die Zahlen sind Spannen über Instanzen, kein Satz.")
    st.plotly_chart(build_bands(stats["by_key"]), width="stretch", key="band_chart")
    exact = stats["reference"] == "exact"
    head = "| Erzeuger | Abstand Median | Minimum bis Maximum | Mittel | " + ("Optimum erreicht | Länge über Rundreise, Median |" if exact else "Referenz erreicht oder unterboten |")
    table = [head, "|---|---|---|---|---|" + ("---|" if exact else "")]
    for k in C.KEYS:
        e = stats["by_key"][k]
        row = f"| **{C.NAMES[k]}** | {pct(e['median'])} | {pct(e['min'])} bis {pct(e['max'])} | {pct(e['mean'])} | {e['optimal']} von {stats['count']} |"
        table.append(row + (f" {pct(e['length_median'])} |" if exact else ""))
    st.markdown("\n".join(table))
    if exact:
        total = stats["agree"] + stats["disagree"]
        st.caption(f"Einigkeit der beiden Maße: In {stats['agree']} von {total} Paaren von Erzeugern ({pct(100.0 * stats['agree'] / total)}) ergibt die kürzere Rundreise auch den billigeren Split.")
kind, text = verdict_bands(stats)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Garantien der Literatur gelten für die Länge** | Rosenkrantz u. a. beschränken die Länge der Rundreise (Nächster Nachbar logarithmisch in n, Einfügen höchstens doppelt so lang wie die kürzeste); für den Split kennt die Demo keine Schranke | Literatur (Abstract gesehen) |
| **Unbegrenzte Flotte** | Mit höchstens *B* Fahrzeugen braucht der Split eine Dimension mehr; die Erzeuger bleiben, die Zahlen ändern sich | Stück 3 (Flottengrenze) |
| **Nur Kapazität, keine Zeitfenster** | Mit Zeitfenstern braucht der Hilfsgraph Etiketten, das Einfügen eine Zeitprüfung | Stück 8 (Zeitfenster) |
| **Bänder nur für drei Zielrouten** | Kürzere Routen (mehr Zielrouten) und andere Auslastungen wurden nicht gemessen | – |
| **Einfügen nach Split rechnet mehr** | Es bewertet rund n²/2 Teilfolgen mit je einem Split (n = 8: 36); für große Instanzen wächst der Aufwand schneller als bei den längenorientierten Erzeugern | Stück 11 (Riesentour suchen) |
| **Kein Vergleich mit Savings und Sweep** | Beide sind keine Riesentour-Erzeuger im engen Sinn und folgen in Stück 4 und 6 | Stück 4, Stück 6 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Wie in Stück 1: Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen $d(u, v)$. Eine Riesentour $\pi$ ist eine Reihenfolge aller Kunden, $\mathrm{Split}(\pi)$ die Kosten ihrer optimalen Zerlegung in Routen.

| Symbol | Bedeutung |
|---|---|
| $\pi = (\pi_1, \dots, \pi_k)$ | Folge von Kunden (eine Teilfolge beim Bauen, am Ende alle $n$) |
| $L(\pi)$ | Länge der Rundreise $0 \to \pi_1 \to \dots \to \pi_k \to 0$ |
| $S(\pi)$ | Split-Kosten der Folge $\pi$: kürzester Weg im Hilfsgraphen (Stück 1) |
| $\mathrm{OPT}$, $L^{*}$ | kleinste Gesamtlänge aller zulässigen Tourenpläne; Länge der kürzesten Rundreise durch alle Kunden |

**Anhängen.** Nächster Nachbar: $c^{*} = \arg\min_{c \notin \pi} d(\pi_k, c)$ (am Anfang $\pi_k = 0$). Nach Split: $c^{*} = \arg\min_{c \notin \pi} S(\pi, c)$.

**Einfügen.** Ein Kunde $c$ wird an der Stelle $p$ zwischen $\pi_p$ und $\pi_{p+1}$ eingefügt. Die Längenzunahme ist
$$\Delta_p(c) = d(\pi_p, c) + d(c, \pi_{p+1}) - d(\pi_p, \pi_{p+1}),$$
mit $\pi_0 = \pi_{k+1} = 0$. Billigstes Einfügen wählt $(c, p)$ mit kleinstem $\Delta_p(c)$; fernstes Einfügen wählt zuerst $c^{*} = \arg\max_{c \notin \pi} \min_{u \in \{0\} \cup \pi} d(c, u)$ und dann die Stelle mit kleinstem $\Delta_p(c^{*})$.
Einfügen nach Split nimmt die Kunden in absteigender Entfernung vom Depot und wählt die Stelle mit kleinstem $S(\pi \text{ mit } c \text{ an Stelle } p)$.

**Abstände.** $\text{Split über Optimum} = 100 \cdot \max\big(0, \tfrac{S(\pi)}{\mathrm{OPT}} - 1\big)$ und $\text{Länge über Rundreise} = 100 \cdot \big(\tfrac{L(\pi)}{L^{*}} - 1\big)$. Bei den größeren Instanzen steht statt $\mathrm{OPT}$ die Referenz von PyVRP.

**Rangkorrelation.** Über alle $n!$ Reihenfolgen: die Korrelation (Pearson) der Ränge von $L(\pi)$ und $S(\pi)$. Exakt gleiche Werte erhalten den mittleren Rang; bei reellen Längen sind sie selten.

**Zählung der bewerteten Kandidaten.** Nächster Nachbar nach Split und Einfügen nach Split bewerten $\sum_{k=1}^{n} k = n(n+1)/2$ Teilfolgen; der Nächste Nachbar bewertet ebenso viele Entfernungen.

**Literatur.** Rosenkrantz, Stearns und Lewis (1977), „An analysis of several heuristics for the traveling salesman problem“: laut Abstract wächst das Güteverhältnis des Nächsten Nachbarn nach oben und unten logarithmisch in $n$, nächstes und billigstes Einfügen sind bei Dreiecksungleichung höchstens um den Faktor 2 länger als die kürzeste Rundreise. Die Quelle wurde nur auf Abstract-Ebene gesehen; die Demo übernimmt keine Zahl daraus. Der Split als Zerlegung einer Riesentour geht laut Sekundärquellen auf Beasley (1983) und Prins (2004) zurück (nicht im Volltext geprüft). „Einfügen nach Split“ ist ein selbst gebautes Verfahren.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
