import pytest

from apify_jobs import build_search_url, parse_items, search_jobs


def test_build_search_url_encodes_params():
    url = build_search_url("LKW Fahrer", "Freiburg im Breisgau")
    assert "keywords=LKW+Fahrer" in url
    assert "location=Freiburg+im+Breisgau" in url


def test_parse_items_normalizes_and_filters():
    items = [
        {"title": "Fahrer CE", "companyName": "ACME", "link": "u",
         "descriptionText": " Text "},
        {"jobTitle": "Fahrer", "company": "B", "description": "d"},
        {},
        "kaputt",
    ]
    jobs = parse_items(items)
    assert len(jobs) == 2
    assert jobs[0]["company"] == "ACME"
    assert jobs[0]["description"] == "Text"
    assert jobs[1]["title"] == "Fahrer"


def test_search_jobs_requires_token_and_keywords():
    with pytest.raises(RuntimeError):
        search_jobs("", "Fahrer", "Freiburg")
    with pytest.raises(ValueError):
        search_jobs("t", "  ", "Freiburg")
