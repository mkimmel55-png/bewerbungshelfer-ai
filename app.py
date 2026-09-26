"""
Bewerbungshelfer AI
Version 0.5.0
"""

import re
from textwrap import fill


def ask(label: str) -> str:
    return input(f"{label}: ").strip()


def split_items(text: str) -> list[str]:
    """
    Trennt Eingaben an Kommas oder Semikolons
    und entfernt leere Einträge.
    """
    text = text.replace(";", ",")
    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


def normalize(text: str) -> str:
    return text.lower().strip()


def word_set(text: str) -> set[str]:
    """
    Zerlegt Text in einzelne Wörter.
    Zahlen und deutsche Umlaute bleiben erhalten.
    """
    return set(
        re.findall(
            r"[a-zA-ZäöüÄÖÜß0-9]+",
            normalize(text),
        )
    )


def requirement_matches(
    requirement: str,
    qualification: str,
) -> bool:
    """
    Prüft, ob eine Anforderung zu einer Qualifikation passt.

    Zuerst wird auf direkte Textübereinstimmung geprüft.
    Danach werden gemeinsame Wörter verglichen.
    """

    req = normalize(requirement)
    qual = normalize(qualification)

    if not req or not qual:
        return False

    # Direkter Treffer
    if req in qual or qual in req:
        return True

    req_words = word_set(req)
    qual_words = word_set(qual)

    if not req_words or not qual_words:
        return False

    common_words = req_words & qual_words

    # Anteil gemeinsamer Wörter bezogen auf die Anforderung
    score = len(common_words) / len(req_words)

    return score >= 0.5


def compare_requirements(
    requirements: list[str],
    qualifications: list[str],
) -> tuple[list[str], list[str]]:
    """
    Vergleicht Anforderungen flexibler mit vorhandenen
    Qualifikationen.
    """

    matched = []
    missing = []

    for requirement in requirements:

        found = any(
            requirement_matches(
                requirement,
                qualification,
            )
            for qualification in qualifications
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
    Berechnet die Trefferquote in Prozent.
    """

    if not requirements:
        return 0

    return round(
        len(matched) / len(requirements) * 100
    )


def build_summary(
    role: str,
    requirements: list[str],
    qualifications: list[str],
    matched: list[str],
    missing: list[str],
) -> str:

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


def build_letter(
    role: str,
    experience: str,
    qualifications: list[str],
    focus: str,
    matched: list[str],
) -> str:

    strengths = []

    if experience:
        strengths.append(experience)

    if qualifications:
        strengths.extend(qualifications)

    if focus:
        strengths.append(focus)

    strengths_text = ", ".join(strengths)

    if not strengths_text:
        strengths_text = (
            "meine bisherige Berufserfahrung "
            "und meine Motivation"
        )

    matched_text = ""

    if matched:
        matched_text = (
            " Besonders passend zu den Anforderungen sind "
            + ", ".join(matched)
            + "."
        )

    text = (
        "Sehr geehrte Damen und Herren,\n\n"
        f"hiermit bewerbe ich mich auf die Position als {role}. "
        f"Für die Stelle bringe ich insbesondere "
        f"{strengths_text} mit."
        f"{matched_text} "
        "Gern erläutere ich Ihnen in einem persönlichen Gespräch, "
        "wie ich meine Erfahrung in Ihrem Unternehmen "
        "einbringen kann.\n\n"
        "Mit freundlichen Grüßen"
    )

    return "\n".join(
        fill(paragraph, width=88)
        if paragraph
        else ""
        for paragraph in text.split("\n")
    )


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
        "Anforderungen der Stelle "
        "(mit Komma trennen)"
    )

    experience = ask(
        "Deine passende Berufserfahrung"
    )

    qualifications_input = ask(
        "Deine Qualifikationen "
        "(mit Komma trennen)"
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
