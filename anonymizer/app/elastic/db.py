from hashlib import sha512
import os
from time import time
from typing import Any, List, Mapping, Optional
from elasticsearch import Elasticsearch, ConflictError, NotFoundError
from elasticsearch.helpers import scan

from app.schema import AnnotatedDocument

ES_HOST = os.getenv("ANONYMIZER_ES_HOST")
ES_PORT = int(os.getenv("ANONYMIZER_ES_PORT"))
ES_INDEX = os.getenv("ANONYMIZER_ES_INDEX")


spans_mapping = {
    "type": "nested",
    "properties": {
        "start": {"type": "unsigned_long"},
        "end": {"type": "unsigned_long"},
        "label": {"type": "keyword"},
    },
}

ES_MAPPING = {
    "properties": {
        "timestamp": {"type": "date"},
        "username": {"type": "keyword"},
        "filename": {"type": "keyword"},
        "content": {"type": "text", "analyzer": "italian"},
        "predicted": spans_mapping,
        "ground_truth": spans_mapping,
    }
}


def connect_elasticsearch(
    host: str = ES_HOST,
    port: int = ES_PORT,
    index: str = ES_INDEX,
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


def insert_document(
    client: Elasticsearch,
    document: AnnotatedDocument,
    index: str = ES_INDEX,
    encoding: str = "utf-8",
) -> Optional[str]:
    """Adds a document to the Elasticsearch index, only if it does not exist.
    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        document (AnnotatedDocument): Annotated document.
        index (str, optional): Index where to add `document`. Defaults to ES_INDEX.
        encoding (str, optional): Encoding to use when computing the hash. Defaults to "utf-8".
    Returns:
        Optional[str]: Document ID, or None if the insertion went bad.
    """
    # Computes the hash of the text content
    hash_value: str = sha512(document.content.encode(encoding)).hexdigest()
    # If needed, computes the timestamp
    if document.timestamp is None:
        document.timestamp = int(time())
    # Inserts the element in the index
    try:
        response = client.create(
            index=index, id=hash_value, body=document.dict(), refresh=True
        )
        return response["_id"]
    except ConflictError:
        return None


def retrieve_document(
    client: Elasticsearch, doc_id: str, index: str = ES_INDEX
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


def retrieve_documents_user(
    client: Elasticsearch, username: str, index: str = ES_INDEX
) -> List[Mapping[str, str]]:
    """Retrieves all the documents for a given user.
    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        username (str): Username.
        index (str, optional): Index on Elasticsearch. Defaults to ES_INDEX.
    Returns:
        List[Mapping[str, str]]: List of entries.
    """
    results = scan(
        client=client,
        index=index,
        query={
            "query": {"term": {"username": username}},
            "_source": ["filename"],
            "sort": {"timestamp": "desc"},
        },
        preserve_order=True,
    )
    documents = [
        {"doc_id": result["_id"], "filename": result["_source"]["filename"]}
        for result in results
    ]
    return documents


def remove_document(client: Elasticsearch, doc_id: str, index: str = ES_INDEX) -> bool:
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
