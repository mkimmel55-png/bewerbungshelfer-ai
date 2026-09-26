"""
Bewerbungshelfer AI
Weboberfläche Version 0.7.1
"""

import json
import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import Flask, render_template, request, send_file

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


app = Flask(__name__)

PROFILE_FILE = Path("applicant_profile.json")

last_letter = ""


# =========================================================
# Text-Hilfsfunktionen
# =========================================================

def normalize(text):
    """
    Vereinheitlicht Text für sichere Vergleiche.
    """
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "/": " ",
        "-": " ",
        "_": " ",
        ",": " ",
        ".": " ",
        ":": " ",
        ";": " ",
        "(": " ",
        ")": " ",
        "[": " ",
        "]": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_items(text):
    """
    Trennt Texte an:
    - Zeilenumbrüchen
    - Kommas
    - Semikolons
    - Aufzählungszeichen
    """
    if not text:
        return []

    text = text.replace("\r", "\n")

    parts = re.split(
        r"[\n,;•✓✔►▪]+",
        text,
    )

    result = []

    for part in parts:
        item = part.strip(" -*\t")

        if item and item not in result:
            result.append(item)

    return result


# =========================================================
# Synonyme / Fachbegriffe
# =========================================================

CONCEPT_GROUPS = {

    "license_ce": {
        "ce",
        "klasse ce",
        "fuehrerschein ce",
        "fuehrerscheinklasse ce",
        "lkw fuehrerschein ce",
    },

    "license_c": {
        "klasse c",
        "fuehrerschein c",
        "fuehrerscheinklasse c",
    },

    "driver_card": {
        "fahrerkarte",
        "digitale fahrerkarte",
        "gueltige fahrerkarte",
    },

    # Deutschland
    "module_95_de": {
        "modul 95",
        "module 95",
        "schluesselzahl 95",
        "fahrerqualifizierungsnachweis",
        "berufskraftfahrerqualifikation",
        "bkrfqg",
    },

    # Schweiz bewusst getrennt
    "czv_ch": {
        "czv",
        "chauffeurzulassungsverordnung",
        "chauffeur zulassungsverordnung",
    },

    "load_security": {
        "ladungssicherung",
        "ladung sichern",
        "ladungsicherung",
    },

    "experience": {
        "berufserfahrung",
        "fahrerfahrung",
        "mehrjaehrige berufserfahrung",
        "mehrjaehrige erfahrung",
        "berufspraxis",
    },

    "truck_driver": {
        "lkw fahrer",
        "lkw fahrerin",
        "berufskraftfahrer",
        "berufskraftfahrerin",
        "chauffeur",
        "truck driver",
    },

    "local_transport": {
        "nahverkehr",
        "regionalverkehr",
        "regionaler verkehr",
        "tagestour",
        "tagestouren",
        "lokale touren",
        "lokalverkehr",
    },

    "night_work": {
        "nachttour",
        "nachttouren",
        "nachtfahrt",
        "nachtfahrten",
        "nachtschicht",
        "nachtarbeit",
    },

    "delivery": {
        "auslieferung",
        "zustellung",
        "warenzustellung",
        "lieferung",
        "distribution",
    },

    "german": {
        "deutsch",
        "deutschkenntnisse",
        "gute deutschkenntnisse",
        "deutsche sprache",
    },

    "english": {
        "englisch",
        "englischkenntnisse",
        "englische sprache",
    },

    "reliable": {
        "zuverlaessig",
        "zuverlaessigkeit",
    },

    "independent": {
        "selbststaendig",
        "eigenstaendig",
        "selbstaendige arbeitsweise",
        "selbststaendige arbeitsweise",
    },

    "teamwork": {
        "teamfaehig",
        "teamarbeit",
        "teamplayer",
    },

    "punctual": {
        "puenktlich",
        "puenktlichkeit",
    },

    "responsible": {
        "verantwortungsbewusst",
        "verantwortungsbewusstsein",
        "verantwortungsvoll",
    },

    "early_hours": {
        "fruehe arbeitszeiten",
        "fruehschicht",
        "fruehe schicht",
        "frueher arbeitsbeginn",
    },

    "flexible": {
        "flexibel",
        "flexibilitaet",
    },

    "customer_contact": {
        "kundenkontakt",
        "kundenservice",
        "kundenorientierung",
        "kundenfreundlich",
    },
}


def contains_phrase(text, phrase):
    """
    Prüft Begriffe möglichst sauber.
    Sehr kurze Begriffe wie C oder CE werden
    als einzelne Wörter geprüft.
    """
    text = normalize(text)
    phrase = normalize(phrase)

    if not text or not phrase:
        return False

    if len(phrase) <= 2:
        pattern = rf"\b{re.escape(phrase)}\b"
        return bool(re.search(pattern, text))

    return phrase in text


def detect_concepts(text):
    """
    Erkennt bekannte Qualifikationen oder Eigenschaften
    in einem Text.
    """
    detected = set()

    normalized_text = normalize(text)

    for concept, phrases in CONCEPT_GROUPS.items():

        for phrase in phrases:

            if contains_phrase(
                normalized_text,
                phrase,
            ):
                detected.add(concept)
                break

    return detected


# =========================================================
# Anforderungen analysieren
# =========================================================

def requirement_concepts(requirement):
    """
    Bestimmt, welche konkreten Konzepte eine
    Stellenanforderung verlangt.
    """
    text = normalize(requirement)

    concepts = set()

    # Führerschein C / CE
    if (
        re.search(r"\bce\b", text)
        or "klasse c ce" in text
        or "fuehrerschein c ce" in text
    ):
        concepts.add("license_ce")

    elif (
        re.search(r"\bklasse c\b", text)
        or "fuehrerschein c" in text
    ):
        concepts.add("license_c")

    if "fahrerkarte" in text:
        concepts.add("driver_card")

    # Module 95 / deutsche Qualifikation
    if any(
        phrase in text
        for phrase in (
            "modul 95",
            "module 95",
            "schluesselzahl 95",
            "berufskraftfahrerqualifikation",
            "fahrerqualifizierungsnachweis",
        )
    ):
        concepts.add("module_95_de")

    # Schweizer CZV
    if "czv" in text:
        concepts.add("czv_ch")

    if "ladungssicherung" in text:
        concepts.add("load_security")

    if (
        "berufserfahrung" in text
        or "fahrerfahrung" in text
        or "berufspraxis" in text
    ):
        concepts.add("experience")

    if any(
        phrase in text
        for phrase in (
            "lkw fahrer",
            "berufskraftfahrer",
            "chauffeur",
        )
    ):
        concepts.add("truck_driver")

    if any(
        phrase in text
        for phrase in (
            "nahverkehr",
            "regionalverkehr",
            "tagestour",
            "lokalverkehr",
        )
    ):
        concepts.add("local_transport")

    if any(
        phrase in text
        for phrase in (
            "auslieferung",
            "zustellung",
            "lieferung",
        )
    ):
        concepts.add("delivery")

    if "deutsch" in text:
        concepts.add("german")

    if "englisch" in text:
        concepts.add("english")

    if "zuverlaess" in text:
        concepts.add("reliable")

    if (
        "selbststaendig" in text
        or "eigenstaendig" in text
    ):
        concepts.add("independent")

    if "teamfaeh" in text:
        concepts.add("teamwork")

    if "puenktlich" in text:
        concepts.add("punctual")

    if "verantwortungsbewusst" in text:
        concepts.add("responsible")

    if any(
        phrase in text
        for phrase in (
            "fruehe arbeitszeiten",
            "fruehschicht",
            "frueher arbeitsbeginn",
        )
    ):
        concepts.add("early_hours")

    if "flexibel" in text:
        concepts.add("flexible")

    if (
        "kundenkontakt" in text
        or "kundenorient" in text
    ):
        concepts.add("customer_contact")

    return concepts


def is_optional_requirement(requirement):
    """
    Erkennt Anforderungen, die lediglich
    'von Vorteil', 'wünschenswert' usw. sind.
    """
    text = normalize(requirement)

    optional_markers = (
        "von vorteil",
        "wuenschenswert",
        "waere von vorteil",
        "idealerweise",
        "bevorzugt",
        "nice to have",
    )

    return any(
        marker in text
        for marker in optional_markers
    )


def requirement_matches(
    requirement,
    profile_concepts,
    profile_text,
):
    """
    Strenger Vergleich.

    Keine unscharfe Prozent-/Textähnlichkeit.
    """
    required = requirement_concepts(
        requirement
    )

    # Wenn bekannte Fachbegriffe erkannt wurden:
    if required:
        return required.issubset(
            profile_concepts
        )

    # Fallback nur bei deutlicher direkter Textübereinstimmung
    req = normalize(requirement)
    profile = normalize(profile_text)

    if not req or not profile:
        return False

    important_words = [
        word
        for word in req.split()
        if (
            len(word) >= 5
            and word not in {
                "kenntnisse",
                "erfahrung",
                "arbeitsweise",
                "bereitschaft",
                "mehrjaehrige",
                "mehrjaehriger",
                "mehrjaehriges",
                "gueltige",
                "gute",
                "vorteil",
            }
        )
    ]

    if not important_words:
        return False

    matched_words = sum(
        1
        for word in important_words
        if word in profile
    )

    # mindestens zwei deutliche Begriffe
    # oder alle Begriffe bei einer kurzen Anforderung
    if len(important_words) <= 2:
        return (
            matched_words
            == len(important_words)
        )

    return matched_words >= 2


def compare_requirements(
    requirements,
    experience,
    qualifications,
):
    """
    Vergleicht Stellenanforderungen mit echten
    Angaben aus Berufserfahrung und Qualifikationen.

    Das Hervorhebungsfeld wird bewusst NICHT
    als Nachweis verwendet.
    """

    profile_text = (
        f"{experience}\n{qualifications}"
    )

    profile_concepts = detect_concepts(
        profile_text
    )

    matched = []
    missing = []

    detailed_results = []

    for requirement in requirements:

        optional = is_optional_requirement(
            requirement
        )

        found = requirement_matches(
            requirement,
            profile_concepts,
            profile_text,
        )

        detailed_results.append(
            {
                "requirement": requirement,
                "matched": found,
                "optional": optional,
            }
        )

        if found:
            matched.append(requirement)

        else:
            if optional:
                missing.append(
                    f"{requirement} (optional)"
                )
            else:
                missing.append(requirement)

    return matched, missing, detailed_results


def calculate_match_rate(
    detailed_results,
):
    """
    Berechnet eine realistischere Trefferquote.

    Pflichtanforderung = Gewicht 1.0
    optionale Anforderung = Gewicht 0.5
    """

    if not detailed_results:
        return 0

    possible = 0.0
    achieved = 0.0

    for result in detailed_results:

        weight = (
            0.5
            if result["optional"]
            else 1.0
        )

        possible += weight

        if result["matched"]:
            achieved += weight

    if possible == 0:
        return 0

    return round(
        achieved
        / possible
        * 100
    )


# =========================================================
# Bewerberprofil
# =========================================================

def load_profile():
    """
    Gespeichertes Bewerberprofil laden.
    """

    if not PROFILE_FILE.exists():
        return {
            "experience": "",
            "qualifications": "",
            "focus": "",
        }

    try:

        with PROFILE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return {
            "experience": data.get(
                "experience",
                "",
            ),
            "qualifications": data.get(
                "qualifications",
                "",
            ),
            "focus": data.get(
                "focus",
                "",
            ),
        }

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return {
            "experience": "",
            "qualifications": "",
            "focus": "",
        }


def save_profile(
    experience,
    qualifications,
    focus,
):
    """
    Bewerberprofil lokal speichern.
    """

    profile = {
        "experience": experience,
        "qualifications": qualifications,
        "focus": focus,
    }

    with PROFILE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            profile,
            file,
            ensure_ascii=False,
            indent=2,
        )


# =========================================================
# Stellenbezeichnung erkennen
# =========================================================

def extract_role(job_ad):
    """
    Erkennt möglichst die eigentliche
    Stellenbezeichnung.
    """

    if not job_ad:
        return ""

    lines = [
        line.strip()
        for line in job_ad.splitlines()
        if line.strip()
    ]

    job_keywords = (
        "fahrer",
        "fahrerin",
        "chauffeur",
        "berufskraftfahrer",
        "lkw",
        "busfahrer",
        "buslenker",
        "kraftfahrer",
        "sachbearbeiter",
        "kundenservice",
        "datenerfassung",
        "support",
        "assistant",
        "assistenz",
    )

    for line in lines[:15]:

        cleaned = re.sub(
            r"^[\-\*\u2022✓✔►▪]+\s*",
            "",
            line,
        ).strip()

        lower = cleaned.lower()

        if (
            3 <= len(cleaned) <= 120
            and any(
                keyword in lower
                for keyword in job_keywords
            )
            and not lower.startswith(
                "wir suchen"
            )
        ):
            return cleaned

    for line in lines[:10]:

        cleaned = re.sub(
            r"^[\-\*\u2022✓✔►▪]+\s*",
            "",
            line,
        ).strip()

        lower = cleaned.lower()

        if (
            3 <= len(cleaned) <= 100
            and not cleaned.endswith(".")
            and not lower.startswith(
                "wir suchen"
            )
        ):
            return cleaned

    return ""


# =========================================================
# Anforderungen automatisch erkennen
# =========================================================

def extract_requirements(job_ad):
    """
    Extrahiert nur echte wahrscheinliche Anforderungen.
    """

    if not job_ad:
        return ""

    requirement_keywords = (
        "erfahrung",
        "kenntnis",
        "kenntnisse",
        "führerschein",
        "fuehrerschein",
        "klasse c",
        "klasse ce",
        "qualifikation",
        "ausbildung",
        "berufserfahrung",
        "deutsch",
        "englisch",
        "bereitschaft",
        "zuverläss",
        "zuverlaess",
        "selbstständig",
        "selbststaendig",
        "teamfähig",
        "teamfaehig",
        "fahrerkarte",
        "ladungssicherung",
        "czv",
        "modul 95",
        "module 95",
        "schlüsselzahl 95",
        "schluesselzahl 95",
        "adr",
        "flexibel",
        "flexibilität",
        "flexibilitaet",
        "pünktlich",
        "puenktlich",
        "verantwortungsbewusst",
        "kundenorient",
        "eigenständig",
        "eigenstaendig",
        "arbeitszeiten",
        "frühschicht",
        "fruehschicht",
    )

    ignored_starts = (
        "wir suchen",
        "wir bieten",
        "wir freuen",
        "ihre aufgaben",
        "deine aufgaben",
        "aufgaben",
        "ihr profil",
        "dein profil",
        "profil",
        "zum nächstmöglichen zeitpunkt",
        "zum naechstmoeglichen zeitpunkt",
        "unser unternehmen",
        "über uns",
        "ueber uns",
        "bewerben sie sich",
        "jetzt bewerben",
        "bei uns erwartet",
        "freuen sie sich",
        "freue dich",
    )

    extracted = []

    lines = job_ad.replace(
        "\r",
        "",
    ).split("\n")

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue

        line = re.sub(
            r"^[\-\*\u2022✓✔►▪]+\s*",
            "",
            line,
        ).strip()

        if len(line) < 3:
            continue

        lower = line.lower().rstrip(":")

        # Überschriften und Werbesätze ausschließen
        if any(
            lower == phrase
            or lower.startswith(phrase)
            for phrase in ignored_starts
        ):
            continue

        # Aufgaben nicht automatisch als Anforderungen behandeln
        task_phrases = (
            "durchführung von",
            "durchfuehrung von",
            "be- und entladen",
            "kontrolle und sicherung",
            "pflege und kontrolle",
            "dokumentation der",
            "freundlicher umgang",
        )

        if any(
            lower.startswith(task)
            for task in task_phrases
        ):
            continue

        # Nur Zeilen mit echten Anforderungssignalen
        if any(
            keyword in lower
            for keyword in requirement_keywords
        ):
            extracted.append(line)

    unique = []

    for item in extracted:

        normalized_item = normalize(item)

        if not any(
            normalize(existing)
            == normalized_item
            for existing in unique
        ):
            unique.append(item)

    return "\n".join(
        unique[:30]
    )


# =========================================================
# Zusammenfassung
# =========================================================

def build_summary(
    role,
    detailed_results,
    match_rate,
):
    """
    Erstellt eine verständliche Zusammenfassung.
    """

    lines = [
        f"Stelle: {role}",
        "",
        f"Übereinstimmung: {match_rate} %",
        "",
        "Erkannte Anforderungen:",
    ]

    for result in detailed_results:

        requirement = result["requirement"]

        if result["optional"]:
            requirement += " [optional]"

        if result["matched"]:
            lines.append(
                f"✓ {requirement}"
            )
        else:
            lines.append(
                f"✗ {requirement}"
            )

    return "\n".join(lines)


# =========================================================
# Anschreiben
# =========================================================

def build_letter(
    role,
    experience,
    qualifications,
    focus,
    matched,
):
    """
    Erstellt ein Bewerbungsanschreiben.
    """

    qualification_text = ", ".join(
        qualifications
    )

    paragraphs = [
        f"Bewerbung als {role}",
        "",
        "Sehr geehrte Damen und Herren,",
        "",
        (
            f"mit Interesse bewerbe ich mich "
            f"bei Ihnen als {role}."
        ),
    ]

    if experience:

        paragraphs.extend(
            [
                "",
                (
                    "Ich verfüge über folgende "
                    f"Berufserfahrung: {experience}."
                ),
            ]
        )

    if qualification_text:

        paragraphs.extend(
            [
                "",
                (
                    "Zu meinen vorhandenen "
                    "Qualifikationen zählen "
                    f"{qualification_text}."
                ),
            ]
        )

    if matched:

        safe_matches = ", ".join(
            matched[:5]
        )

        paragraphs.extend(
            [
                "",
                (
                    "Mehrere Anforderungen Ihrer "
                    "Stelle decken sich mit meiner "
                    "bisherigen Erfahrung und meinen "
                    f"Qualifikationen, darunter "
                    f"{safe_matches}."
                ),
            ]
        )

    if focus:

        paragraphs.extend(
            [
                "",
                focus,
            ]
        )

    paragraphs.extend(
        [
            "",
            (
                "Gerne erläutere ich Ihnen meine "
                "Erfahrung und Qualifikationen in "
                "einem persönlichen Gespräch."
            ),
            "",
            "Mit freundlichen Grüßen",
        ]
    )

    return "\n".join(paragraphs)


# =========================================================
# Flask Hauptseite
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"],
)
def index():

    global last_letter

    result = None
    letter = None
    matched = []
    missing = []
    match_rate = None
    error = None
    success = None

    profile = load_profile()

    form_data = {
        "role": "",
        "job_ad": "",
        "requirements": "",
        "experience": profile["experience"],
        "qualifications": profile[
            "qualifications"
        ],
        "focus": profile["focus"],
    }

    if request.method == "POST":

        action = request.form.get(
            "action",
            "analyze",
        )

        form_data["role"] = request.form.get(
            "role",
            "",
        ).strip()

        form_data["job_ad"] = request.form.get(
            "job_ad",
            "",
        ).strip()

        form_data[
            "requirements"
        ] = request.form.get(
            "requirements",
            "",
        ).strip()

        form_data[
            "experience"
        ] = request.form.get(
            "experience",
            "",
        ).strip()

        form_data[
            "qualifications"
        ] = request.form.get(
            "qualifications",
            "",
        ).strip()

        form_data["focus"] = request.form.get(
            "focus",
            "",
        ).strip()

        # Profil speichern
        if action == "save_profile":

            try:

                save_profile(
                    form_data["experience"],
                    form_data[
                        "qualifications"
                    ],
                    form_data["focus"],
                )

                success = (
                    "Bewerberprofil wurde gespeichert."
                )

            except OSError:

                error = (
                    "Das Bewerberprofil konnte "
                    "nicht gespeichert werden."
                )

        else:

            # Stellenbezeichnung erkennen
            if (
                not form_data["role"]
                and form_data["job_ad"]
            ):

                form_data[
                    "role"
                ] = extract_role(
                    form_data["job_ad"]
                )

            # Anforderungen erkennen
            if (
                not form_data["requirements"]
                and form_data["job_ad"]
            ):

                form_data[
                    "requirements"
                ] = extract_requirements(
                    form_data["job_ad"]
                )

            if not form_data["role"]:

                error = (
                    "Bitte eine Stellenbezeichnung "
                    "eingeben."
                )

            elif not form_data["requirements"]:

                error = (
                    "Es konnten keine Anforderungen "
                    "erkannt werden. Bitte die "
                    "Anforderungen manuell eingeben."
                )

            elif not (
                form_data["qualifications"]
                or form_data["experience"]
            ):

                error = (
                    "Bitte Berufserfahrung oder "
                    "vorhandene Qualifikationen "
                    "eingeben."
                )

            else:

                requirements = split_items(
                    form_data["requirements"]
                )

                qualifications = split_items(
                    form_data[
                        "qualifications"
                    ]
                )

                (
                    matched,
                    missing,
                    detailed_results,
                ) = compare_requirements(
                    requirements,
                    form_data["experience"],
                    form_data[
                        "qualifications"
                    ],
                )

                match_rate = (
                    calculate_match_rate(
                        detailed_results
                    )
                )

                result = build_summary(
                    form_data["role"],
                    detailed_results,
                    match_rate,
                )

                if action == "generate_letter":

                    letter = build_letter(
                        form_data["role"],
                        form_data[
                            "experience"
                        ],
                        qualifications,
                        form_data["focus"],
                        matched,
                    )

                    last_letter = letter

    return render_template(
        "index.html",
        result=result,
        letter=letter,
        matched=matched,
        missing=missing,
        match_rate=match_rate,
        error=error,
        success=success,
        form_data=form_data,
    )


# =========================================================
# TXT Download
# =========================================================

@app.route("/download-letter")
def download_letter():

    if not last_letter:

        return (
            "Noch kein Anschreiben vorhanden.",
            400,
        )

    file_data = BytesIO(
        last_letter.encode("utf-8")
    )

    return send_file(
        file_data,
        as_attachment=True,
        download_name="anschreiben.txt",
        mimetype="text/plain; charset=utf-8",
    )


# =========================================================
# PDF Download
# =========================================================

@app.route("/download-letter-pdf")
def download_letter_pdf():

    if not last_letter:

        return (
            "Noch kein Anschreiben vorhanden.",
            400,
        )

    pdf_data = BytesIO()

    document = SimpleDocTemplate(
        pdf_data,
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title="Bewerbungsanschreiben",
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "Bewerbungsanschreiben",
            styles["Title"],
        )
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    for paragraph in last_letter.split(
        "\n"
    ):

        paragraph = paragraph.strip()

        if paragraph:

            safe_text = escape(
                paragraph
            )

            story.append(
                Paragraph(
                    safe_text,
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(
                    1,
                    0.25 * cm,
                )
            )

    document.build(story)

    pdf_data.seek(0)

    return send_file(
        pdf_data,
        as_attachment=True,
        download_name="Anschreiben.pdf",
        mimetype="application/pdf",
    )


# =========================================================
# Start
# =========================================================

if __name__ == "__main__":

    print(
        "Bewerbungshelfer AI Version 0.7.1"
    )

    print(
        "Webseite: http://127.0.0.1:5000"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
