"""
Temuclaude Browser Automation Module
Web interaction — fetch, parse, extract content from web pages.

Uses aiohttp for async HTTP, BeautifulSoup for HTML parsing.
No browser process needed — HTTP fetch + HTML parsing.
"""
import asyncio
import re
from typing import Optional, List, Dict, Callable
from urllib.parse import urljoin, urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def validate_url(url: str) -> bool:
    """Validate that a URL is well-formed."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.netloc
    except Exception:
        return False


async def fetch_page(url: str, timeout: int = 15) -> str:
    """Fetch a web page and return the HTML content.

    Args:
        url: URL to fetch
        timeout: Timeout in seconds

    Returns:
        HTML content as string
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed. Run: pip install aiohttp")

    if not validate_url(url):
        raise ValueError(f"Invalid URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True,
        ) as resp:
            return await resp.text()


def extract_text(html: str) -> str:
    """Extract main content text from HTML.

    Removes scripts, styles, and extracts text from body.
    """
    if BeautifulSoup is None:
        # Fallback: regex-based extraction
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to find main content
    main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|main|article", re.I))
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def extract_links(html: str, base_url: str = "") -> List[Dict]:
    """Extract all links from HTML.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links

    Returns:
        List of {text, url} dicts
    """
    links = []

    if BeautifulSoup is None:
        # Fallback: regex
        for match in re.finditer(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            url = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if base_url:
                url = urljoin(base_url, url)
            if text and url:
                links.append({"text": text, "url": url})
        return links

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if base_url:
            href = urljoin(base_url, href)
        if text and href:
            links.append({"text": text, "url": href})

    return links


def extract_structured(html: str, selector: str) -> List[str]:
    """Extract content by CSS selector.

    Args:
        html: HTML content
        selector: CSS selector (simplified: tag, .class, #id)

    Returns:
        List of extracted text strings
    """
    if BeautifulSoup is None:
        # Fallback: very basic regex
        if selector.startswith("."):
            cls = selector[1:]
            pattern = rf'class="[^"]*{cls}[^"]*"[^>]*>(.*?)</\w+>'
        elif selector.startswith("#"):
            idv = selector[1:]
            pattern = rf'id="{idv}"[^>]*>(.*?)</\w+>'
        else:
            pattern = rf'<{selector}[^>]*>(.*?)</{selector}>'
        return [re.sub(r'<[^>]+>', '', m).strip() for m in re.findall(pattern, html, re.DOTALL)]

    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(selector)
    return [el.get_text(strip=True) for el in elements]


async def fetch_and_extract(url: str, timeout: int = 15) -> Dict:
    """Fetch a URL and extract text content.

    Returns:
        Dict with: url, title, text, links
    """
    html = await fetch_page(url, timeout)

    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else url

    text = extract_text(html)
    links = extract_links(html, url)

    return {
        "url": url,
        "title": title,
        "text": text[:5000],  # Limit to 5000 chars
        "links": links[:20],  # Limit to 20 links
    }


async def summarize_page(
    url: str,
    model_fn: Optional[Callable] = None,
    timeout: int = 15,
) -> Dict:
    """Fetch a page and summarize its content.

    Args:
        url: URL to summarize
        model_fn: Async LLM function for summarization
        timeout: Fetch timeout

    Returns:
        Dict with: url, title, summary
    """
    page = await fetch_and_extract(url, timeout)

    if model_fn:
        messages = [
            {"role": "system", "content": "Summarize the following web page content concisely."},
            {"role": "user", "content": f"Title: {page['title']}\n\nContent:\n{page['text'][:3000]}"},
        ]
        summary = await model_fn(messages)
    else:
        # Fallback: first 500 chars
        summary = page["text"][:500]

    return {
        "url": url,
        "title": page["title"],
        "summary": summary,
    }


def detect_url_in_query(text: str) -> Optional[str]:
    """Detect a URL in user text."""
    match = re.search(r'https?://[^\s<>"\']+', text)
    return match.group(0) if match else None