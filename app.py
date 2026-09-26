"""Bewerbungshelfer AI command-line application."""

import re
from io import BytesIO
from textwrap import fill


APP_VERSION = "0.9.0"


def extract_resume_text(uploaded_file) -> str:
    """Extract text from an uploaded PDF, DOCX or TXT file in memory.

    The function deliberately raises a clear ValueError instead of guessing
    when a file is unsupported or contains no readable text.
    """
    if uploaded_file is None:
        return ""

    name = getattr(uploaded_file, "name", "").lower()
    data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()

    try:
        if name.endswith(".txt"):
            return data.decode("utf-8-sig", errors="replace").strip()
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if not text.strip():
                raise ValueError("Die PDF enthält keinen auslesbaren Text. Bitte eine textbasierte PDF verwenden.")
            return text.strip()
        if name.endswith(".docx"):
            from docx import Document
            document = Document(BytesIO(data))
            paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        paragraphs.append(" | ".join(cells))
            text = "\n".join(paragraphs)
            if not text.strip():
                raise ValueError("Die DOCX-Datei enthält keinen auslesbaren Text.")
            return text.strip()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Die Datei konnte nicht gelesen werden. Bitte Format und Dateiinhalt prüfen.") from exc

    raise ValueError("Nicht unterstütztes Dateiformat. Bitte PDF, DOCX oder TXT hochladen.")


def extract_resume_profile(text: str) -> dict[str, str]:
    """Conservatively suggest profile fields from resume text.

    Only text that is actually present is returned. No qualifications are
    inferred from job titles or generic words.
    """
    if not text or not text.strip():
        return {"experience": "", "qualifications": "", "focus": ""}

    lines = [re.sub(r"^[\s\-•*]+", "", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if len(line) >= 3]
    lower = "\n".join(lines).lower()

    qualification_terms = (
        "abschluss", "ausbildung", "studium", "zertifikat", "zertifizierung",
        "bachelor", "master", "diplom", "m.sc", "b.a.",
        "führerschein", "fuehrerschein", "fahrerkarte", "modul 95", "module 95",
        "sprachkenntnisse", "sprachen", "deutsch", "englisch", "französisch", "franzoesisch",
        "kenntnisse", "qualifikation", "qualifikationen",
    )
    strength_terms = (
        "zuverläss", "zuverlaess", "teamfähig", "teamfaehig", "selbstständig",
        "selbststaendig", "kommunikativ", "belastbar", "organisiert", "pünktlich",
        "puenktlich", "verantwortungsbewusst", "kundenorient",
    )
    experience_terms = (
        "berufserfahrung", "beruflicher werdegang", "berufliche stationen",
        "beschäftigt", "beschaeftigt", "tätigkeit", "taetigkeit", "erfahrung",
    )

    qualifications = [line for line in lines if any(term in line.lower() for term in qualification_terms)]
    strengths = [line for line in lines if any(term in line.lower() for term in strength_terms)]
    experience = [line for line in lines if any(term in line.lower() for term in experience_terms)]

    # Preserve nearby job/date lines where a CV uses a heading followed by entries.
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in experience_terms):
            experience.extend(lines[index + 1:index + 6])

    def unique(items: list[str]) -> list[str]:
        output = []
        for item in items:
            if item not in output:
                output.append(item)
        return output[:20]

    return {
        "experience": "\n".join(unique(experience)),
        "qualifications": "\n".join(unique(qualifications)),
        "focus": "\n".join(unique(strengths)),
    }


# Wörter, die für den Vergleich wenig Aussagekraft haben
STOP_WORDS = {
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einer",
    "einem",
    "einen",
    "und",
    "oder",
    "mit",
    "für",
    "von",
    "im",
    "in",
    "am",
    "an",
    "als",
    "auf",
    "zu",
    "zur",
    "zum",
    "bei",
    "sowie",
    "sie",
    "ihr",
    "ihre",
    "ihren",
    "dein",
    "deine",
    "wir",
    "suchen",
}


def ask(label: str) -> str:
    return input(f"{label}: ").strip()


def split_items(text: str) -> list[str]:
    """
    Trennt Eingaben an:
    - Zeilenumbrüchen
    - Kommas
    - Semikolons
    - Aufzählungszeichen

    Entfernt außerdem typische Überschriften.
    """
    if not text:
        return []

    text = text.replace("\r", "\n")

    raw_items = re.split(
        r"[\n,;]+",
        text,
    )

    ignored_headings = {
        "ihr profil",
        "dein profil",
        "profil",
        "anforderungen",
        "voraussetzungen",
        "was sie mitbringen",
        "was du mitbringst",
    }

    items = []

    for item in raw_items:
        item = re.sub(
            r"^[\s\-\*\u2022✓✔►▪]+",
            "",
            item,
        ).strip()

        item = item.rstrip(":").strip()

        if not item:
            continue

        if item.lower() in ignored_headings:
            continue

        if item not in items:
            items.append(item)

    return items


def normalize(text: str) -> str:
    """
    Vereinheitlicht Texte für den Vergleich.
    """
    text = text.lower().strip()

    replacements = {
        "lkw fahrer": "lkw-fahrer",
        "lkw-fahrerin": "lkw-fahrer",
        "kraftfahrer": "lkw-fahrer",
        "kraftfahrerin": "lkw-fahrer",
        "führerschein klasse ce": "führerschein ce",
        "führerschein der klasse ce": "führerschein ce",
        "führerschein kl. ce": "führerschein ce",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def word_set(text: str) -> set[str]:
    """
    Zerlegt Text in aussagekräftige Wörter.
    Unwichtige Standardwörter werden entfernt.
    """
    words = re.findall(
        r"[a-zA-ZäöüÄÖÜß0-9\-]+",
        normalize(text),
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 1
    }


def requirement_matches(
    requirement: str,
    qualification: str,
) -> bool:
    """
    Prüft, ob eine konkrete Anforderung durch eine
    vorhandene Qualifikation abgedeckt wird.

    Der Vergleich ist bewusst konservativer als vorher,
    damit nicht zu schnell ein Treffer entsteht.
    """

    req = normalize(requirement)
    qual = normalize(qualification)

    if not req or not qual:
        return False

    # Exakte Übereinstimmung
    if req == qual:
        return True

    # Sinnvolle direkte Teilübereinstimmung
    if len(req) >= 6 and req in qual:
        return True

    if len(qual) >= 6 and qual in req:
        return True

    req_words = word_set(req)
    qual_words = word_set(qual)

    if not req_words or not qual_words:
        return False

    common_words = req_words & qual_words

    if not common_words:
        return False

    # Kurze Anforderungen müssen sehr genau passen
    if len(req_words) == 1:
        return len(common_words) == 1

    if len(req_words) == 2:
        return len(common_words) == 2

    # Bei längeren Anforderungen müssen mindestens
    # 60 % der aussagekräftigen Wörter übereinstimmen.
    score = len(common_words) / len(req_words)

    return score >= 0.60


def compare_requirements(
    requirements: list[str],
    qualifications: list[str],
    experience: str = "",
) -> tuple[list[str], list[str]]:
    """
    Vergleicht jede Anforderung einzeln mit den
    vorhandenen Qualifikationen.
    """

    matched = []
    missing = []

    profile_text = "\n".join([experience, *qualifications])

    for requirement in requirements:
        found = requirement_matches(
            requirement,
            profile_text,
        )

        if found:
            matched.append(requirement)
        else:
            missing.append(requirement)

    return matched, missing


def calculate_match_rate(
    requirements: list[str],
    matched: list[str],
) -> int:
    """
    Berechnet die Trefferquote anhand einzelner
    Anforderungen.
    """

    if not requirements:
        return 0

    return round(
        len(matched)
        / len(requirements)
        * 100
    )


def build_summary(
    role: str,
    requirements: list[str],
    qualifications: list[str],
    matched: list[str],
    missing: list[str],
) -> str:
    """
    Erstellt eine übersichtliche Zusammenfassung.
    """

    match_rate = calculate_match_rate(
        requirements,
        matched,
    )

    lines = [
        f"Zielstelle: {role}",
        "",
        f"Trefferquote: {match_rate} %",
        "",
        "Anforderungen:",
    ]

    if requirements:
        lines.extend(
            f"- {item}"
            for item in requirements
        )
    else:
        lines.append("- keine Angaben")

    lines.extend([
        "",
        "Vorhandene Qualifikationen:",
    ])

    if qualifications:
        lines.extend(
            f"- {item}"
            for item in qualifications
        )
    else:
        lines.append("- keine Angaben")

    lines.extend([
        "",
        "Passende Anforderungen:",
    ])

    if matched:
        lines.extend(
            f"- {item}"
            for item in matched
        )
    else:
        lines.append(
            "- keine eindeutigen Treffer"
        )

    lines.extend([
        "",
        "Fehlende oder nicht erkannte Anforderungen:",
    ])

    if missing:
        lines.extend(
            f"- {item}"
            for item in missing
        )
    else:
        lines.append("- keine")

    return "\n".join(lines)


def clean_sentence(text: str) -> str:
    """
    Bereinigt Texte für das Anschreiben.
    """
    text = text.strip()

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    if text[-1] not in ".!?":
        text += "."

    return text


def build_letter(
    role: str,
    experience: str,
    qualifications: list[str],
    focus: str,
    matched: list[str],
) -> str:
    """
    Erstellt ein natürlicheres Anschreiben.

    Anforderungen der Stellenanzeige werden nicht einfach
    vollständig in das Anschreiben kopiert.
    """

    paragraphs = [
        "Sehr geehrte Damen und Herren,",
        "",
        (
            f"mit Interesse bewerbe ich mich auf die Position "
            f"als {role}. Aufgrund meiner bisherigen "
            f"Berufserfahrung und meiner vorhandenen "
            f"Qualifikationen sehe ich eine gute fachliche "
            f"Übereinstimmung mit der ausgeschriebenen Stelle."
        ),
    ]

    if experience:
        paragraphs.extend([
            "",
            clean_sentence(experience),
        ])

    if qualifications:
        qualification_text = ", ".join(
            qualifications[:6]
        )

        paragraphs.extend([
            "",
            (
                "Zu meinen vorhandenen Qualifikationen "
                f"und Kenntnissen zählen {qualification_text}."
            ),
        ])

    if focus:
        paragraphs.extend([
            "",
            (
                "Besonders hervorheben möchte ich "
                + clean_sentence(focus).lower()
            ),
        ])

    if matched:
        selected_matches = matched[:3]

        matched_text = ", ".join(
            selected_matches
        )

        paragraphs.extend([
            "",
            (
                "Damit erfülle ich insbesondere Anforderungen "
                f"wie {matched_text}."
            ),
        ])

    paragraphs.extend([
        "",
        (
            "Gern überzeuge ich Sie in einem persönlichen Gespräch "
            "von meiner Erfahrung und Motivation. "
            "Über die Einladung zu einem Kennenlernen freue ich mich."
        ),
        "",
        "Mit freundlichen Grüßen",
    ])

    formatted = []

    for paragraph in paragraphs:
        if not paragraph:
            formatted.append("")
        else:
            formatted.append(
                fill(
                    paragraph,
                    width=88,
                )
            )

    return "\n".join(formatted)


def main() -> None:
    print("Bewerbungshelfer AI")
    print("===================")

    print(
        "\nHinweis: Das Programm erfindet keine Qualifikationen.\n"
        "Bitte nur echte Erfahrungen und Kenntnisse eingeben.\n"
    )

    role = ask(
        "Stellenbezeichnung"
    )

    requirements_input = ask(
        "Anforderungen der Stelle"
    )

    experience = ask(
        "Deine passende Berufserfahrung"
    )

    qualifications_input = ask(
        "Deine Qualifikationen"
    )

    focus = ask(
        "Was soll besonders hervorgehoben werden"
    )

    requirements = split_items(
        requirements_input
    )

    qualifications = split_items(
        qualifications_input
    )

    matched, missing = compare_requirements(
        requirements,
        qualifications,
        experience,
    )

    print(
        "\n--- Vergleich ---\n"
    )

    print(
        build_summary(
            role,
            requirements,
            qualifications,
            matched,
            missing,
        )
    )

    print(
        "\n--- Anschreiben-Entwurf ---\n"
    )

    print(
        build_letter(
            role,
            experience,
            qualifications,
            focus,
            matched,
        )
    )


if __name__ == "__main__":
    main()
