"""Tests for browser module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.browser import (
    validate_url, extract_text, extract_links, detect_url_in_query
)


def test_validate_url_valid():
    assert validate_url("https://example.com") == True
    assert validate_url("http://example.com/page") == True


def test_validate_url_invalid():
    assert validate_url("not a url") == False
    assert validate_url("ftp://example.com") == False


def test_extract_text_basic():
    html = "<html><body><p>Hello world</p></body></html>"
    text = extract_text(html)
    assert "Hello world" in text


def test_extract_text_removes_scripts():
    html = "<html><body><script>alert('xss')</script><p>Content</p></body></html>"
    text = extract_text(html)
    assert "alert" not in text
    assert "Content" in text


def test_extract_text_removes_styles():
    html = "<html><body><style>.cls{color:red}</style><p>Text</p></body></html>"
    text = extract_text(html)
    assert "color" not in text
    assert "Text" in text


def test_extract_links():
    html = '<html><body><a href="https://example.com">Example</a><a href="/page2">Page2</a></body></html>'
    links = extract_links(html, base_url="https://example.com")
    assert len(links) >= 1
    assert any("Example" in l["text"] for l in links)


def test_extract_links_empty():
    html = "<html><body><p>No links here</p></body></html>"
    links = extract_links(html)
    assert len(links) == 0


def test_detect_url_in_query():
    assert detect_url_in_query("Check https://example.com/page") is not None
    assert detect_url_in_query("No URL here") is None


def test_extract_text_empty():
    assert extract_text("") == ""