"""
Temuclaude Web Search Module
Search-first policy for present-day facts.

Implements the mandatory search-first rule: for ANY factual question about the
present-day world (prices, versions, leaders, laws, current events, newest releases),
MUST search before answering.

Uses DuckDuckGo HTML endpoint (no API key required).
"""
import asyncio
import re
import urllib.parse
from typing import List, Dict, Optional
from datetime import datetime

try:
    import aiohttp
except ImportError:
    aiohttp = None


# Topics that require search (present-day facts)
SEARCH_TRIGGERS = [
    "price", "cost", "version", "latest", "new", "recent", "current",
    "today", "now", "2025", "2026", "release", "update", "announce",
    "news", "event", "happen", "who is", "what is the current",
    "president", "prime minister", "ceo", "leader", "champion",
    "winner", "score", "result", "standing", "ranking",
    "stock", "market", "weather", "forecast",
    "release date", "launch", "available", "on sale",
]

# Topics that do NOT need search
SEARCH_EXEMPTIONS = [
    "define", "what does x mean", "explain concept", "how does",
    "math", "calculate", "solve", "equation",
    "history of", "ancient", "medieval", "century",
    "theory", "philosophy", "hypothetical",
]


def should_search(query: str) -> bool:
    """Decide if a query needs web search.

    Returns True for present-day factual questions.
    Returns False for math, definitions, history, hypotheticals.
    """
    query_lower = query.lower().strip()

    # Check exemptions first
    for trigger in SEARCH_EXEMPTIONS:
        if trigger in query_lower:
            return False

    # Check triggers
    for trigger in SEARCH_TRIGGERS:
        if trigger in query_lower:
            return True

    # Default: don't search for short/opinion questions
    if len(query_lower.split()) < 4:
        return False

    return False


def format_search_query(query: str) -> str:
    """Clean and format a natural language query for search."""
    # Remove question words
    cleaned = re.sub(r"^(what is|what are|who is|who are|when|where|why|how|is|are|do|does|can|could|would|should)\s+", "", query, flags=re.IGNORECASE)
    # Remove trailing punctuation
    cleaned = cleaned.strip().rstrip("?.,!")
    # Take first 100 chars
    return cleaned[:100]


async def search_ddg(query: str, num_results: int = 5) -> List[Dict]:
    """Search DuckDuckGo and return results.

    Uses the HTML endpoint (no API key required).

    Returns list of dicts: {title, url, snippet}
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed. Run: pip install aiohttp")

    search_url = "https://html.duckduckgo.com/html/"
    params = {"q": query, "kl": "us-en"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(search_url, data=params, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()

    results = []

    # Parse results from HTML
    # DuckDuckGo HTML has results in .result__body blocks
    blocks = re.findall(r'<div class="result__body[^"]*">(.*?)</div>\s*(?:<div class="result__body|</div>\s*</div>)', html, re.DOTALL)

    if not blocks:
        # Try alternative parsing
        blocks = re.findall(r'class="result__(?:a|title)"[^>]*>(.*?)</a>', html, re.DOTALL)

    for block in blocks[:num_results]:
        # Extract title and URL
        title_match = re.search(r'result__a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        snippet_match = re.search(r'result__snippet[^>]*>(.*?)</(?:a|div|span)', block, re.DOTALL)

        if title_match:
            url = title_match.group(1)
            # DuckDuckGo wraps URLs in a redirect
            if "uddg=" in url:
                url = urllib.parse.unquote(url.split("uddg=")[1].split("&")[0])

            title = re.sub(r"<[^>]+>", "", title_match.group(2)).strip()
            snippet = ""
            if snippet_match:
                snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip()

            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })

    return results


async def search(query: str, num_results: int = 5) -> List[Dict]:
    """Search the web and return results.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of {title, url, snippet} dicts
    """
    formatted = format_search_query(query)
    return await search_ddg(formatted, num_results)


async def search_and_summarize(
    query: str,
    model_fn: Optional[callable] = None,
    num_results: int = 5,
) -> Dict:
    """Search the web and summarize results with an LLM.

    Args:
        query: Search query
        model_fn: Async function that takes messages and returns text
        num_results: Number of search results

    Returns:
        Dict with: query, results, summary
    """
    results = await search(query, num_results)

    if not results:
        return {"query": query, "results": [], "summary": "No results found."}

    if model_fn is None:
        # Build a simple text summary without LLM
        summary = "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
        return {"query": query, "results": results, "summary": summary}

    # Build context from results
    context = "\n\n".join(
        f"Source {i+1}: {r['title']}\nURL: {r['url']}\n{r['snippet']}"
        for i, r in enumerate(results)
    )

    messages = [
        {"role": "system", "content": "Summarize the search results to answer the user's question. Be concise and cite sources."},
        {"role": "user", "content": f"Question: {query}\n\nSearch results:\n{context}"},
    ]

    summary = await model_fn(messages)
    return {"query": query, "results": results, "summary": summary}


async def search_first_policy(
    query: str,
    model_fn: Optional[callable] = None,
) -> Optional[Dict]:
    """Implement the search-first policy.

    If the query needs search, search and return results + summary.
    If not, return None (no search needed).

    Args:
        query: User's question
        model_fn: Async LLM function for summarization

    Returns:
        Dict with results and summary if search was performed, None otherwise
    """
    if not should_search(query):
        return None

    return await search_and_summarize(query, model_fn)


async def search_recursive(query: str, depth: int = 2, num_results: int = 3) -> List[Dict]:
    """
    Recursive Academic Search Loop.
    Performs multi-step search queries to retrieve deep knowledge contexts for HLE academic questions.
    """
    all_results = []
    seen_urls = set()

    current_queries = [query]

    for d in range(depth):
        tasks = []
        for q in current_queries:
            tasks.append(search(q, num_results))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        next_queries = []
        for res in results_list:
            if isinstance(res, list):
                for item in res:
                    url = item["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(item)
                        # Extract potential keywords/entities from snippets/titles
                        words = re.findall(r'"([^"]+)"|\b([A-Z][a-zA-Z0-9-]{4,})\b', item["title"] + " " + item["snippet"])
                        for w_tuple in words[:2]:
                            w = w_tuple[0] or w_tuple[1]
                            if w and len(w) > 4 and w not in query:
                                next_queries.append(f"{query} {w}")

        if not next_queries:
            break
        current_queries = list(set(next_queries))[:2]  # Limit fanout

    return all_results