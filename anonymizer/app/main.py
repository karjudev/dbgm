import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, status
from app.elastic.db import (
    connect_elasticsearch,
    insert_document,
    retrieve_document,
    remove_document,
)
from app.model.architecture import NERAnnotator

from app.schema import AnnotatedDocument, Span, Text


app = FastAPI()

# Path of the annotation model checkpoint on disk
MODEL_PATH = Path(os.getenv("ANONYMIZER_MODEL_DIR"))

# Annotation model
model = NERAnnotator.from_directory(MODEL_PATH)

# Connection to Elasticsearch
client = connect_elasticsearch()


@app.get("/hello")
def hello() -> str:
    """Returns an "HELLO" message.

    Returns:
        str: "HELLO"
    """
    return "HELLO"


@app.post("/predictions")
async def predict_annotations(text: Text) -> List[Span]:
    """Predicts the possible annotations with the machine learning model.

    Args:
        text (Text): JSON wrapper of a text document.

    Returns:
        List[Span]: List of possible "Prodigy-style", char-encoded spans.
    """
    # Predicts the annotations with the machine learning model
    spans = model.predict(text.content)
    return spans


@app.post("/documents", status_code=status.HTTP_201_CREATED)
def post_document(document: AnnotatedDocument) -> str:
    """Stores a new annotated document.

    Args:
        document (AnnotatedDocument): Document to Store.

    Raises:
        HTTPException: If the document already exists.

    Returns:
        str: Document ID.
    """
    # Tries to insert the document
    doc_id = insert_document(client, document)
    if doc_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document with this content already exists.",
        )
    return doc_id


@app.get("/documents/{doc_id}")
def get_document(doc_id: str) -> AnnotatedDocument:
    """Gets a document by ID.

    Args:
        doc_id (str): Document ID.

    Raises:
        HTTPException: If the document does not exist.

    Returns:
        AnnotatedDocument: Document retrieved from the database.
    """
    # Tries to retrieve the document
    document = retrieve_document(client, doc_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document ID {doc_id} not found.",
        )
    return document


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> None:
    """Deletes a document.

    Args:
        doc_id (str): Document ID.

    Raises:
        HTTPException: If the document is not found.
    """
    exists = remove_document(client, doc_id)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID {doc_id} not found.",
        )
