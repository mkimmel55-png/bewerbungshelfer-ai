"""Bewerbungshelfer AI command-line application."""

import re
from textwrap import fill


APP_VERSION = "0.8.0"


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
