"""
Bewerbungshelfer AI
Weboberfläche für Version 0.6
"""

import json
import re
from io import BytesIO
from pathlib import Path

from flask import Flask, render_template, request, send_file

from app import (
    split_items,
    compare_requirements,
    calculate_match_rate,
    build_summary,
    build_letter,
)

app = Flask(__name__)

PROFILE_FILE = Path("applicant_profile.json")

last_letter = ""


def load_profile():
    """Gespeichertes Bewerberprofil laden."""
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
            "experience": data.get("experience", ""),
            "qualifications": data.get("qualifications", ""),
            "focus": data.get("focus", ""),
        }

    except (json.JSONDecodeError, OSError):
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
    """Bewerberprofil lokal speichern."""
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


def extract_role(job_ad):
    """
    Versucht aus einer Stellenanzeige eine Stellenbezeichnung
    zu erkennen.

    Es wird bewusst nur eine vorsichtige Heuristik verwendet.
    """
    if not job_ad:
        return ""

    lines = [
        line.strip()
        for line in job_ad.splitlines()
        if line.strip()
    ]

    for line in lines[:8]:
        cleaned = re.sub(
            r"^[\-\*\u2022]+\s*",
            "",
            line,
        )

        if (
            3 <= len(cleaned) <= 100
            and not cleaned.endswith(".")
        ):
            return cleaned

    return ""


def extract_requirements(job_ad):
    """
    Extrahiert wahrscheinliche Anforderungen aus einer
    kompletten Stellenanzeige.

    Die Funktion erfindet keine Qualifikationen.
    """
    if not job_ad:
        return ""

    keywords = (
        "erfahrung",
        "kenntnis",
        "kenntnisse",
        "führerschein",
        "qualifikation",
        "voraussetzung",
        "anforderung",
        "erwart",
        "bringen sie",
        "bringen du",
        "dein profil",
        "ihr profil",
        "ausbildung",
        "berufserfahrung",
        "deutsch",
        "englisch",
        "bereitschaft",
        "zuverläss",
        "selbstständig",
        "teamfähig",
        "fahrerkarte",
        "ce",
        "c/ce",
        "czv",
        "modul 95",
    )

    extracted = []

    lines = job_ad.replace(
        "\r",
        "",
    ).split("\n")

    for raw_line in lines:
        line = raw_line.strip()

        line = re.sub(
            r"^[\-\*\u2022✓✔►▪]+\s*",
            "",
            line,
        )

        if len(line) < 4:
            continue

        lower = line.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):
            extracted.append(line)

    # Falls keine klaren Anforderungen erkannt wurden,
    # werden sinnvolle kurze Zeilen verwendet.
    if not extracted:
        for raw_line in lines:
            line = raw_line.strip()

            line = re.sub(
                r"^[\-\*\u2022✓✔►▪]+\s*",
                "",
                line,
            )

            if 10 <= len(line) <= 180:
                extracted.append(line)

    # Duplikate entfernen, Reihenfolge erhalten
    unique = []

    for item in extracted:
        if item not in unique:
            unique.append(item)

    return "\n".join(unique[:30])


@app.route("/", methods=["GET", "POST"])
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
        "qualifications": profile["qualifications"],
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

        form_data["requirements"] = request.form.get(
            "requirements",
            "",
        ).strip()

        form_data["experience"] = request.form.get(
            "experience",
            "",
        ).strip()

        form_data["qualifications"] = request.form.get(
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
                    form_data["qualifications"],
                    form_data["focus"],
                )

                success = (
                    "Bewerberprofil wurde gespeichert."
                )

            except OSError:
                error = (
                    "Das Bewerberprofil konnte nicht "
                    "gespeichert werden."
                )

        else:
            # Stellenbezeichnung vorsichtig aus
            # Stellenanzeige übernehmen
            if (
                not form_data["role"]
                and form_data["job_ad"]
            ):
                form_data["role"] = extract_role(
                    form_data["job_ad"]
                )

            # Anforderungen automatisch aus kompletter
            # Stellenanzeige extrahieren
            if (
                not form_data["requirements"]
                and form_data["job_ad"]
            ):
                form_data["requirements"] = (
                    extract_requirements(
                        form_data["job_ad"]
                    )
                )

            if not form_data["role"]:
                error = (
                    "Bitte eine Stellenbezeichnung eingeben."
                )

            elif not form_data["requirements"]:
                error = (
                    "Bitte Stellenanforderungen eingeben "
                    "oder eine komplette Stellenanzeige "
                    "einfügen."
                )

            elif not form_data["qualifications"]:
                error = (
                    "Bitte mindestens eine vorhandene "
                    "Qualifikation eingeben."
                )

            else:
                requirements = split_items(
                    form_data["requirements"]
                )

                qualifications = split_items(
                    form_data["qualifications"]
                )

                matched, missing = compare_requirements(
                    requirements,
                    qualifications,
                )

                match_rate = calculate_match_rate(
                    requirements,
                    matched,
                )

                result = build_summary(
                    form_data["role"],
                    requirements,
                    qualifications,
                    matched,
                    missing,
                )

                # Anschreiben erst erzeugen,
                # wenn der Benutzer es ausdrücklich auswählt.
                if action == "generate_letter":
                    letter = build_letter(
                        form_data["role"],
                        form_data["experience"],
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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
