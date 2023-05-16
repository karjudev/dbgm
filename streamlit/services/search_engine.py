from datetime import datetime
from typing import Any, List, Dict, Mapping, Optional, Tuple

import requests
from requests import Response
import streamlit as st

from services.rest import get_json_response


@st.cache_data
def _get_search_engine_url():
    host: str = st.secrets["search_engine"]["host"]
    port: int = int(st.secrets["search_engine"]["port"])
    url: str = f"http://{host}:{port}"
    return url


def __redact_content(text: str, entities: List[Dict]) -> str:
    for span in sorted(entities, key=lambda span: span["start"], reverse=True):
        start, end, label = span["start"], span["end"], span["label"]
        text = text[:start] + label + text[end:]
    return text


def get_stats(base_url: str = None) -> Tuple[int, int]:
    """Downloads statistics about the documents in the service.

    Args:
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP fetching.

    Returns:
        Tuple[int, int, datetime, datetime]: Count of the documents and of the courts.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    url: str = base_url + "/stats"
    response: Response = requests.get(url)
    body = get_json_response(response)
    count, courts = body["count"], body["courts"]
    return count, courts


def send_ordinance(
    doc_id: str,
    username: str,
    filename: str,
    institution: str,
    court: str,
    content: str,
    entities: List[Dict],
    measures: List[Dict],
    base_url: str = None,
    timestamp: int | str = None,
) -> None:
    """Sends a new ordinance to the search engine.

    Args:
        doc_id (str): Document ID to use.
        username (str): Name of the user that posts the ordinance.
        filename (str): Name of the file to post.
        institution (str): Institution that delivered the ordinance.
        court (str): Court of the ordinance.
        content (str): Non-redacted content.
        entities (List[Dict]): Entities to redact in the content.
        measures (List[Dict]): List of measures and outcomes.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP response.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    # Redacts the content
    content: str = __redact_content(content, entities)
    # Gets the service URL
    url: str = base_url + "/ordinances/" + doc_id
    # Performs the API call
    body = {
        "filename": filename,
        "username": username,
        "institution": institution,
        "court": court,
        "content": content,
        "measures": measures,
    }
    if timestamp is not None:
        body["timestamp"] = timestamp
    response: Response = requests.put(
        url,
        json=body,
    )
    get_json_response(response)


def delete_ordinance(doc_id: str, base_url: str = None) -> None:
    """Deletes an ordinance from the search engine.

    Args:
        doc_id (str): Document ID.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP fetching.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/ordinances/" + doc_id
    # Performs the API call
    response: Response = requests.delete(url)
    get_json_response(response)


def get_count_ordinances(
    base_url: str = None,
) -> Mapping[str, Mapping[str, Mapping[str, int]]]:
    """Gets the count of ordinances per count and per t

    Args:
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP fetching.

    Returns:
        Mapping[str, Mapping[str, Mapping[str, int]]]: For each court, for each measure, for each outcome, its count.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/ordinances/by_type_by_outcome"
    # Performs the API call
    response: Response = requests.get(url)
    counts = get_json_response(response)
    return counts


def get_significant_keywords(
    base_url: str = None,
) -> Mapping[str, Mapping[str, float]]:
    """Gets the significant keywords for each court.

    Args:
        base_url (str, optional): _description_. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP fetching.

    Returns:
        Mapping[str, Mapping[str, float]]: For each court, for each keyword, its frequency.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/keywords/significant"
    # Performs the API call
    response: Response = requests.get(url)
    body = get_json_response(response)
    return body


def perform_query(
    text: Optional[str],
    courts: List[str],
    measures: List[str],
    outcome: Optional[str],
    base_url: str = None,
    date_format: str = "%Y-%m-%d",
) -> List[Mapping[str, Any]]:
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/ordinances"
    # Builds the query params
    params = {}
    if len(text) > 0:
        params["text"] = text
    if len(courts) > 0:
        params["courts"] = courts
    if len(measures) > 0:
        params["measures"] = measures
    if outcome != "Tutti":
        params["outcome"] = outcome
    # Performs the request
    response: Response = requests.get(url, params=params)
    hits = get_json_response(response)
    for hit in hits:
        hit["timestamp"] = datetime.fromisoformat(hit["timestamp"]).strftime("%d/%m/%Y")
    return hits
