"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 12, 8
ENUM_MAX = 8                                  # bis hierher werden alle n! Reihenfolgen aufgezählt (Experiment 3)
SEED_MAX, DEFAULT_SEED = 999999, 5
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL = 0.9                                    # Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl * FILL)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)")
FAMILY_KEYS = ("small", "random", "clustered")
DEFAULT_FAMILY = 1
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0

# Erzeuger: Schlüssel, Name, Art (Maß beim Bauen)
KEYS = ("random", "nn", "cheapest", "farthest", "nn_split", "insert_split")
NAMES = {
    "random": "Zufall",
    "nn": "Nächster Nachbar",
    "cheapest": "Billigstes Einfügen",
    "farthest": "Fernstes Einfügen",
    "nn_split": "Nächster Nachbar nach Split",
    "insert_split": "Einfügen nach Split",
}
LENGTH_KEYS = ("nn", "cheapest", "farthest")  # längenorientierte Erzeuger
SPLIT_KEYS = ("nn_split", "insert_split")     # nach Split bewertete Erzeuger
DEFAULT_CONSTRUCTOR = 5                       # Index in KEYS: Einfügen nach Split
TOL = 1e-9                                    # Gleichstände und Optimum-Treffer: absolut
TIE = 1e-12                                   # Verbesserung beim Einfügen nur, wenn um mehr als TIE besser
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt

BAND_SEEDS_EXACT = tuple(range(300000, 300020))   # n = 10, 12: 20 feste Instanzen je Zelle
BAND_SEEDS_REF = tuple(range(300000, 300008))     # n = 25, 50: 8 feste Instanzen je Zelle
BAND_SIZES = (10, 12, 25, 50)
EXACT_SIZES = (10, 12)
BAND_ROUTES = 3
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))      # (Familie, Depotlage): zufällig/Gruppen mal Mitte/Ecke
BAND_FILE = "rte_bands.json"
SCATTER_POINTS = 4000                         # so viele Reihenfolgen werden im Streudiagramm gezeichnet; die Zahlen nutzen alle

COLOR_LEN = "#4c78a8"
COLOR_SPLIT = "#2F6B65"
COLOR_OPT = "#c0504d"
COLOR_TSP = "#7b5ea7"
COLOR_OTHER = "rgba(150,150,150,0.35)"
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b")
KEY_COLORS = {"random": "#999999", "nn": "#4c78a8", "cheapest": "#7aa6d1", "farthest": "#1f4e8c", "nn_split": "#d8a13a", "insert_split": "#2F6B65"}

PRESETS = {
    "Länge gegen Split (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "seed": 5, "constructor": 5},
    "Länge und Split gehen auseinander (n = 8)": {"n": 8, "family": 2, "depot": 1, "routes": 3, "seed": 5, "constructor": 5},
    "Anhängen nach Split scheitert (n = 10)": {"n": 10, "family": 1, "depot": 0, "routes": 3, "seed": 2, "constructor": 4},
    "Alle Erzeuger nahe beieinander (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "seed": 7, "constructor": 5},
    "Einfügen nach Split verliert (n = 8)": {"n": 8, "family": 2, "depot": 1, "routes": 3, "seed": 16, "constructor": 5},
    "Größere Instanz (n = 12)": {"n": 12, "family": 2, "depot": 1, "routes": 3, "seed": 22, "constructor": 5},
}
PRESET_HELP = {
    "Länge gegen Split (n = 8)": "Das fernste Einfügen baut hier genau die kürzeste Rundreise, ihr Split liegt 3,9 % über dem Optimum; Einfügen nach Split trifft das Optimum, obwohl seine Rundreise 12,8 % länger ist.",
    "Länge und Split gehen auseinander (n = 8)": "Kunden in Gruppen, Depot in der Ecke: Die Rangkorrelation zwischen Länge und Split über alle 40 320 Reihenfolgen ist nur 0,14; das fernste Einfügen liegt 19,7 % über dem Optimum.",
    "Anhängen nach Split scheitert (n = 10)": "Nächster Nachbar nach Split liegt 23,2 % über dem Optimum, der gewöhnliche Nächste Nachbar nur 4,3 %: Das Maß hilft nur, wenn die Stelle frei wählbar ist.",
    "Alle Erzeuger nahe beieinander (n = 8)": "Alle Erzeuger außer dem Zufall liegen höchstens 1,0 % über dem Optimum: Hier ist es egal, wie man baut.",
    "Einfügen nach Split verliert (n = 8)": "Hier liegt Einfügen nach Split 15,0 % über dem Optimum, das fernste Einfügen trifft es: Das Maß „Split“ ist kein Garant.",
    "Größere Instanz (n = 12)": "Zwölf Kunden: Einfügen nach Split trifft das Optimum, die drei längenorientierten Erzeuger liegen etwa 21 % darüber.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge, euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.

**Grenzen**
- Live rechnet die App bis zu 12 Kunden mit exaktem Optimum, alle Reihenfolgen werden nur bis 8 Kunden aufgezählt. Die Bänder gelten für 10, 12, 25 und 50 Kunden an je 20 (n = 10, 12) beziehungsweise 8 (n = 25, 50) festen Instanzen je Zelle mit drei Zielrouten.
- Bei 25 und 50 Kunden ist die Referenz eine Lösung von PyVRP (5 Sekunden je Instanz), keine bewiesene Untergrenze; ein Abstand unter null zählt als null.
- Die Erzeuger sind eigene Fassungen nach dem Muster der Literatur (Start mit dem entferntesten Kunden, Gleichstände nach kleinerer Nummer und kleinerer Stelle), nicht deren Originalimplementierungen.
- Maß der Rundreise ist ihre Länge ohne Rücksicht auf die Kapazität; die Garantien der Literatur (Rosenkrantz u. a.) gelten für diese Länge, nicht für den Split.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über feste Instanzen, keine Trends und keine Aussagen über andere Kartenarten oder andere Zielroutenzahlen.
- „Einfügen nach Split“ ist hier ein selbst gebautes Verfahren; ob es unter anderem Namen in der Literatur steht, wurde nicht geprüft.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft."""
