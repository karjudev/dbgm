import os
from pathlib import Path
from typing import List, Mapping, Set
from fastapi import FastAPI, status, HTTPException, Query
import spacy

from app.schema import (
    InstitutionType,
    MeasureType,
    Ordinance,
    OutcomeType,
    QueryResponse,
    Statistics,
)
from app.elastic.db import (
    connect_elasticsearch,
    insert_ordinance,
    remove_ordinance,
    retrieve_ordinance,
)
from app.elastic.queries import (
    count_ordinances_by_type_by_outcome,
    extract_significant_keywords,
    query_ordinances,
    stats_ordinances,
)
from app.keywords.model import (
    detect_pos_keywords,
    load_spacy_model,
    detect_juridic_references,
)
from app.keywords.dictionary import detect_juridic_keywords, load_juridic_dictionary


# Directory of the SpaCy InformedPA model
MODEL_DIR: Path = Path(os.getenv("SEARCH_INFORMEDPA_DIR"))
# Filename of the juridic keywords file
JURIDIC_KEYWORDS_FILENAME: Path = Path(os.getenv("SEARCH_JURIDIC_DICTIONARY"))


app = FastAPI()


# Custom SpaCy model
nlp: spacy.language.Language = load_spacy_model(MODEL_DIR)

# Set of juridic keywords
juridic_dictionary: Set[str] = load_juridic_dictionary(JURIDIC_KEYWORDS_FILENAME)


# Connection to Elasticsearch
client = connect_elasticsearch()


@app.put("/ordinances/{doc_id}", status_code=status.HTTP_201_CREATED)
def put_ordinance(doc_id: str, ordinance: Ordinance) -> None:
    """Puts an ordinance in the service.

    Args:
        doc_id (str): Document ID.
        ordinance (Ordinance): Annotated ordinance.

    Raises:
        HTTPException: If an ordinance with the same content already exists.
    """
    # Parses the document with SpaCy
    doc: spacy.language.Doc = nlp(ordinance.content)
    # Extracts the juridic references
    ner_keywords: List[str] = detect_juridic_references(doc)
    # Extracts the juridic keywords
    dict_keywords: List[str] = detect_juridic_keywords(
        juridic_dictionary, ordinance.content
    )
    # Extracts the POS keywords
    pos_keywords: List[str] = detect_pos_keywords(doc, nlp.vocab)
    # Transforms the list of measure objects into a list of JSON objects
    measures: List[Mapping] = [
        {"measure": entry.measure.value, "outcome": entry.outcome.value}
        for entry in ordinance.measures
    ]
    # Stores the document
    stored: bool = insert_ordinance(
        client=client,
        doc_id=doc_id,
        username=ordinance.username,
        filename=ordinance.filename,
        institution=ordinance.institution.value,
        court=ordinance.court,
        content=ordinance.content,
        measures=measures,
        dictionary_keywords=dict_keywords,
        ner_keywords=ner_keywords,
        pos_keywords=pos_keywords,
        timestamp=ordinance.timestamp,
    )
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ordinance with the same content already exists.",
        )


@app.get("/ordinances")
def get_ordinances_by_query(
    text: str | None = Query(None),
    institution: InstitutionType | None = Query(None),
    courts: List[str] | None = Query(None),
    measures: List[MeasureType] | None = Query(None),
    outcomes: List[OutcomeType] | None = Query(None),
) -> List[QueryResponse]:
    # Decodes optional measures and outcome
    institution = None if institution is None else institution.value
    measures = None if measures is None else [m.value for m in measures]
    outcomes = None if outcomes is None else [o.value for o in outcomes]
    # Performs the query
    response = query_ordinances(
        client,
        text=text,
        institution=institution,
        courts=courts,
        measures=measures,
        outcomes=outcomes,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to perform the query",
        )
    # Returns the response
    return response


@app.get("/ordinances/summary")
def get_ordinances_summary() -> (
    Mapping[str, Mapping[MeasureType, Mapping[OutcomeType, int]]]
):
    """Gets ordinance count.

    Returns:
        Mapping[str, Mapping[MeasureType, Mapping[OutcomeType, int]]]: For each institution and each court for each measure, for each outcome, its count.
    """
    response = count_ordinances_by_type_by_outcome(client)
    return response


@app.get("/ordinances/{doc_id}")
def get_ordinance(doc_id: str) -> Ordinance:
    """Gets an ordinance from the service.

    Args:
        doc_id (str): Document ID.

    Raises:
        HTTPException: If the ordinance with the given document ID have not been found.

    Returns:
        Ordinance: Ordinance stored in the service, if any.
    """
    ordinance = retrieve_ordinance(client, doc_id)
    if ordinance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordinance with document ID {doc_id} not found.",
        )
    return ordinance


@app.delete("/ordinances/{doc_id}")
def delete_ordinance(doc_id: str) -> None:
    """Removes an ordinance from the service.

    Args:
        doc_id (str): Document ID.

    Raises:
        HTTPException: If an ordinance with the same content already exists.
    """
    removed: bool = remove_ordinance(client, doc_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordinance with document ID {doc_id} not found.",
        )


@app.get("/stats")
def get_stats() -> Statistics:
    """Gets the statistics about documents in the service.

    Returns:
        Statistics: Statistics around the documents.
    """
    count, courts = stats_ordinances(client)
    return Statistics(count=count, courts=courts)


@app.get("/keywords/significant")
def get_significant_references() -> Mapping[str, Mapping[str, float]]:
    """Gets the most significant juridic keywords for each court.

    Returns:
        Mapping[str, Mapping[str, float]]: For each court, for each significant keywords, its frequency.
    """
    response = extract_significant_keywords(client)
    return response
