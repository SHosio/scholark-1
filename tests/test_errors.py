# tests/test_errors.py
from apis.errors import SourceUnavailable, RateLimited


def test_source_unavailable_stores_source_and_reason():
    err = SourceUnavailable("Semantic Scholar", "no results")
    assert err.source == "Semantic Scholar"
    assert err.reason == "no results"


def test_source_unavailable_default_reason():
    err = SourceUnavailable("Crossref")
    assert err.reason == ""


def test_rate_limited_is_source_unavailable():
    err = RateLimited("Semantic Scholar")
    assert isinstance(err, SourceUnavailable)
    assert err.source == "Semantic Scholar"
    assert err.reason == "rate limit exceeded"
