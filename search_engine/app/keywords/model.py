from collections import Counter
from pathlib import Path
from typing import List, Mapping, Set
import spacy


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


def detect_pos_keywords(
    doc: spacy.language.Doc,
    vocab: spacy.vocab.Vocab,
    include_juridic_patterns: bool = True,
    multikeywords_to_remove: List[str] = None,
    tokens_to_avoid: List[str] = None,
    min_frequency: int = 2,
    top_k: int = 10,
) -> List[str]:
    """Extract the most common multi keywords tagged with relevant POS tags patterns from a SpaCy doc,
        in a longest-match fashion.
        Currently, the relevant POS tags patterns (taken from the IR course slides) are:
        - ADJ, NOUN
        - NOUN, NOUN
        - ADJ, ADJ, NOUN
        - ADJ, NOUN, NOUN
        - NOUN, NOUN, NOUN
        - NOUN, ADJ, NOUN
        - NOUN, ADP, NOUN
        Additionally, the following patterns have been extracted from the most common ones present in the
        external juridic dictionary (Brocardi + Edizione Simone):
        - NOUN, ADP, NOUN, ADJ
        - NOUN, ADJ
        - NOUN, ADJ, ADJ
        - NOUN, ADJ, ADP, NOUN

    Args:
        doc (spacy.language.Doc): Document parsed with SpaCy.
        vocab (spacy.vocab.Vocab): SpaCy vocabulary, used to access the lexemes.
        include_juridic_patterns (bool, optional): Wether to include the patterns extracted from juridic dictionary. Defaults to True.
        multikeywords_to_remove (List[str], optional): List of multi-token keywords to remove, because they are usually too common. Defaults to None.
        tokens_to_avoid (List[str], optional): List of tokens to avoid. Defaults to None.
        min_frequency (int, optional): Minimum number of matches. Defaults to 2.
        top_k (int, optional): Number of results to return. Defaults to 10.

    Returns:
        List[str]: Most common keywords extracted with this metodology.
    """
    # Sets the global variables
    if multikeywords_to_remove is None:
        multikeywords_to_remove = ["ex art.", "ex artt."]
    if tokens_to_avoid is None:
        tokens_to_avoid = ["n."]
    # Creates POS patterns
    pos_tags_patterns = [
        [
            {"POS": "ADJ"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "NOUN"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "ADJ"},
            {"POS": "ADJ"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "ADJ"},
            {"POS": "NOUN"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "NOUN"},
            {"POS": "ADJ"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "NOUN"},
            {"POS": "NOUN"},
            {"POS": "NOUN"},
        ],
        [
            {"POS": "NOUN"},
            {"POS": "ADP"},
            {"POS": "NOUN"},
        ],
    ]
    if include_juridic_patterns:
        additional_patterns = [
            ("NOUN", "ADJ"),
            ("NOUN", "ADJ", "ADJ"),
            ("NOUN", "ADJ", "ADP", "NOUN"),
            ("NOUN", "ADP", "NOUN", "ADJ"),
        ]
        additional_patterns = [
            [{"POS": token} for token in pattern] for pattern in additional_patterns
        ]
        pos_tags_patterns.extend(additional_patterns)
    # Creates a matcher for POS patterns
    matcher = spacy.matcher.Matcher(vocab)
    matcher.add("pos_patterns", pos_tags_patterns)
    # Detects POS pattern matches
    matches = matcher(doc)
    multi_pos_counter = Counter()
    for _, start, end in matches:
        multi_pos_counter.update({doc[start:end].text: 1})
    filtered_pos_multi_keywords = []
    for text_entry, freq in multi_pos_counter.most_common(2 * top_k):
        if freq < min_frequency:
            continue
        if text_entry in multikeywords_to_remove or any(
            [token in text_entry for token in tokens_to_avoid]
        ):
            continue
        # Ensure longest match
        if any(
            [text_entry in matched_kw for matched_kw in filtered_pos_multi_keywords]
        ):
            continue
        filtered_pos_multi_keywords.append(text_entry)
    return filtered_pos_multi_keywords[:top_k]
