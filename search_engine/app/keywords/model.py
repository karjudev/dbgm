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


def load_spacy_model(
    informedpa_dir: Path, spacy_model: str = "it_core_news_sm"
) -> spacy.language.Language:
    """Creates a custom SpaCy model.

    Args:
        informedpa_dir (Path): Path of the InformedPA model, used to extract NER.
        spacy_model (str, optional): Name of the base SpaCy model. Defaults to "it_core_news_sm".

    Returns:
        spacy.language.Language: SpaCy model.
    """
    # Loads the base NLP model
    nlp = spacy.load(spacy_model)
    # Loads the InformedPA model
    informedpa_ner = spacy.load(informedpa_dir)
    # Uses the same embeddings for ner and the rest of the model
    informedpa_ner.replace_listeners("tok2vec", "ner", ["model.tok2vec"])
    # Uses the NER pipeline of InformedPA into the base model
    nlp.add_pipe("ner", source=informedpa_ner, name="ipa_ner", before="ner")
    # Adds the custom sentence boundary recognizer
    nlp.add_pipe("custom_sents_bounds", before="parser")
    # Adds the TextRank keyword extractor
    nlp.add_pipe("textrank")
    return nlp


def detect_juridic_references(
    doc: spacy.language.Doc, labels: Set[str] = None
) -> List[str]:
    """Extracts the juridic references from the text.

    Args:
        doc (spacy.language.Doc): Document parsed by SpaCy.
        labels (Set[str], optional): Labels to capture. Defaults to None.

    Returns:
        List[str]: List of juridic keywords.
    """
    if labels is None:
        labels = {"LAW", "ACT"}
    references = []
    for entity in doc.ents:
        if entity.label_ in labels:
            references.append(entity.text)
    return references


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
