from collections import Counter
import heapq
from pathlib import Path
import re
from typing import List, Set
from flashtext import KeywordProcessor


def load_juridic_dictionary(filename: Path) -> KeywordProcessor:
    """Loads the juridic dictionary from file.

    Args:
        filename (Path): Path of the file containing the scraped juridic keywords.

    Returns:
        KeywordProcessor: SProcessor able to extract keywords.
    """
    extractor = KeywordProcessor()
    extractor.add_keyword_from_file(filename)
    return extractor


def detect_juridic_keywords(
    extractor: KeywordProcessor, text: str, size: int = 10
) -> List[str]:
    """Detects a juridic keywords from a set.

    Args:
        extractor (KeywordProcessor): Keywords detector.
        text (str): Text to analyze.
        size (int, optional): Number of keywords to return. Defaults to 10.

    Returns:
        List[str]: List of juridic keywords.
    """
    # Set of all the distinct keywords
    keywords: Set[str] = set(extractor.extract_keywords(text))
    # Top-k Keyword-occurrences pairs
    top_keywords: List[str] = heapq.nlargest(
        size, keywords, key=lambda kw: text.lower().count(kw.lower())
    )
    return top_keywords
