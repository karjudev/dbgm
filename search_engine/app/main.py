from datetime import date
import os
from pathlib import Path
from typing import List, Mapping, Set
from fastapi import FastAPI, status, HTTPException, Query
import spacy

from app.schema import (
    InstitutionType,
    JuridicDataResponse,
    MeasureType,
    Ordinance,
    OrdinanceEntry,
    QueryResponse,
)
from app.elastic.db import (
    connect_elasticsearch,
    insert_ordinance,
    remove_ordinance,
    retrieve_juridic_data,
    retrieve_ordinance,
)
from app.elastic.queries import (
    edit_publication_date,
    extract_keywords,
    retrieve_ordinances_user,
    query_ordinances,
    stats_ordinances,
)
from app.keywords.model import detect_textrank_keywords, load_spacy_model
from app.keywords.dictionary import detect_juridic_keywords, load_juridic_dictionary

# Filename of the juridic keywords file
JURIDIC_KEYWORDS_FILENAME: Path = Path(os.getenv("SEARCH_JURIDIC_DICTIONARY"))


app = FastAPI()


# Custom SpaCy model
nlp: spacy.language.Language = load_spacy_model()

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
    # Transforms the list of measure keywords_objects into a list of JSON objects
    measures: List[Mapping] = [
        {"measure": entry.measure.value, "outcome": entry.outcome}
        for entry in ordinance.measures
    ]
    # Parses the document with SpaCy
    doc: spacy.language.Doc = nlp(ordinance.content)
    # Extracts the dictionary keywords
    dict_keywords: List[str] = detect_juridic_keywords(
        juridic_dictionary, ordinance.content
    )
    # Extracts the TextRank keywords
    textrank_keywords: List[str] = detect_textrank_keywords(doc)
    # Extracts the juridic keywords
    keywords, entities = extract_keywords(client, ordinance.content, measures)

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
        textrank_keywords=textrank_keywords,
        juridic_keywords=keywords,
        juridic_entities=entities,
        publication_date=ordinance.publication_date,
        timestamp=ordinance.timestamp,
    )
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ordinance with the same content already exists.",
        )


@app.get("/juridic_data")
def get_juridic_data() -> JuridicDataResponse:
    keywords, concepts = retrieve_juridic_data(client)
    return {"keywords": keywords, "concepts": concepts}


@app.get("/ordinances")
def get_ordinances_by_query(
    start_date: date = Query(...),
    end_date: date = Query(...),
    text: str | None = Query(None),
    keywords: List[str] | None = Query(None),
    concepts: List[str] | None = Query(None),
    institution: InstitutionType | None = Query(None),
    courts: List[str] | None = Query(None),
    measures: List[MeasureType] | None = Query(None),
    outcome: bool | None = Query(None),
) -> QueryResponse:
    # Decodes optional measures and institutions
    institution = None if institution is None else institution.value
    measures = None if measures is None else [m.value for m in measures]
    # Performs the query
    response = query_ordinances(
        client,
        text=text,
        keywords=keywords,
        concepts=concepts,
        institution=institution,
        courts=courts,
        measures=measures,
        outcome=outcome,
        start_date=start_date,
        end_date=end_date,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to perform the query",
        )
    # Returns the response
    aggregations, hits, keywords, concepts, num_hits = response
    return {
        "aggregations": aggregations,
        "hits": hits,
        "keywords": keywords,
        "concepts": concepts,
        "num_hits": num_hits,
    }


@app.get("/ordinances/user")
def get_ordinances_user(
    username: str = Query(...), search_from: int = Query(0)
) -> List[OrdinanceEntry]:
    return retrieve_ordinances_user(client, username, search_from)


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


@app.get("/count")
def get_count() -> int:
    """Gets the number of documents in the service.

    Returns:
        Statistics: Statistics around the documents.
    """
    num_docs = stats_ordinances(client)
    return num_docs


@app.put("/dates/{doc_id}", status_code=status.HTTP_202_ACCEPTED)
def put_publication_date(doc_id: str, publication_date: date = Query(...)) -> None:
    updated = edit_publication_date(client, doc_id, publication_date)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordinance with document ID {doc_id} not found.",
        )
