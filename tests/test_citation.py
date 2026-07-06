"""Tests for citation module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.citation import (
    Citation, CitationTracker, add_citations,
    format_footnotes, format_inline
)


def test_citation_construction():
    c = Citation(index=1, source="Example", sentence="A fact", url="http://example.com")
    assert c.index == 1
    assert c.source == "Example"
    assert c.url == "http://example.com"


def test_citation_tracker_add():
    tracker = CitationTracker()
    c = tracker.add_source("Test Source", "Test sentence")
    assert c.index == 1
    assert len(tracker.citations) == 1


def test_citation_tracker_multiple():
    tracker = CitationTracker()
    tracker.add_source("Source A", "Fact A")
    tracker.add_source("Source B", "Fact B")
    assert len(tracker.citations) == 2
    assert tracker.citations[1].index == 2


def test_format_footnotes():
    tracker = CitationTracker()
    tracker.add_source("Wikipedia", "A fact", "http://wikipedia.org")
    result = tracker.format_footnotes()
    assert "Sources:" in result
    assert "[1]" in result
    assert "Wikipedia" in result


def test_format_inline():
    tracker = CitationTracker()
    tracker.add_source("Test", "Some excerpt")
    result = tracker.format_inline()
    assert "[1]" in result
    assert "Test" in result


def test_add_citations():
    text = "This is a response."
    sources = [{"title": "Source A", "url": "http://a.com", "snippet": "Fact A"}]
    result = add_citations(text, sources)
    assert "Sources:" in result
    assert "Source A" in result


def test_add_citations_empty():
    text = "Just text"
    result = add_citations(text, [])
    assert result == "Just text"


def test_format_footnotes_empty():
    tracker = CitationTracker()
    assert tracker.format_footnotes() == ""


def test_add_citations_from_search():
    tracker = CitationTracker()
    results = [
        {"title": "A", "url": "http://a.com", "snippet": "Snippet A"},
        {"title": "B", "url": "http://b.com", "snippet": "Snippet B"},
    ]
    tracker.add_citations_from_search(results)
    assert len(tracker.citations) == 2