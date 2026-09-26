import unittest

from web_app import (
    app,
    calculate_match_rate,
    compare_requirements,
    extract_requirements,
    extract_role,
)


JOB_AD = """
Wir suchen zum nächstmöglichen Zeitpunkt einen zuverlässigen LKW-Fahrer /
Berufskraftfahrer für den regionalen Nahverkehr.

Ihre Aufgaben
• Be- und Entladen des LKW
• Auslieferung an Kunden

Ihr Profil
• Führerschein Klasse C/CE
• Gültige Fahrerkarte
• Berufskraftfahrerqualifikation / Module 95
• Mehrjährige Berufserfahrung als LKW-Fahrer von Vorteil
• Kenntnisse in der Ladungssicherung
• Gute Deutschkenntnisse
• Zuverlässige und selbstständige Arbeitsweise
• Pünktlichkeit und Verantwortungsbewusstsein
• Bereitschaft zu frühen Arbeitszeiten
• Erfahrung im Nahverkehr und in der Auslieferung von Vorteil

Wir bieten
• Geregelte Arbeitszeiten
• Einen sicheren Arbeitsplatz
• Faire Bezahlung
"""


class JobAdAnalysisTests(unittest.TestCase):
    def test_role_is_extracted_from_intro(self):
        role = extract_role(JOB_AD)
        self.assertIn("LKW-Fahrer", role)
        self.assertIn("Berufskraftfahrer", role)
        self.assertNotIn("Wir suchen", role)

    def test_benefits_and_tasks_are_not_requirements(self):
        requirements = extract_requirements(JOB_AD).splitlines()
        self.assertEqual(len(requirements), 10)
        self.assertTrue(any("Gute Deutschkenntnisse" in item for item in requirements))
        self.assertTrue(any("von Vorteil" in item for item in requirements))
        self.assertFalse(any("Geregelte Arbeitszeiten" in item for item in requirements))
        self.assertFalse(any("Faire Bezahlung" in item for item in requirements))
        self.assertFalse(any("Be- und Entladen" in item for item in requirements))

    def test_profile_sources_are_combined_but_czv_is_not_module_95(self):
        requirements = extract_requirements(JOB_AD).splitlines()
        matched, missing, details = compare_requirements(
            requirements,
            "Mehrjährige Berufserfahrung als LKW-Fahrer im Nahverkehr.",
            "Führerschein C, CE, Fahrerkarte, CZV, Ladungssicherung",
        )
        self.assertTrue(any("Berufserfahrung" in item for item in matched))
        self.assertTrue(any("Module 95" in item for item in missing))
        self.assertFalse(any("Geregelte Arbeitszeiten" in item for item in details))
        self.assertEqual(calculate_match_rate(details), 39)

    def test_current_job_ad_replaces_old_requirements(self):
        client = app.test_client()
        response = client.post(
            "/",
            data={
                "action": "analyze",
                "job_ad": JOB_AD,
                "role": "",
                "requirements": "Geregelte Arbeitszeiten\nAlte Anforderung",
                "experience": "Mehrjährige Berufserfahrung als LKW-Fahrer",
                "qualifications": "Führerschein CE, Fahrerkarte, CZV",
                "focus": "",
            },
        )
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Module 95", body)
        self.assertNotIn("Alte Anforderung", body)
        self.assertNotIn("Geregelte Arbeitszeiten</li>", body)


if __name__ == "__main__":
    unittest.main()
