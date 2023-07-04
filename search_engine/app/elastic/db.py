from datetime import date
import os
from time import time
from typing import Any, List, Mapping, Optional
from elasticsearch import Elasticsearch, ConflictError
from elasticsearch.exceptions import NotFoundError

ES_HOST = os.getenv("SEARCH_ES_HOST")
ES_PORT = int(os.getenv("SEARCH_ES_PORT"))
ES_INDEX_ORDINANCES = os.getenv("SEARCH_ES_INDEX_ORDINANCES")


ES_MAPPING = {
    "properties": {
        "timestamp": {"type": "date"},
        "username": {"type": "keyword"},
        "filename": {"type": "keyword"},
        "institution": {"type": "keyword"},
        "court": {"type": "keyword"},
        "content": {"type": "text", "analyzer": "italian"},
        "measures": {
            "type": "nested",
            "properties": {
                "measure": {"type": "keyword"},
                "outcome": {"type": "boolean"},
            },
        },
        "dictionary_keywords": {"type": "keyword"},
        "ner_keywords": {"type": "keyword"},
        "textrank_keywords": {"type": "keyword"},
        "publication_date": {
            "type": "date",
            "format": "yyyy-MM-dd",
            "null_value": "1900-01-01",
        },
    }
}


def connect_elasticsearch(
    host: str = ES_HOST,
    port: int = ES_PORT,
    index: str = ES_INDEX_ORDINANCES,
    mapping: Mapping[str, Any] = ES_MAPPING,
) -> Elasticsearch:
    """Connects to an Elasticsearch server.

    Args:
        host (str, optional): Host where to connect. Defaults to ES_HOST.
        port (int, optional): Port on the host. Defaults to ES_PORT.
        index (str, optional): Index name to create if it does not exist. Defaults to ES_INDEX.
        mapping (Mapping[str, Any], optional): Mapping of the index. Defaults to ES_MAPPING.

    Returns:
        Elasticsearch: Connection to Elasticsearch
    """
    # Connects to the ES server
    client = Elasticsearch(f"http://{host}:{port}", sniff_on_start=True)
    # If the index does not exist, creates it
    if not client.indices.exists(index=index):
        client.indices.create(index=index, body={"mappings": mapping})
    return client


def insert_ordinance(
    client: Elasticsearch,
    doc_id: str,
    username: str,
    filename: str,
    institution: str,
    court: str,
    content: str,
    measures: List[Mapping],
    dictionary_keywords: List[str],
    ner_keywords: List[str],
    textrank_keywords: List[str],
    publication_date: date,
    timestamp: float = None,
    index: str = ES_INDEX_ORDINANCES,
) -> bool:
    """Puts a document in Elasticsearch if absent.
    Args:
        client (Elasticsearch): Elasticsearch client.
        doc_id (str): Document ID.
        username (str): Username of the user.
        filename (str): Name of the file.
        institution (str): Institution that delivered the ordinance.
        court (str): Court of the ordinance.
        content (str): Content of the ordinance (anonymized).
        measures (List[Mapping]): Measures of the ordinance with outcome.
        dictionary_keywords (List[str]): Keywords coming from the juridic dictionary.
        ner_keywords (List[str]): Keywords from the NER model.
        textrank_keywords (List[str]): Keywords from the TextRank algorithm.
        publication_date (date): Date of the publication.
        timestamp (float, optional): Timestamp to use. Defaults to None.
        index (str, optional): Elasticsearch index. Defaults to ES_INDEX_ORDINANCES.
    Returns:
        bool: If the element have been inserted.
    """
    # Computes the timestamp
    if timestamp is None:
        timestamp = int(time())
    # Inserts the element in the index
    body = {
        "timestamp": timestamp,
        "filename": filename,
        "username": username,
        "institution": institution,
        "court": court,
        "content": content,
        "measures": measures,
        "dictionary_keywords": dictionary_keywords,
        "ner_keywords": ner_keywords,
        "textrank_keywords": textrank_keywords,
        "publication_date": publication_date.strftime("%Y-%m-%d"),
    }
    try:
        client.create(index=index, id=doc_id, body=body, refresh=True)
        return True
    except ConflictError:
        return False


def retrieve_ordinance(
    client: Elasticsearch, doc_id: str, index: str = ES_INDEX_ORDINANCES
) -> Optional[Mapping[str, Any]]:
    """Retrieves a specific document on Elasticsearch.
    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        doc_id (str): Document ID.
        index (str, optional): Index on Elasticsearch. Defaults to ES_INDEX.
    Returns:
        Optional[Mapping[str, Any]]: The document, if it is found, else None.
    """
    try:
        result = client.get(index=index, id=doc_id)
        return result["_source"]
    except NotFoundError:
        return None


def remove_ordinance(
    client: Elasticsearch, doc_id: str, index: str = ES_INDEX_ORDINANCES
) -> bool:
    """Deletes a document on the Elasticsearch index.
    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        doc_id (str): Document ID.
        index (str, optional): Index on Elasticsearch. Defaults to ES_INDEX.
    Returns:
        bool: If the deletion actually deleted the document.
    """
    try:
        client.delete(index=index, id=doc_id, refresh=True)
        return True
    except NotFoundError:
        return False
