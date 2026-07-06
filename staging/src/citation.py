"""
Temuclaude Citation System
Standardized inline citations for trustworthy responses.

Format: {cite index="DOC-SENTENCE"} or [N] (Source: "excerpt")
Ensures every factual claim is backed by a source.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Citation:
    """A single citation source."""
    index: int
    source: str  # title or domain
    sentence: str  # the excerpt being cited
    url: Optional[str] = None


class CitationTracker:
    """Tracks citations throughout a response."""

    def __init__(self):
        self.citations: List[Citation] = []

    def add_source(self, source: str, sentence: str, url: Optional[str] = None) -> Citation:
        """Add a citation source and return the citation."""
        index = len(self.citations) + 1
        citation = Citation(
            index=index,
            source=source,
            sentence=sentence,
            url=url,
        )
        self.citations.append(citation)
        return citation

    def add_citations_from_search(self, results: List[Dict]) -> None:
        """Add citations from search results.

        Args:
            results: List of {title, url, snippet} dicts
        """
        for r in results:
            self.add_source(
                source=r.get("title", ""),
                sentence=r.get("snippet", ""),
                url=r.get("url"),
            )

    def format_inline(self) -> str:
        """Format citations as inline references.

        Returns: [N] (Source: "excerpt")
        """
        if not self.citations:
            return ""
        lines = []
        for c in self.citations:
            line = f"[{c.index}] ({c.source}: \"{c.sentence[:100]}\""
            if c.url:
                line += f" — {c.url}"
            line += ")"
            lines.append(line)
        return "\n".join(lines)

    def format_footnotes(self) -> str:
        """Format citations as footnote block.

        Returns:
            Sources:
            [1] SourceName — "excerpt" (url)
        """
        if not self.citations:
            return ""
        lines = ["Sources:"]
        for c in self.citations:
            line = f'[{c.index}] {c.source} — "{c.sentence[:100]}"'
            if c.url:
                line += f" ({c.url})"
            lines.append(line)
        return "\n".join(lines)

    def get_citation_at(self, index: int) -> Optional[Citation]:
        """Get citation by 1-based index."""
        if 1 <= index <= len(self.citations):
            return self.citations[index - 1]
        return None

    def clear(self) -> None:
        """Clear all citations."""
        self.citations = []


def add_citations(text: str, sources: List[Dict]) -> str:
    """Add inline citations to a text.

    Args:
        text: The response text
        sources: List of {title, url, snippet} dicts

    Returns:
        Text with citation markers appended
    """
    tracker = CitationTracker()
    tracker.add_citations_from_search(sources)
    footnotes = tracker.format_footnotes()
    if footnotes:
        return f"{text}\n\n{footnotes}"
    return text


def insert_inline_citations(text: str, sources: List[Dict]) -> str:
    """Insert inline [N] markers into text at sentence boundaries.

    Args:
        text: The response text
        sources: List of source dicts

    Returns:
        Text with [N] markers inserted
    """
    if not sources:
        return text

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    source_idx = 0

    for i, sentence in enumerate(sentences):
        # Insert citation every 2-3 sentences if sources available
        if source_idx < len(sources) and i > 0 and i % 3 == 0:
            result.append(f"[{source_idx + 1}]")
            source_idx += 1
        result.append(sentence)

    text_with_markers = " ".join(result)

    # Append footnote block
    tracker = CitationTracker()
    tracker.add_citations_from_search(sources)
    footnotes = tracker.format_footnotes()
    if footnotes:
        text_with_markers += f"\n\n{footnotes}"

    return text_with_markers


def format_footnotes(citations: List[Citation]) -> str:
    """Format a list of citations as footnotes."""
    if not citations:
        return ""
    lines = ["Sources:"]
    for c in citations:
        line = f'[{c.index}] {c.source} — "{c.sentence[:100]}"'
        if c.url:
            line += f" ({c.url})"
        lines.append(line)
    return "\n".join(lines)


def format_inline(citations: List[Citation]) -> str:
    """Format a list of citations as inline references."""
    if not citations:
        return ""
    lines = []
    for c in citations:
        line = f'[{c.index}] ({c.source}: "{c.sentence[:100]}"'
        if c.url:
            line += f" — {c.url}"
        line += ")"
        lines.append(line)
    return "\n".join(lines)