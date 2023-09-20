from pathlib import Path
from typing import List, Set
import heapq
import spacy
import pytextrank


@spacy.language.Language.component("custom_sents_bounds")
def set_custom_boundaries(doc: spacy.language.Doc) -> spacy.language.Doc:
    for tok in doc[:-1]:
        if tok.text == "•":
            doc[tok.i].is_sent_start = True
        elif tok.text in [
            ",",
            ".",
        ]:
            doc[tok.i].is_sent_start = False
    return doc


def load_spacy_model(spacy_model: str = "it_core_news_sm") -> spacy.language.Language:
    """Creates a custom SpaCy model.

    Args:
        spacy_model (str, optional): Name of the base SpaCy model. Defaults to "it_core_news_sm".

    Returns:
        spacy.language.Language: SpaCy model.
    """
    # Loads the base NLP model
    nlp = spacy.load(spacy_model)
    # Adds the custom sentence boundary recognizer
    nlp.add_pipe("custom_sents_bounds", before="parser")
    # Adds the TextRank keyword extractor
    nlp.add_pipe("textrank")
    return nlp


def detect_textrank_keywords(
    doc: spacy.language.Doc, size: int = 10, filtered: Set[str] = None
) -> List[str]:
    """Detects keywords in the document with the TextRank algorithm.

    Args:
        doc (spacy.language.Doc): SpaCy document.
        size (int, optional): Number of keywords to return. Defaults to 10.
        filtered (Set[str], optional): Set of filtered keywords. Defaults to None.

    Returns:
        List[str]: List of top-k keywords found via TextRank.
    """
    if filtered is None:
        filtered = {"ORG", "PER", "LOC", "MISC", "TIME", "DOTT", "art.", "artt."}
    chunks = heapq.nlargest(
        size,
        (
            chunk
            for chunk in doc._.phrases
            if not any(f in chunk.text for f in filtered) and len(chunk.text) <= 20
        ),
        key=lambda chunk: chunk.rank,
    )
    return list(set(chunk.text.strip().lower() for chunk in chunks))
