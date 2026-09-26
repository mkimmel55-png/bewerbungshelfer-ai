# Bewerbungshelfer AI

Ein kleines Open-Source-Projekt, das Bewerberinnen und Bewerbern dabei hilft, Stellenanzeigen strukturiert auszuwerten und passende Bewerbungsunterlagen vorzubereiten.

## Funktionen

- Anforderungen aus einer Stellenanzeige erfassen
- Eigene Qualifikationen und Erfahrung gegenüberstellen
- Passende Stärken hervorheben
- Einen Entwurf für ein Anschreiben erzeugen
- Hinweise auf fehlende Angaben oder mögliche Lücken geben
- Stellenanforderungen mit vorhandenen Qualifikationen vergleichen
- passende Anforderungen erkennen
- fehlende oder nicht erkannte Anforderungen anzeigen
- Nutzung über eine einfache Weboberfläche

## Ziel

Das Projekt soll besonders Quereinsteigern und Menschen mit wenig Erfahrung im Schreiben von Bewerbungen helfen, ihre Informationen übersichtlich zu strukturieren.

Die Anwendung soll keine Qualifikationen erfinden und ersetzt keine persönliche Prüfung der Bewerbung.

## Schnellstart

Voraussetzung: Python 3.10 oder neuer.

Für die Kommandozeilen-Version:

    python app.py

## Weboberfläche starten

Ab Version 0.3.0 kann Bewerbungshelfer AI auch im Browser verwendet werden.

### Installation

Zuerst die benötigten Abhängigkeiten installieren:

    pip install -r requirements.txt

### Start

Danach die Webanwendung starten:

    python web_app.py

Anschließend im Browser öffnen:

    http://127.0.0.1:5000

## Funktionen der Weboberfläche

- Eingabe der Stellenbezeichnung
- Erfassung von Stellenanforderungen
- Eingabe der Berufserfahrung
- Eingabe vorhandener Qualifikationen
- Vergleich von Anforderungen und Qualifikationen
- Anzeige passender Anforderungen
- Anzeige fehlender oder nicht erkannter Anforderungen
- Erstellung eines einfachen Anschreiben-Entwurfs

## Vergleichslogik

Die aktuelle Version verwendet eine einfache textbasierte Vergleichslogik.

Eine Anforderung gilt als passend, wenn sie textlich mit einer vorhandenen Qualifikation übereinstimmt oder darin enthalten ist.

## Datenschutz

Die aktuelle Basisversion läuft lokal.

Persönliche Eingaben werden nicht automatisch an externe Dienste gesendet.

Die Weboberfläche verwendet in der aktuellen Version keinen externen KI-Dienst.

## Projektstruktur

    bewerbungshelfer-ai
    ├── .gitignore
    ├── CONTRIBUTING.md
    ├── LICENSE
    ├── README.md
    ├── app.py
    ├── requirements.txt
    ├── web_app.py
    └── templates
        └── index.html

## Versionen

### v0.1.0

Erste öffentliche Basisversion.

### v0.2.0

Vergleich zwischen Stellenanforderungen und vorhandenen Qualifikationen.

### v0.3.0

Weboberfläche für die Bedienung im Browser.
### v0.4.0
### v0.4.0

Verbesserte Weboberfläche und komfortablere Bedienung.

Neu:

- Eingaben bleiben nach der Analyse im Formular erhalten
- verständlichere Fehlermeldungen bei fehlenden Angaben
- passende Anforderungen werden getrennt angezeigt
- fehlende Anforderungen werden getrennt angezeigt
- mobilfreundlicheres Layout
- Anschreiben kann als TXT-Datei heruntergeladen werden

### v0.5.0

Verbesserte Vergleichslogik und Trefferquote.

Neu:

- flexiblerer Vergleich von Anforderungen und Qualifikationen
- Vergleich anhand gemeinsamer Wörter
- weiterhin keine erfundenen Qualifikationen
- Berechnung einer Trefferquote in Prozent
- Anzeige der Trefferquote in der Weboberfläche
- passende und fehlende Anforderungen bleiben getrennt sichtbar
 ## Geplante Funktionen
- deutsche und englische Ausgabe
- PDF-Ausgabe für Anschreiben
- DOCX-Export
- weitere Verbesserungen der Weboberfläche
- optionale KI-Unterstützung
- Tests für die Vergleichsfunktionen

## Mitmachen

Fehlerberichte, Verbesserungsvorschläge und Pull Requests sind willkommen.

Siehe CONTRIBUTING.md.

## Lizenz

Dieses Projekt steht unter der MIT License.

Siehe LICENSE.
