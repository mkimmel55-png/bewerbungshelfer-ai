"""
Bewerbungshelfer AI
Einfache lokale Basisversion.
"""

from textwrap import fill


def ask(label: str) -> str:
    return input(f"{label}: ").strip()


def build_summary(
    role: str,
    requirements: str,
    experience: str,
    qualifications: str,
) -> str:
    return (
        f"Zielstelle: {role}\n\n"
        f"Anforderungen:\n{requirements or '- keine Angaben'}\n\n"
        f"Berufserfahrung:\n{experience or '- keine Angaben'}\n\n"
        f"Qualifikationen:\n{qualifications or '- keine Angaben'}"
    )


def build_letter(
    role: str,
    experience: str,
    qualifications: str,
    focus: str,
) -> str:
    details = [experience, qualifications, focus]

    strengths = ", ".join(
        item.strip()
        for item in details
        if item.strip()
    )

    if not strengths:
        strengths = "meine bisherige Berufserfahrung und meine Motivation"

    text = (
        "Sehr geehrte Damen und Herren,\n\n"
        f"hiermit bewerbe ich mich auf die Position als {role}. "
        f"Für die Stelle bringe ich insbesondere {strengths} mit. "
        "Gern erläutere ich Ihnen in einem persönlichen Gespräch, "
        "wie ich meine Erfahrung in Ihrem Unternehmen einbringen kann.\n\n"
        "Mit freundlichen Grüßen"
    )

    return "\n".join(
        fill(paragraph, width=88) if paragraph else ""
        for paragraph in text.split("\n")
    )


def main() -> None:
    print("Bewerbungshelfer AI")
    print("===================")

    print(
        "\nBitte keine Qualifikationen eingeben, "
        "die du nicht wirklich besitzt.\n"
    )

    role = ask("Stellenbezeichnung")
    requirements = ask("Wichtigste Anforderungen aus der Stellenanzeige")
    experience = ask("Deine passende Berufserfahrung")
    qualifications = ask("Deine relevanten Qualifikationen")
    focus = ask("Was soll besonders hervorgehoben werden")

    print("\n--- Strukturierte Zusammenfassung ---\n")
    print(
        build_summary(
            role,
            requirements,
            experience,
            qualifications,
        )
    )

    print("\n--- Anschreiben-Entwurf ---\n")
    print(
        build_letter(
            role,
            experience,
            qualifications,
            focus,
        )
    )


if __name__ == "__main__":
    main()
