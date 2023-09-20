from datetime import date
import os
from time import time
from typing import Any, Iterable, List, Mapping, Optional, Tuple
from elasticsearch import Elasticsearch, ConflictError
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk

ES_HOST = os.getenv("SEARCH_ES_HOST")
ES_PORT = int(os.getenv("SEARCH_ES_PORT"))
ES_INDEX_ORDINANCES = os.getenv("SEARCH_ES_INDEX_ORDINANCES")
ES_INDEX_KEYWORDS = os.getenv("SEARCH_ES_INDEX_KEYWORDS")


ES_MAPPING_ORDINANCES = {
    "properties": {
        "timestamp": {"type": "date", "format": "yyyy-MM-dd"},
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
        "publication_date": {
            "type": "date",
            "format": "yyyy-MM-dd",
            "null_value": "1900-01-01",
        },
        "dictionary_keywords": {"type": "keyword"},
        "textrank_keywords": {"type": "keyword"},
        "juridic_keywords": {"type": "keyword"},
        "juridic_concepts": {"type": "keyword"},
    }
}

ES_MAPPING_KEYWORDS = {
    "properties": {
        "content": {"type": "text", "analyzer": "italian"},
        "measures": {
            "type": "nested",
            "properties": {
                "measure": {"type": "keyword"},
                "outcome": {"type": "boolean"},
            },
        },
        "query": {"type": "percolator"},
    }
}


def connect_elasticsearch(
    host: str = ES_HOST,
    port: int = ES_PORT,
    index: str = ES_INDEX_ORDINANCES,
    mapping: Mapping[str, Any] = ES_MAPPING_ORDINANCES,
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
    textrank_keywords: List[str],
    juridic_keywords: List[str],
    juridic_entities: List[str],
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
        dictionary_keywords (List[str]): Keywords coming from the dictionary.
        textrank_keywords (List[str]): Keywords from the TextRank algorithm.
        juridic_keywords (List[str]): Keywords from the juridic search.
        juridic_entities (List[str]): Entities associated to the juridic keywords.
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
        "textrank_keywords": textrank_keywords,
        "juridic_keywords": juridic_keywords,
        "juridic_concepts": juridic_entities,
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


def is_index_populated(client: Elasticsearch, index: str) -> bool:
    """Checks if an index is populated.

    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        index (str): Index to use.

    Returns:
        bool: If the Elasticsearch index is populated.
    """
    response = client.count(index=index)
    return response["count"] > 0


def bulk_upload(
    client: Elasticsearch, records: Iterable[Mapping[str, str]], index: str
) -> None:
    """Performs a bulk upload on an Elasticsearch server.

    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        records (Iterable[Mapping[str, str]]): Records to store.
        index (str): Index to use.
        type (str): Type of records. Defaults to "_doc".
    """
    bulk(
        client,
        ({"_index": index, "_type": "_doc", "_source": record} for record in records),
    )


def retrieve_juridic_data(
    client: Elasticsearch,
    index: str = ES_INDEX_ORDINANCES,
    max_count: int = 1_000_000_000,
) -> Tuple[List[str], List[str]]:
    """Retrieves all the juridic keywords and concepts.

    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        index (str, optional): Index to use. Defaults to ES_INDEX_ORDINANCES.
        max_count (int, optional): Maximum cardinality of keywords and/or concepts. Defaults to 1_000_000_000.

    Returns:
        Tuple[List[str], List[str]]: List of keywords and list of concepts.
    """
    body = {
        "size": 0,
        "aggs": {
            "keywords": {
                "terms": {"field": "juridic_keywords", "size": max_count},
            },
            "concepts": {"terms": {"field": "juridic_concepts", "size": max_count}},
        },
    }
    response = client.search(body=body, index=index)
    keywords = [
        bucket["key"] for bucket in response["aggregations"]["keywords"]["buckets"]
    ]
    concepts = [
        bucket["key"] for bucket in response["aggregations"]["concepts"]["buckets"]
    ]
    return keywords, concepts
