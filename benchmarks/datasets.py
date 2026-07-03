"""
Timuclaude Benchmark Dataset Loaders
Loads datasets from HuggingFace, local JSON, or custom formats.

Supported:
- HLE (Humanity's Last Exam) — from HuggingFace (needs HF_TOKEN)
- MRCR v2 — from HuggingFace (needs HF_TOKEN)
- Custom JSON — local files in [{question, answer, ...}] format
"""
import json
import os
from typing import Iterator, Optional, Callable, Awaitable


# Standard question format used across all benchmarks
# {"id": str, "question": str, "answer": str, "category": str, "image": Optional[str]}


def load_custom_json(file_path: str) -> list:
    """Load a custom JSON dataset.
    
    Expected format: [{"id": "1", "question": "...", "answer": "...", "category": "..."}]
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Normalize: ensure all required fields exist
    normalized = []
    for i, item in enumerate(data):
        normalized.append({
            "id": item.get("id", str(i + 1)),
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "category": item.get("category", "unknown"),
            "image": item.get("image", None),
        })
    
    return normalized


def load_hle(sample_size: Optional[int] = None, text_only: bool = False) -> list:
    """Load HLE dataset from HuggingFace.
    
    Requires HF_TOKEN environment variable.
    HLE is a gated dataset — user must register at huggingface.co.
    
    Args:
        sample_size: Limit to N questions (None = all 2500)
        text_only: Filter to text-only questions (exclude 14% multimodal)
    
    Returns:
        List of {id, question, answer, category, image}
    """
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        raise ValueError(
            "HLE is a gated dataset. Set HF_TOKEN environment variable. "
            "Register at huggingface.co/datasets/cais/hle to get access."
        )
    
    from datasets import load_dataset as hf_load_dataset
    
    ds = hf_load_dataset("cais/hle", split="test", token=token)
    
    results = []
    for item in ds:
        has_image = bool(item.get("image"))
        
        if text_only and has_image:
            continue
        
        results.append({
            "id": item.get("id", str(len(results) + 1)),
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "category": item.get("category", "unknown"),
            "image": item.get("image", None) if has_image else None,
        })
        
        if sample_size and len(results) >= sample_size:
            break
    
    return results


def load_mrcr(sample_size: Optional[int] = None) -> list:
    """Load MRCR v2 dataset from HuggingFace.
    
    Returns:
        List of {id, question (the full conversation prompt), answer, category}
    """
    from datasets import load_dataset as hf_load_dataset
    
    ds = hf_load_dataset("openai/mrcr", split="train", streaming=True)
    
    results = []
    for item in ds:
        results.append({
            "id": str(item.get("desired_msg_index", len(results) + 1)),
            "question": item.get("prompt", ""),
            "answer": item.get("answer", ""),
            "category": "long_context",
            "image": None,
            "n_needles": item.get("n_needles", 0),
        })
        
        if sample_size and len(results) >= sample_size:
            break
    
    return results


def load_dataset_by_name(name: str, sample_size: Optional[int] = None, text_only: bool = False) -> list:
    """Load a dataset by name.
    
    Args:
        name: 'hle', 'mrcr', or path to a JSON file
        sample_size: Limit to N questions
        text_only: For HLE, filter to text-only
    
    Returns:
        List of question dicts
    """
    if name == "hle":
        return load_hle(sample_size=sample_size, text_only=text_only)
    elif name == "mrcr":
        return load_mrcr(sample_size=sample_size)
    elif os.path.isfile(name):
        return load_custom_json(name)[:sample_size] if sample_size else load_custom_json(name)
    else:
        raise ValueError(f"Unknown dataset: {name}. Use 'hle', 'mrcr', or path to JSON file.")


def create_sample_dataset() -> list:
    """Create a small sample dataset for testing.
    
    These are simple questions with known answers, suitable for
    testing the benchmark framework without needing HF access.
    """
    return [
        {"id": "1", "question": "What is 15 * 12?", "answer": "180", "category": "math"},
        {"id": "2", "question": "What is the capital of France?", "answer": "Paris", "category": "knowledge"},
        {"id": "3", "question": "What is the derivative of x^2?", "answer": "2x", "category": "math"},
        {"id": "4", "question": "Who wrote the play Hamlet?", "answer": "William Shakespeare", "category": "knowledge"},
        {"id": "5", "question": "What is the chemical formula for water?", "answer": "H2O", "category": "science"},
        {"id": "6", "question": "What is 25 * 4?", "answer": "100", "category": "math"},
        {"id": "7", "question": "What is the largest planet in our solar system?", "answer": "Jupiter", "category": "knowledge"},
        {"id": "8", "question": "What is the square root of 144?", "answer": "12", "category": "math"},
        {"id": "9", "question": "In what year did World War II end?", "answer": "1945", "category": "history"},
        {"id": "10", "question": "What is the speed of light in km/s (approximately)?", "answer": "300000", "category": "physics"},
    ]