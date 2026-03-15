import pytest
from server import _deduplicate_results


def test_dedup_removes_duplicate_dois():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: 10.1234/test\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 1 copy**\n  DOI: 10.1234/test\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 1
    assert "Source: A" in result[0]
    assert "all results were duplicates" in result[1]


def test_dedup_keeps_unique_papers():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: 10.1234/aaa\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 2**\n  DOI: 10.1234/bbb\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 0
    assert "Paper 1" in result[0]
    assert "Paper 2" in result[1]


def test_dedup_keeps_papers_without_doi():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: Not available\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 2**\n  DOI: Not available\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 0


def test_dedup_case_insensitive():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: 10.1234/ABC\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 1**\n  DOI: 10.1234/abc\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 1


def test_dedup_preserves_unavailable_sections():
    sections = [
        "=== Source A ===\nSource A unavailable (rate limit exceeded).",
        "=== Source B Results ===\n\n**Paper 1**\n  DOI: 10.1234/test\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 0
    assert "unavailable" in result[0]
    assert "Paper 1" in result[1]


def test_dedup_multiple_papers_per_section():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: 10.1234/aaa\n  [Source: A]\n\n**Paper 2**\n  DOI: 10.1234/bbb\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 1 copy**\n  DOI: 10.1234/aaa\n  [Source: B]\n\n**Paper 3**\n  DOI: 10.1234/ccc\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 1
    # Paper 3 should still be in Source B
    assert "Paper 3" in result[1]
    # Paper 1 copy should be removed
    assert "Paper 1 copy" not in "\n".join(result)


def test_dedup_strips_trailing_punctuation_from_doi():
    sections = [
        "=== Source A Results ===\n\n**Paper 1**\n  DOI: 10.1234/test.\n  [Source: A]",
        "=== Source B Results ===\n\n**Paper 1**\n  DOI: 10.1234/test\n  [Source: B]",
    ]
    result, removed = _deduplicate_results(sections)
    assert removed == 1
