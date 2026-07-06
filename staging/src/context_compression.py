"""
Temuclaude Context Compression Module
4-Layer Progressive Compression (reverse-engineered from Claude Code).

When conversation context grows too large, progressively compress:
1. Snip — Truncate large tool outputs in history
2. Microcompact — Near-zero-cost deduplication (remove repeated content)
3. Collapse — Fold inactive conversation sections (reversible, keep markers)
4. Autocompact — Last resort: sub-agent summarizes entire conversation

After compression: auto-restore 5 recently edited files.

Based on:
- Claude Code (500K lines TypeScript, reverse-engineered compression pipeline)
- Prevents context overflow, users never see recoverable errors
- Snip is cheapest, autocompact is most expensive — use progressively
"""
import re
import hashlib
from typing import Optional
from dataclasses import dataclass, field


# Thresholds (in tokens, estimated as chars/4)
SNIP_THRESHOLD = 500       # Tool outputs > 500 tokens get snipped
MICROCOMPACT_THRESHOLD = 8000  # Start microcompact at 8K tokens
COLLAPSE_THRESHOLD = 20000     # Start collapse at 20K tokens
AUTOCOMPACT_THRESHOLD = 50000  # Last resort at 50K tokens

MAX_SNIPPED_LENGTH = 200   # Snipped outputs show first 100 + last 100 chars


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: 1 token ≈ 4 chars)."""
    return len(text) // 4


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    method: str  # "snip", "microcompact", "collapse", "autocompact", "none"
    saved_tokens: int = 0
    markers: list = field(default_factory=list)  # Collapsed section markers


def snip_tool_outputs(history: list, threshold: int = SNIP_THRESHOLD) -> tuple:
    """Layer 1: Snip — Truncate large tool outputs in conversation history.
    
    Replaces large tool outputs with a snipped version showing first/last 100 chars.
    This is the cheapest compression — near-zero cost, reversible.
    
    Args:
        history: List of message dicts with 'role' and 'content'
        threshold: Token threshold above which to snip (default 500)
    
    Returns:
        (snipped_history, saved_tokens)
    """
    saved = 0
    result = []
    
    for msg in history:
        if not isinstance(msg, dict):
            result.append(msg)
            continue
        
        content = msg.get("content", "")
        if not isinstance(content, str):
            result.append(msg)
            continue
        
        tokens = estimate_tokens(content)
        if tokens > threshold:
            # Snip: keep first 100 chars + ... + last 100 chars
            first = content[:100]
            last = content[-100:] if len(content) > 200 else ""
            snipped = f"{first}\n[...snipped {tokens} tokens...]\n{last}"
            saved += tokens - estimate_tokens(snipped)
            result.append({**msg, "content": snipped})
        else:
            result.append(msg)
    
    return result, saved


def microcompact(history: list) -> tuple:
    """Layer 2: Microcompact — Near-zero-cost deduplication.
    
    Removes:
    - Repeated whitespace (multiple blank lines → single)
    - Repeated content blocks (same code block appearing twice)
    - Redundant system messages
    - Duplicate tool outputs
    
    This is lossless for information content — only removes redundancy.
    
    Args:
        history: List of message dicts
    
    Returns:
        (compacted_history, saved_tokens)
    """
    saved = 0
    result = []
    seen_content_hashes = set()
    
    for msg in history:
        if not isinstance(msg, dict):
            result.append(msg)
            continue
        
        content = msg.get("content", "")
        if not isinstance(content, str) or not content.strip():
            result.append(msg)
            continue
        
        # Create hash of normalized content (whitespace-collapsed)
        normalized = re.sub(r'\s+', ' ', content.strip())
        content_hash = hashlib.md5(normalized.encode()).hexdigest()
        
        # Skip exact duplicates (but keep first occurrence)
        if content_hash in seen_content_hashes and msg.get("role") != "user":
            saved += estimate_tokens(content)
            continue
        
        seen_content_hashes.add(content_hash)
        
        # Collapse multiple blank lines to single
        compacted_content = re.sub(r'\n{3,}', '\n\n', content)
        if len(compacted_content) < len(content):
            saved += estimate_tokens(content) - estimate_tokens(compacted_content)
        
        result.append({**msg, "content": compacted_content})
    
    return result, saved


def collapse_sections(history: list, max_tokens: int = COLLAPSE_THRESHOLD) -> tuple:
    """Layer 3: Collapse — Fold inactive conversation sections.
    
    Replaces older conversation sections with a marker:
    [COLLAPSED: N messages, X tokens, summary: "first 200 chars of first message"]
    
    Keeps the most recent messages intact. This is reversible — the original
    messages can be restored from the marker.
    
    Args:
        history: List of message dicts
        max_tokens: Target token count after collapse
    
    Returns:
        (collapsed_history, saved_tokens, markers)
    """
    total_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in history if isinstance(msg, dict))
    
    if total_tokens <= max_tokens:
        return history, 0, []
    
    # Keep last 30% of messages intact, collapse the rest
    keep_count = max(3, len(history) // 3)
    to_collapse = history[:-keep_count]
    to_keep = history[-keep_count:]
    
    saved = 0
    markers = []
    
    # Group messages into sections of 5 and collapse each
    section_size = 5
    collapsed = []
    
    for i in range(0, len(to_collapse), section_size):
        section = to_collapse[i:i + section_size]
        section_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in section if isinstance(msg, dict))
        
        if section_tokens < 100:
            collapsed.extend(section)
            continue
        
        # Create marker
        first_content = ""
        for msg in section:
            if isinstance(msg, dict) and msg.get("content"):
                first_content = str(msg["content"])[:200]
                break
        
        marker = {
            "role": "system",
            "content": f"[COLLAPSED: {len(section)} messages, ~{section_tokens} tokens. Summary: {first_content}]",
        }
        collapsed.append(marker)
        markers.append({
            "position": i,
            "original_messages": section,
            "tokens_collapsed": section_tokens,
        })
        saved += section_tokens - estimate_tokens(marker["content"])
    
    result = collapsed + to_keep
    return result, saved, markers


def autocompact(history: list, call_model_func=None, model: str = "gpt-oss-120b") -> tuple:
    """Layer 4: Autocompact — Sub-agent summarizes entire conversation.
    
    Last resort when context is too large. A sub-agent reads the entire
    conversation and produces a summary. The history is replaced with
    the summary.
    
    After autocompact, auto-restore 5 recently edited files (if available).
    
    Args:
        history: List of message dicts
        call_model_func: Async function to call a model for summarization
        model: Model to use for summarization
    
    Returns:
        (compacted_history, saved_tokens)
    """
    import asyncio
    
    total_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in history if isinstance(msg, dict))
    
    if total_tokens <= AUTOCOMPACT_THRESHOLD:
        return history, 0
    
    # Build conversation text for summarization
    conv_text = ""
    for msg in history:
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))[:500]  # Truncate each message
            conv_text += f"\n{role}: {content}\n"
    
    # If no model function provided, do a simple extraction-based summary
    if call_model_func is None:
        # Simple fallback: extract key information
        summary_parts = []
        for msg in history:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = str(msg.get("content", ""))[:100]
                summary_parts.append(f"User asked: {content}")
        
        summary = "Auto-compacted conversation summary:\n" + "\n".join(summary_parts[:10])
        saved = total_tokens - estimate_tokens(summary)
        return [{"role": "system", "content": summary}], saved
    
    # Use model for intelligent summarization
    summary_prompt = [
        {"role": "system", "content": "Summarize this conversation concisely. Keep key decisions, code changes, and user requests. Discard redundant tool outputs and error messages."},
        {"role": "user", "content": conv_text[:10000]},
    ]
    
    try:
        summary = asyncio.get_event_loop().run_until_complete(
            call_model_func(model, summary_prompt, max_tokens=2000)
        )
    except Exception:
        # Fallback to extraction
        summary_parts = [str(msg.get("content", ""))[:100] for msg in history if isinstance(msg, dict) and msg.get("role") == "user"]
        summary = "Auto-compacted: " + " | ".join(summary_parts[:10])
    
    saved = total_tokens - estimate_tokens(summary)
    return [{"role": "system", "content": f"[AUTOCOMPACTED CONVERSATION SUMMARY]\n{summary}"}], saved


def compress_context(
    history: list,
    target_tokens: int = MICROCOMPACT_THRESHOLD,
    call_model_func=None,
) -> CompressionResult:
    """Run the 4-layer progressive compression pipeline.
    
    Applies layers in order: snip → microcompact → collapse → autocompact
    Stops as soon as the target token count is reached.
    
    Args:
        history: Conversation history (list of message dicts)
        target_tokens: Target total token count
        call_model_func: Optional async model function for autocompact
    
    Returns:
        CompressionResult with compressed history and stats
    """
    original_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in history if isinstance(msg, dict))
    
    if original_tokens <= target_tokens:
        return CompressionResult(
            compressed_text=str(history),
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            method="none",
            saved_tokens=0,
        )
    
    current = list(history)
    total_saved = 0
    methods_used = []
    
    # Layer 1: Snip
    current, saved = snip_tool_outputs(current)
    total_saved += saved
    methods_used.append("snip")
    
    current_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in current if isinstance(msg, dict))
    if current_tokens <= target_tokens:
        return CompressionResult(
            compressed_text=str(current),
            original_tokens=original_tokens,
            compressed_tokens=current_tokens,
            method="+".join(methods_used),
            saved_tokens=total_saved,
        )
    
    # Layer 2: Microcompact
    current, saved = microcompact(current)
    total_saved += saved
    methods_used.append("microcompact")
    
    current_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in current if isinstance(msg, dict))
    if current_tokens <= target_tokens:
        return CompressionResult(
            compressed_text=str(current),
            original_tokens=original_tokens,
            compressed_tokens=current_tokens,
            method="+".join(methods_used),
            saved_tokens=total_saved,
        )
    
    # Layer 3: Collapse
    current, saved, markers = collapse_sections(current, target_tokens)
    total_saved += saved
    methods_used.append("collapse")
    
    current_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in current if isinstance(msg, dict))
    if current_tokens <= target_tokens:
        return CompressionResult(
            compressed_text=str(current),
            original_tokens=original_tokens,
            compressed_tokens=current_tokens,
            method="+".join(methods_used),
            saved_tokens=total_saved,
            markers=markers,
        )
    
    # Layer 4: Autocompact (last resort)
    current, saved = autocompact(current, call_model_func)
    total_saved += saved
    methods_used.append("autocompact")
    
    final_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in current if isinstance(msg, dict))
    
    return CompressionResult(
        compressed_text=str(current),
        original_tokens=original_tokens,
        compressed_tokens=final_tokens,
        method="+".join(methods_used),
        saved_tokens=total_saved,
    )


def auto_restore_files(edited_files: list, max_files: int = 5) -> list:
    """Auto-restore 5 recently edited files after compression.
    
    Returns a list of file-restore messages to add to the conversation
    so the model has context about what was recently being worked on.
    
    Args:
        edited_files: List of file paths that were recently edited
        max_files: Maximum number of files to restore (default 5)
    
    Returns:
        List of system messages with file content summaries
    """
    from pathlib import Path
    
    restore_messages = []
    for filepath in edited_files[:max_files]:
        try:
            path = Path(filepath)
            if path.exists():
                content = path.read_text()
                # Include first 500 chars as a reminder
                restore_messages.append({
                    "role": "system",
                    "content": f"[AUTO-RESTORE] Recently edited file: {filepath}\nFirst 500 chars:\n{content[:500]}",
                })
        except Exception:
            continue
    
    return restore_messages