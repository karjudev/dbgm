from typing import List, Dict, Mapping, Optional

import streamlit as st
from requests import Response
import requests

from services.rest import get_json_response


@st.cache_resource
def _get_anonymizer_url() -> str:
    """Gets the URL of the anonymization microservice."""
    host: str = st.secrets["anonymizer"]["host"]
    port: int = int(st.secrets["anonymizer"]["port"])
    url: str = f"http://{host}:{port}"
    return url


@st.cache_resource
def predict_annotations(text: str, base_url: str = None) -> List[Dict]:
    """Predicts the annotations with a machine learning annotator.

    Args:
        text (str): Text to annotate.
        base_url (str, optional): Base URL fo the remote service. Defaults to None.

    Raises:
        ValueError: If the annotation went bad.

    Returns:
        List[Dict]: List of possible annotations
    """
    # Performs the API call
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/predictions"
    response: Response = requests.post(url, json={"content": text})
    # Parses the body to extract annotations
    annotations: List[Dict] = get_json_response(response)
    return annotations


def correct_annotations(
    username: str,
    filename: str,
    text: str,
    predicted: List[Dict],
    ground_truth: List[Dict],
    timestamp: int | str = None,
    base_url: str = None,
) -> str:
    """Sends to the server the correct annotations.

    Args:
        username (str): User that sends the annotations.
        filename (str): Name of the file.
        text (str): Text content of the file.
        predicted (List[Dict]): Annotations previously predicted.
        ground_truth (List[Dict]): True annotations given by the human.
        timestamp (int | str): Timestamp of the ordinance. Defaults to None.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If the annotation went bad.

    Returns:
        str: Document ID.
    """
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/documents"
    body: Dict = {
        "username": username,
        "filename": filename,
        "content": text,
        "predicted": predicted,
        "ground_truth": ground_truth,
    }
    if timestamp is not None:
        body["timestamp"] = timestamp
    response: Response = requests.post(url, json=body)
    doc_id: str = get_json_response(response)
    return doc_id


def edit_annotations(
    doc_id: str,
    username: str,
    filename: str,
    text: str,
    predicted: List[Dict],
    ground_truth: List[Dict],
    base_url: str = None,
) -> None:
    """Edits the annotations for a document that already exists.

    Args:
        doc_id (str): Document ID.
        username (str): User that sends the annotations.
        filename (str): Name of the file.
        text (str): Text content of the file.
        predicted (List[Dict]): Annotations previously predicted.
        ground_truth (List[Dict]): True annotations given by the human.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the editing.
    """
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/documents/" + doc_id
    body: Dict = {
        "username": username,
        "filename": filename,
        "text": text,
        "predicted": predicted,
        "ground_truth": ground_truth,
    }
    response: Response = requests.put(url, json=body)
    get_json_response(response)


def get_annotated_document(
    doc_id: str, base_url: str = None
) -> Mapping[str, str | List[Mapping]]:
    """Gets an annotated document from the server.

    Args:
        doc_id (str): Document ID.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If the document did not exist.

    Returns:
        Mapping[str, str | List[Mapping]]: Annotated document from the server.
    """
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/documents/" + doc_id
    response: Response = requests.get(url)
    document = get_json_response(response)
    return document


def list_documents_user(username: str, base_url: str = None) -> List[Mapping]:
    """Lists all the documents posted by the user.

    Args:
        username (str): User to list.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP API.

    Returns:
        List[Mapping]: List of entries in the form `{"doc_id": ..., "filename": ...}`
    """
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/documents"
    response: Response = requests.get(url, params={"username": username})
    entries: List[Dict] = get_json_response(response)
    return entries


def delete_document(doc_id: str, base_url: str = None) -> None:
    """Deletes a document from the server.

    Args:
        doc_id (str): Document ID.
        base_url (str, optional): Base URL of the service. Defaults to None.
    """
    if base_url is None:
        base_url = _get_anonymizer_url()
    url: str = base_url + "/documents/" + doc_id
    response: Response = requests.delete(url)
    get_json_response(response)
