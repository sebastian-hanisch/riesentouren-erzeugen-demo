# Riesentouren erzeugen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-riesentouren-erzeugen-demo.streamlit.app/)** -->

Zweites Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt, und dass die kürzeste Rundreise dafür keine gute Wahl sein muss. Dieses Stück fragt, wie man eine gute Reihenfolge **baut**, und ob man beim Bauen die Länge der Rundreise oder die Split-Kosten messen sollte.

## Kernfrage

Sechs Erzeuger bauen Riesentouren: der Zufall als Maßstab, **Nächster Nachbar**, **billigstes** und **fernstes Einfügen** (alle drei halten die Länge der Rundreise kurz) sowie **Nächster Nachbar nach Split** und **Einfügen nach Split** (beide messen an den Split-Kosten der Teilfolge). Die Demo vergleicht sie auf einer Instanz mit dem exakten Optimum, geht einen Erzeuger Schritt für Schritt durch, zeichnet Länge gegen Split über alle Reihenfolgen und zeigt Bänder über feste Instanzen bis 50 Kunden.

## Modell

Wie in Stück 1: ein Depot, n Kunden mit ganzzahliger Nachfrage, beliebig viele gleiche Fahrzeuge der Kapazität Q, euklidische Entfernungen. Der Split einer Folge ist der kürzeste Weg im Hilfsgraphen (Stück 1). **Anhängen:** der Nächste Nachbar hängt den nächsten Kunden hinten an, der Nächste Nachbar nach Split den Kunden, der die Split-Kosten der Teilfolge am wenigsten erhöht. **Einfügen:** Kunden werden einer nach dem anderen an die beste Stelle einer wachsenden Folge gesetzt; billigstes Einfügen wählt Kunde und Stelle mit der kleinsten Längenzunahme der Rundreise, fernstes Einfügen den Kunden, der am weitesten von der bisherigen Rundreise liegt, Einfügen nach Split die Stelle mit den kleinsten Split-Kosten (Kunden in absteigender Entfernung vom Depot). Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Erzeuger** (`rte_construct.py`): jeder mit einer Spur (Kandidaten, gewählte Stelle, Split und Länge der Teilfolge, Zahl der bewerteten Kandidaten). Gleichstände: kleinere Kundennummer, kleinere Stelle; eine Stelle p heißt „vor den p-ten Kunden der Folge“.
- **Kern** (`rte_algorithm.py`): aus Stück 1 kopiert und umbenannt (Split, Hilfsgraph, exakter Löser über Teilmengen, Held–Karp), ergänzt um Länge und Split-Kosten aller Reihenfolgen und die Rangkorrelation (Spearman, Gleichstände mit mittleren Rängen).
- **Maße:** *Split über Optimum* = Prozent über dem exakten Optimum (bei n = 25 und 50: über einer Lösung von PyVRP); *Länge über Rundreise* = Prozent über der kürzesten Rundreise durch Depot und alle Kunden.
- **Instanzen:** wie in Stück 1 (kleine Karte, zufällig verteilt, in Gruppen; Depot in der Mitte oder in der Ecke; Kapazität aus der Zielroutenzahl).
- **Vier Experimente:** ein Erzeuger Schritt für Schritt, die Erzeuger im Vergleich, Länge gegen Split, Bänder über feste Instanzen.
- **Bänder** (`rte_bands.json`, erzeugt von `generate_precomputed.py`): n = 10 und 12 mit 20 festen Instanzen je Zelle (80 gesamt, Referenz: exaktes Optimum), n = 25 und 50 mit 8 je Zelle (32 gesamt, Referenz: PyVRP 0.14.1, 5 Sekunden je Instanz, Seed 1, Entfernungen mal 100 gerundet). Vier Zellen: Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke; Zielroutenzahl 3.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Seeds (Median über Instanzen, Abstand in Prozent), nachgerechnet in `tests/test_claims.py`, `tests/test_bands.py` und `tests/test_algorithm.py`. Spalten der Tabelle: n = 10 / 12 / 25 / 50.

| Frage | Befund |
|---|---|
| Wie gut ist der Zufall? | Median **37,3 / 52,5 / 126,9 / 275,7 %** über dem Optimum (der Referenz) |
| Längenorientierte Erzeuger | Median Nächster Nachbar 5,4 / 8,2 / 14,0 / 19,7 %, billigstes Einfügen 3,2 / 4,7 / 9,2 / 15,9 %, fernstes Einfügen 2,3 / 3,8 / 6,8 / 10,4 %; in allen vier Größen ist die Reihenfolge Nächster Nachbar > billigstes > fernstes Einfügen. Optimum erreicht bei n = 10 / 12: Nächster Nachbar 1 / 3, billigstes Einfügen 6 / 5, fernstes Einfügen 6 / 3 von je 80; Maxima bei n = 12: 23,7 / 28,1 / 30,7 % |
| **Einfügen nach Split** | Median **0,0 / 0,6 / 3,3 / 8,3 %**, Optimum bei n = 10 in **40 von 80**, bei n = 12 in **32 von 80**; Maximum 10,0 / 15,3 / 18,8 / 17,4 %, Mittel 1,1 / 1,8 / 5,1 / 9,1 %. Gegen das fernste Einfügen (den besten längenorientierten Erzeuger im Median) ist der Unterschied 2,3 / 3,2 / 3,5 / 2,1 Prozentpunkte |
| Anhängen nach Split | Median Nächster Nachbar nach Split **7,8 / 9,8 / 24,3 / 36,9 %**, in allen vier Größen schlechter als der gewöhnliche Nächste Nachbar (5,4 / 8,2 / 14,0 / 19,7 %); das Optimum trifft er in keiner der je 80 Instanzen bei n = 10 und 12. Das Maß hilft nur, wenn die Stelle frei wählbar ist |
| Wie lang sind die Rundreisen der Erzeuger? | Länge über der kürzesten Rundreise (Median, n = 10 / 12): Zufall 83,6 / 111,4 %, Nächster Nachbar 7,1 / 9,5 %, billigstes Einfügen 1,6 / 3,6 %, fernstes Einfügen 0,0 / 0,0 %, Nächster Nachbar nach Split 20,4 / 24,1 %, **Einfügen nach Split 22,6 / 20,2 %** (Maximum 77,7 / 93,0 %): Die bessere Riesentour hat eine **längere** Rundreise |
| Einigkeit von Länge und Split | In **69,2 %** (n = 10: 791 von 1 143 Paaren) und **70,4 %** (n = 12: 818 von 1 162) aller Paare von Erzeugern ergibt die kürzere Rundreise auch den billigeren Split; in knapp 30 % ist es umgekehrt |
| Zusammenhang über **alle** Reihenfolgen (n = 8, 40 Instanzen, je 40 320 Reihenfolgen) | Rangkorrelation Länge gegen Split: Median **0,74** (0,33 bis 0,97); je Zelle (Kunden zufällig / in Gruppen, Depot Mitte, dann Ecke) 0,91 / 0,85 / 0,62 / 0,54. Die optimalen Reihenfolgen liegen im Median unter den kürzesten **2,3 %** der Rundreisen (0,2 bis 26,5 %) |
| Aufwand | Nächster Nachbar, Nächster Nachbar nach Split und Einfügen nach Split bewerten bei n = 8 je 36 Kandidaten (n(n+1)/2); an der Handinstanz (n = 6): 21, 21, 21, fernstes Einfügen 26, billigstes Einfügen 56 |
| Voreinstellung (n = 8, zufällig verteilt, Depot in der Mitte, Seed 5) | Optimum 450,33 in 3 Routen; kürzeste Rundreise 317,63, ihr Split 467,81 (3,9 % über dem Optimum); fernstes Einfügen baut genau diese Rundreise; **Einfügen nach Split trifft das Optimum** bei einer um 12,8 % längeren Rundreise; Rangkorrelation 0,92, 48 optimale Reihenfolgen unter 40 320 |
| Handinstanz aus Stück 1 (n = 6, Optimum 44,36) | Nächster Nachbar: Länge 41,52, Split 49,45 (+11,5 %); billigstes Einfügen 38,82 / 46,47 (+4,8 %); fernstes Einfügen 38,24 / 47,19 (+6,4 %); Nächster Nachbar nach Split und Einfügen nach Split: 44,14 / 44,36 (+0,0 %), die Reihenfolge 5 3 6 2 4 1 ist 15,4 % länger als die kürzeste Rundreise und 6,3 % länger als die des Nächsten Nachbarn |
| Referenz PyVRP | Keiner der sechs Erzeuger unterbietet die Referenz in einer der 32 Instanzen bei n = 25 und n = 50 (je 192 Paare) |

## Ehrliche Grenzen

- Die Aussagen gelten für die vier gemessenen Größen, drei Zielrouten und die drei Kartenarten; sie sind keine Aussagen über andere Zielroutenzahlen oder echte Daten.
- Bei n = 25 und 50 ist die Referenz eine Lösung von PyVRP (5 Sekunden), keine bewiesene Untergrenze; die Läufe sind zeitgesteuert und nicht bitgleich wiederholbar.
- Der Unterschied zwischen Einfügen nach Split und fernstem Einfügen bleibt, ist aber bei n = 50 klein (2,1 Prozentpunkte im Median); die Demo macht keine Trendaussage.
- Die Erzeuger sind eigene Fassungen nach dem Muster der Literatur, nicht deren Originalimplementierungen; „Einfügen nach Split“ ist ein selbst gebautes Verfahren, dessen Stand in der Literatur nicht geprüft wurde.
- Die Garantien von Rosenkrantz, Stearns und Lewis (1977) gelten laut Abstract für die **Länge** der Rundreise, nicht für den Split; die Quelle wurde nur auf Abstract-Ebene gesehen.
- Einfügen nach Split rechnet merklich länger als die längenorientierten Erzeuger (in reinem Python bei 100 Kunden im Bereich von Sekunden); Zeiten sind nicht festgeschrieben.
- Savings (Stück 4) und Sweep (Stück 6) fehlen bewusst; auf kleinen Instanzen (n ≤ 12) lag Savings in der Vormessung auf derselben Höhe wie Einfügen nach Split.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
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
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Größere Instanzen neu gerechnet:** Die Referenzen für n = 25 und 50 wurden für die Demo mit PyVRP noch einmal gerechnet (5-Sekunden-Läufe sind zeitgesteuert, nicht bitgleich). Gegenüber der Vormessung änderten sich nur Randzahlen: Nächster Nachbar bei n = 50 Median 19,7 statt 19,3 %, Einfügen nach Split dort Minimum 1,5 statt 0,0 % und Mittel 9,1 statt 9,0 %. Die Zahlen für n = 10, 12 und 25 stimmen mit der Vormessung überein.
- **Stelle in der Spur:** Der Plan zählte Stellen in der Rundreise mit Depot (Kunde 5 „an Stelle 1“); die Demo zählt in der Folge der Kunden (0 = ganz vorn), die Einfügeschritte des billigsten Einfügens an der Handinstanz sind daher 0, 1, 1, 1, 1.
- **Rangkorrelation mit mittleren Rängen:** Ein Eigenschaftstest fand, dass die Vormessung bei konstanter Eingabe eine Korrelation von 1 lieferte (stabile Ränge ohne Mittelung); die Demo mittelt Ränge bei exakten Gleichständen. Die Zahlen der Vormessung bleiben auf zwei Stellen gleich.
- **Anteil der kürzesten 1 %:** Die Vormessung nannte, dass von den kürzesten 1 % der Rundreisen im Median nur 37,6 % höchstens 5 % über dem Optimum liegen; die Demo zeigt stattdessen das Perzentil der optimalen Reihenfolgen (Median 2,3 %).
- **Savings und Sweep** bleiben, wie geplant, Stück 4 und 6; die Vormessung (Savings gegen Einfügen nach Split gleichauf bei n ≤ 12) steht nur qualitativ unter „Ehrliche Grenzen“.

## Verifikation

- **Kern und Erzeuger:** Handwerte aus Wurzeln für die fünf Erzeuger der Handinstanz, die Einfügeschritte, die Zählung der bewerteten Kandidaten (`tests/test_algorithm.py`).
- **Orakel:** jeder Erzeuger noch einmal in reinem Python mit neu gesuchtem Argmin je Schritt (60 Instanzen je Erzeuger), Split der Teilfolgen über die Aufzählung aller Schnittmengen, Kern (Split, exakter Löser, Rundreise, vektorisierter Split) gegen Aufzählung (`tests/test_oracle_riesentouren_erzeugen.py`).
- **Eigenschaften:** Permutation, deterministisch, Split der Teilfolgen nie fallend, nie unter Optimum und kürzester Rundreise, billigstes Einfügen höchstens doppelt so lang wie die kürzeste Rundreise, Verschieben, Skalieren, Umnummerieren, Rangkorrelation (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Kunden, alle Kunden an einem Ort, Kunde auf dem Depot, Nachfrage gleich Kapazität, Gleichstände, Reglergrenzen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Schwelle und jede Zahl im Text an gesetzten Werten (`tests/test_verdicts.py`).
- **Zahlen der README:** `tests/test_claims.py`; die vorberechneten Bänder gegen eine frische Rechnung je Größe (`tests/test_bands.py`, die PyVRP-Referenzen aus der Datei).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Aufbau, jeder Erzeuger, Schritt-Regler, Vergleich, Band-Auswahl, Permalink, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

998 Tests. Laufzeit lokal etwa ein bis zwei Minuten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `rte_bands.json` (exakte Referenz für n = 10, 12; PyVRP optional für n = 25, 50; rund 15 Minuten) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `rte_algorithm.py` | Kern aus Stück 1 (Split, exakter Löser, Held–Karp) plus Längen aller Reihenfolgen und Rangkorrelation |
| `rte_bands.json` | vorberechnete Bänder (4 Größen × 4 Zellen, Kosten je Instanz und Erzeuger) |
| `rte_constants.py` | Regler-Grenzen, Erzeuger, Farben, Presets, Annahmentext |
| `rte_construct.py` | die sechs Erzeuger mit Spuren |
| `rte_evaluation.py` | Analyse, Bänder, Streudaten, Verdikt-Logik |
| `rte_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `rte_pdf_export.py` | PDF-Export des Ergebnisses |
| `rte_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `rte_scenario.py` | Instanzen (aus Stück 1) |
| `rte_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Savings und Sweep** (Stück 4 und 6); die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet beide.
- **Verbesserungsschleifen** (2-opt, Or-opt, ALNS) und die Suche über Reihenfolgen (Stück 11): [hill-climbing-demo](https://sebastianhanisch-hill-climbing-demo.streamlit.app/) und [grasp-demo](https://sebastianhanisch-grasp-demo.streamlit.app/) behandeln Nächster Nachbar als Startlösung der Rundreise, ohne Kapazität.
- **Flottengrenze** (Stück 3), **Zeitfenster** (Stück 8): der Hilfsgraph bleibt wie in Stück 1.
- **Instanzen über 12 Kunden live:** größere Instanzen stehen nur in den vorberechneten Bändern.
- **PyVRP als Abhängigkeit:** nur das Skript `generate_precomputed.py` benutzt es (optional, getestet mit 0.14.1).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
