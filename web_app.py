"""
Bewerbungshelfer AI
Weboberfläche Version 0.7.0
"""

import json
import re
from difflib import SequenceMatcher
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


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

def normalize(text):
    """
    Vereinheitlicht Texte für den Vergleich.
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
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_items(text):
    """
    Trennt Anforderungen und Qualifikationen.

    Unterstützt:
    - Zeilenumbrüche
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


# ---------------------------------------------------------
# Synonyme
# ---------------------------------------------------------

SYNONYM_GROUPS = [
    {
        "ce",
        "klasse ce",
        "fuehrerschein ce",
        "fuehrerscheinklasse ce",
        "lkw fuehrerschein",
        "lkw fuehrerschein ce",
    },
    {
        "c",
        "klasse c",
        "fuehrerschein c",
        "fuehrerscheinklasse c",
    },
    {
        "fahrerkarte",
        "digitale fahrerkarte",
        "gueltige fahrerkarte",
    },
    {
        "95",
        "modul 95",
        "module 95",
        "schluesselzahl 95",
        "berufskraftfahrerqualifikation",
        "fahrerqualifizierungsnachweis",
        "bkrfqg",
    },
    {
        "czv",
        "chauffeurzulassungsverordnung",
        "chauffeur zulassungsverordnung",
    },
    {
        "ladungssicherung",
        "ladung sichern",
        "ladungsicherung",
    },
    {
        "berufserfahrung",
        "erfahrung",
        "mehrjaehrige erfahrung",
        "mehrjährige erfahrung",
        "fahrerfahrung",
        "berufspraxis",
    },
    {
        "lkw fahrer",
        "lkw fahrerin",
        "berufskraftfahrer",
        "berufskraftfahrerin",
        "chauffeur",
        "chauffeuse",
        "truck driver",
    },
    {
        "nahverkehr",
        "regionalverkehr",
        "regionaler verkehr",
        "tagestouren",
        "tagestour",
        "lokale touren",
        "lokalverkehr",
    },
    {
        "nachttouren",
        "nachtfahrten",
        "nachtschicht",
        "nachtarbeit",
        "nachtverkehr",
    },
    {
        "deutsch",
        "deutschkenntnisse",
        "deutsche sprache",
        "gute deutschkenntnisse",
    },
    {
        "englisch",
        "englischkenntnisse",
        "englische sprache",
    },
    {
        "zuverlaessig",
        "zuverlässig",
        "zuverlaessigkeit",
        "zuverlässigkeit",
    },
    {
        "teamfaehig",
        "teamfähig",
        "teamarbeit",
        "teamplayer",
    },
    {
        "selbststaendig",
        "selbstständig",
        "selbststaendige arbeitsweise",
        "eigenstaendig",
        "eigenständig",
    },
    {
        "flexibel",
        "flexibilitaet",
        "flexibilität",
    },
    {
        "pünktlich",
        "puenktlich",
        "puenktlichkeit",
        "pünktlichkeit",
    },
    {
        "kundenkontakt",
        "kundenorientierung",
        "kundenfreundlich",
        "kundenservice",
    },
    {
        "auslieferung",
        "lieferung",
        "zustellung",
        "warenzustellung",
        "distribution",
    },
    {
        "getraenke",
        "getränke",
        "getraenkelogistik",
        "getränkelogistik",
        "getraenkeauslieferung",
        "getränkeauslieferung",
    },
]


def synonym_match(requirement, qualification):
    """
    Prüft, ob zwei Begriffe über eine Synonymgruppe zusammengehören.
    """
    req = normalize(requirement)
    qual = normalize(qualification)

    for group in SYNONYM_GROUPS:
        normalized_group = {
            normalize(item)
            for item in group
        }

        req_found = any(
            item in req or req in item
            for item in normalized_group
        )

        qual_found = any(
            item in qual or qual in item
            for item in normalized_group
        )

        if req_found and qual_found:
            return True

    return False


def word_overlap_score(text1, text2):
    """
    Berechnet die Wortüberschneidung.
    """
    words1 = {
        word
        for word in normalize(text1).split()
        if len(word) >= 2
    }

    words2 = {
        word
        for word in normalize(text2).split()
        if len(word) >= 2
    }

    if not words1 or not words2:
        return 0.0

    common = words1 & words2

    return len(common) / min(
        len(words1),
        len(words2),
    )


def requirement_matches(requirement, qualification):
    """
    Verbesserter Vergleich einer Anforderung
    mit einer vorhandenen Qualifikation.
    """
    req = normalize(requirement)
    qual = normalize(qualification)

    if not req or not qual:
        return False

    # Exakter Treffer
    if req == qual:
        return True

    # Text ist Bestandteil des anderen
    if req in qual or qual in req:
        return True

    # Synonyme
    if synonym_match(req, qual):
        return True

    # Wortüberschneidung
    overlap = word_overlap_score(
        req,
        qual,
    )

    if overlap >= 0.50:
        return True

    # Ähnlichkeit des gesamten Textes
    similarity = SequenceMatcher(
        None,
        req,
        qual,
    ).ratio()

    if similarity >= 0.72:
        return True

    return False


def compare_requirements(
    requirements,
    qualifications,
):
    """
    Vergleicht alle Anforderungen mit
    allen vorhandenen Qualifikationen.
    """
    matched = []
    missing = []

    for requirement in requirements:
        found = False

        for qualification in qualifications:
            if requirement_matches(
                requirement,
                qualification,
            ):
                found = True
                break

        if found:
            matched.append(requirement)
        else:
            missing.append(requirement)

    return matched, missing


def calculate_match_rate(
    requirements,
    matched,
):
    """
    Berechnet die Übereinstimmung in Prozent.
    """
    if not requirements:
        return 0

    rate = (
        len(matched)
        / len(requirements)
    ) * 100

    return round(rate)


# ---------------------------------------------------------
# Bewerberprofil
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Stellenbezeichnung erkennen
# ---------------------------------------------------------

def extract_role(job_ad):
    """
    Versucht automatisch die Stellenbezeichnung
    aus einer Stellenanzeige zu erkennen.
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
        "chauffeuse",
        "berufskraftfahrer",
        "lkw",
        "busfahrer",
        "buslenker",
        "kraftfahrer",
        "mitarbeiter",
        "sachbearbeiter",
        "kundenservice",
        "datenerfassung",
        "data entry",
        "support",
        "assistant",
        "assistenz",
    )

    # Zuerst nach einer typischen Stellenbezeichnung suchen
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
        ):
            return cleaned

    # Falls nichts erkannt wurde:
    # erste kurze sinnvolle Zeile nehmen
    for line in lines[:10]:
        cleaned = re.sub(
            r"^[\-\*\u2022✓✔►▪]+\s*",
            "",
            line,
        ).strip()

        if (
            3 <= len(cleaned) <= 100
            and not cleaned.endswith(".")
        ):
            return cleaned

    return ""


# ---------------------------------------------------------
# Anforderungen aus Stellenanzeige erkennen
# ---------------------------------------------------------

def extract_requirements(job_ad):
    """
    Extrahiert wahrscheinliche Anforderungen
    aus einer kompletten Stellenanzeige.
    """
    if not job_ad:
        return ""

    requirement_keywords = (
        "erfahrung",
        "kenntnis",
        "kenntnisse",
        "führerschein",
        "fuehrerschein",
        "klasse b",
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
        "kundenorient",
        "selbständig",
        "eigenständig",
        "eigenstaendig",
    )

    ignored_phrases = (
        "wir suchen",
        "wir bieten",
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
        "benefits",
        "was wir bieten",
        "das bieten wir",
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

        # Überschriften ignorieren
        if any(
            lower == phrase
            for phrase in ignored_phrases
        ):
            continue

        # Werbetexte ignorieren
        if any(
            lower.startswith(phrase)
            for phrase in (
                "wir bieten",
                "wir bieten ihnen",
                "wir bieten dir",
                "bei uns erwartet",
                "freuen sie sich",
                "freue dich",
            )
        ):
            continue

        # Kurze reine Stellenbezeichnungen ignorieren
        if (
            len(line) < 80
            and any(
                word in lower
                for word in (
                    "lkw-fahrer",
                    "lkw fahrer",
                    "berufskraftfahrer",
                    "chauffeur",
                    "busfahrer",
                    "kraftfahrer",
                )
            )
            and not any(
                keyword in lower
                for keyword in requirement_keywords
            )
        ):
            continue

        # Anforderungen erkennen
        if any(
            keyword in lower
            for keyword in requirement_keywords
        ):
            extracted.append(line)

    # Duplikate entfernen
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


# ---------------------------------------------------------
# Zusammenfassung
# ---------------------------------------------------------

def build_summary(
    role,
    requirements,
    qualifications,
    matched,
    missing,
):
    """
    Erstellt eine verständliche Auswertung.
    """
    match_rate = calculate_match_rate(
        requirements,
        matched,
    )

    lines = [
        f"Stelle: {role}",
        "",
        f"Übereinstimmung: {match_rate} %",
        "",
        "Passende Anforderungen:",
    ]

    if matched:
        for item in matched:
            lines.append(
                f"✓ {item}"
            )
    else:
        lines.append(
            "Keine eindeutigen Treffer erkannt."
        )

    lines.append("")
    lines.append(
        "Noch nicht erkannte Anforderungen:"
    )

    if missing:
        for item in missing:
            lines.append(
                f"• {item}"
            )
    else:
        lines.append(
            "Keine."
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# Anschreiben
# ---------------------------------------------------------

def build_letter(
    role,
    experience,
    qualifications,
    focus,
    matched,
):
    """
    Erstellt ein einfaches Bewerbungsanschreiben.
    """
    qualification_text = ", ".join(
        qualifications
    )

    matched_text = ", ".join(
        matched
    )

    paragraphs = [
        f"Bewerbung als {role}",
        "",
        "Sehr geehrte Damen und Herren,",
        "",
        (
            f"mit großem Interesse bewerbe ich mich "
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
                    "Zu meinen Qualifikationen zählen "
                    f"unter anderem {qualification_text}."
                ),
            ]
        )

    if matched_text:
        paragraphs.extend(
            [
                "",
                (
                    "Besonders gut passen zu Ihrem "
                    "Anforderungsprofil meine Kenntnisse "
                    f"und Erfahrungen in den Bereichen "
                    f"{matched_text}."
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
                "Gerne überzeuge ich Sie in einem "
                "persönlichen Gespräch oder bei einem "
                "Probearbeitstag von meiner Motivation "
                "und meiner praktischen Erfahrung."
            ),
            "",
            "Mit freundlichen Grüßen",
        ]
    )

    return "\n".join(paragraphs)


# ---------------------------------------------------------
# Flask Hauptseite
# ---------------------------------------------------------

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

        # -------------------------------------------------
        # Profil speichern
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Analyse / Anschreiben
        # -------------------------------------------------

        else:

            # Stellenbezeichnung automatisch erkennen
            if (
                not form_data["role"]
                and form_data["job_ad"]
            ):
                form_data[
                    "role"
                ] = extract_role(
                    form_data["job_ad"]
                )

            # Anforderungen automatisch erkennen
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
                    "Stellenanforderungen manuell "
                    "eingeben."
                )

            elif not form_data[
                "qualifications"
            ]:

                error = (
                    "Bitte mindestens eine vorhandene "
                    "Qualifikation eingeben."
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

                matched, missing = (
                    compare_requirements(
                        requirements,
                        qualifications,
                    )
                )

                match_rate = (
                    calculate_match_rate(
                        requirements,
                        matched,
                    )
                )

                result = build_summary(
                    form_data["role"],
                    requirements,
                    qualifications,
                    matched,
                    missing,
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


# ---------------------------------------------------------
# Anschreiben TXT
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Anschreiben PDF
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Start
# ---------------------------------------------------------

if __name__ == "__main__":
    print(
        "Bewerbungshelfer AI Version 0.7.0"
    )
    print(
        "Webseite: http://127.0.0.1:5000"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
