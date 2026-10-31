"""LinkedIn-Stellenanzeigen über Apify abrufen.

Token und Actor stehen in den Streamlit-Secrets:

    [apify]
    token = "apify_api_..."
    actor = "curious_coder~linkedin-jobs-scraper"   # optional

Hinweis: Das Scraping von LinkedIn verstößt gegen deren Nutzungsbedingungen.
Das Eingabeformat und die Ausgabefelder hängen vom gewählten Actor ab und
müssen vor dem Produktiveinsatz gegen dessen Doku geprüft werden.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ACTOR = "curious_coder~linkedin-jobs-scraper"
API_BASE = "https://api.apify.com/v2"


def build_search_url(keywords: str, location: str) -> str:
    query = urllib.parse.urlencode(
        {"keywords": keywords, "location": location}
    )
    return f"https://www.linkedin.com/jobs/search/?{query}"


def parse_items(items: list) -> list:
    """Vereinheitlicht die Actor-Ausgabe auf feste Felder."""
    jobs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        description = (
            item.get("descriptionText")
            or item.get("description")
            or ""
        )
        jobs.append(
            {
                "title": item.get("title") or item.get("jobTitle") or "",
                "company": item.get("companyName") or item.get("company") or "",
                "location": item.get("location") or "",
                "url": item.get("link") or item.get("url") or "",
                "description": str(description).strip(),
            }
        )
    return [job for job in jobs if job["title"] or job["description"]]


def search_jobs(
    token: str,
    keywords: str,
    location: str,
    limit: int = 10,
    actor: str = DEFAULT_ACTOR,
    timeout: int = 120,
) -> list:
    if not token:
        raise RuntimeError("Apify-Token fehlt.")
    if not keywords.strip():
        raise ValueError("Bitte einen Suchbegriff angeben.")

    endpoint = (
        f"{API_BASE}/acts/{actor}/run-sync-get-dataset-items"
        f"?{urllib.parse.urlencode({'token': token})}"
    )
    payload = json.dumps(
        {
            "urls": [build_search_url(keywords, location)],
            "count": max(1, int(limit)),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            items = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Apify-Fehler {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Apify nicht erreichbar.") from exc

    return parse_items(items if isinstance(items, list) else [])
