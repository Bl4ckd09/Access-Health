"""Upstream failures must not disclose private details to API clients."""
import sys
from pathlib import Path
import urllib.request

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import llm
from data import ingest_companies
from server import app as server


def _fail(*args, **kwargs):
    raise RuntimeError("upstream token: private-secret")


def test_lookup_hides_upstream_exception(monkeypatch):
    monkeypatch.setattr(server, "CH_KEY", "test-key")
    monkeypatch.setattr(ingest_companies, "search_by_name", _fail)

    response = server.app.test_client().post("/api/lookup", json={"query": "Example Ltd"})

    assert response.status_code == 200
    assert response.json["error"] == "companies_house_error"
    assert "private-secret" not in response.get_data(as_text=True)

def test_companies_at_hides_upstream_exception(monkeypatch):
    monkeypatch.setattr(server, "CH_KEY", "test-key")
    monkeypatch.setattr(urllib.request, "urlopen", _fail)

    response = server.app.test_client().post("/api/companies-at", json={"postcode": "SW1A 1AA"})

    assert response.status_code == 200
    assert response.json["error"] == "Company lookup failed"
    assert "private-secret" not in response.get_data(as_text=True)


def test_draft_stream_hides_upstream_exception(monkeypatch):
    monkeypatch.setattr(llm, "stream_chat", _fail)

    response = server.app.test_client().post("/api/draft-email", json={"business": {}})

    assert response.status_code == 200
    assert "Draft generation failed" in response.get_data(as_text=True)
    assert "private-secret" not in response.get_data(as_text=True)
