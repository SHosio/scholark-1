import time
import pytest
from cache import CacheDB


@pytest.fixture
def db(tmp_path):
    """Create a cache DB in a temp directory."""
    db_path = tmp_path / "test.db"
    return CacheDB(str(db_path))


def test_put_and_get(db):
    db.put("paper_details:10.1234/foo", "some data", "Semantic Scholar")
    assert db.get("paper_details:10.1234/foo") == "some data"


def test_get_missing_key(db):
    assert db.get("paper_details:10.9999/missing") is None


def test_put_overwrites(db):
    db.put("bibtex:10.1234/foo", "old", "Crossref")
    db.put("bibtex:10.1234/foo", "new", "Crossref")
    assert db.get("bibtex:10.1234/foo") == "new"


def test_expired_entry_returns_none(db):
    db.put("paper_details:10.1234/old", "stale data", "Crossref")
    expired_time = time.time() - (31 * 86400)
    db._conn.execute(
        "UPDATE cache SET created_at = ? WHERE key = ?",
        (expired_time, "paper_details:10.1234/old"),
    )
    db._conn.commit()
    assert db.get("paper_details:10.1234/old") is None


def test_bibtex_ttl_longer_than_paper_details(db):
    db.put("bibtex:10.1234/foo", "bibtex data", "Crossref")
    almost_expired = time.time() - (89 * 86400)
    db._conn.execute(
        "UPDATE cache SET created_at = ? WHERE key = ?",
        (almost_expired, "bibtex:10.1234/foo"),
    )
    db._conn.commit()
    assert db.get("bibtex:10.1234/foo") == "bibtex data"


def test_unknown_prefix_returns_none(db):
    """Keys with unknown prefixes should not be retrievable (no TTL defined)."""
    db.put("unknown:key", "data", "test")
    assert db.get("unknown:key") is None


def test_db_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b" / "papers.db"
    db = CacheDB(str(nested))
    db.put("bibtex:10.1234/foo", "data", "test")
    assert db.get("bibtex:10.1234/foo") == "data"
