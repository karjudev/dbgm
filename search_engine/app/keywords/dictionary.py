from collections import Counter
from pathlib import Path
import re
from typing import List, Set


def load_juridic_dictionary(filename: Path) -> Set[str]:
    """Loads the juridic dictionary from file.

    Args:
        filename (Path): Path of the file containing the scraped juridic keywords.

    Returns:
        Set[str]: Set of juridic keywords.
    """
    keywords: Set[re.Pattern] = set()
    with open(filename) as file:
        for line in file:
            keywords.add(line.strip())
    return keywords


def detect_juridic_keywords(
    keywords: Set[str], text: str, min_frequency: int = 1, top_k: int = 10
) -> List[str]:
    """Detects a juridic keywords from a set.

    Args:
        keywords (Set[str]): Set of keywords.
        text (str): Text to analyze.
        min_frequency (int, optional): Minimum frequency of a keyword to be taken into account. Defaults to 1.
        top_k (int, optional): Number of most common results to return. Defaults to 10.

    Returns:
        List[str]: List of juridic keywords.
    """
    vocabulary_matches = Counter()
    matched_keywords = []
    for keyword in keywords:
        # Matches for the keywords
        keyword_match: List[re.Match] = re.findall(
            r"\b" + re.escape(keyword) + r"\b", text, flags=re.I
        )
        if not keyword_match or len(keyword_match) <= min_frequency:
            continue
        # Ensure longest match
        if any([keyword in matched_kw for matched_kw in matched_keywords]):
            continue
        vocabulary_matches.update({keyword: len(keyword_match)})
        matched_keywords.append(keyword)
    # Extracts the top K keywords
    return [match[0].lower() for match in vocabulary_matches.most_common(top_k)]
