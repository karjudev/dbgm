from datetime import date, datetime
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


def get_count(base_url: str = None) -> int:
    """Downloads the number of documents in the service.

    Args:
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP fetching.

    Returns:
        int: Number of documents.
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    url: str = base_url + "/count"
    response: Response = requests.get(url)
    body = get_json_response(response)
    return body


def send_ordinance(
    doc_id: str,
    username: str,
    filename: str,
    institution: str,
    court: str,
    content: str,
    entities: List[Dict],
    measures: List[Dict],
    publication_date: datetime,
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
        "publication_date": publication_date.strftime("%Y-%m-%d"),
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


def list_ordinances_user(
    username: str, search_from: int = 0, base_url: str = None
) -> List[Mapping]:
    """Lists all the documents posted by the user.

    Args:
        username (str): User to list.
        search_from (int, optional): Search index to use as a starting point. Defaults to 0.
        base_url (str, optional): Base URL of the service. Defaults to None.

    Raises:
        ValueError: If there is an error in the HTTP API.

    Returns:
        List[Mapping]: List of entries in the form `{"doc_id": ..., "filename": ...}`
    """
    if base_url is None:
        base_url = _get_search_engine_url()
    url: str = base_url + "/ordinances/user"
    params = {"username": username, "search_from": search_from}
    response: Response = requests.get(url, params=params)
    entries: List[Dict] = get_json_response(response)
    for entry in entries:
        entry["content"] = entry["content"].replace("\n", "<br/>")
        if "publication_date" in entry and entry["publication_date"] is not None:
            entry["publication_date"] = datetime.strptime(
                entry["publication_date"], "%Y-%m-%d"
            ).date()
    return entries


def perform_query(
    text: Optional[str],
    institution: str,
    courts: List[str],
    measures: List[str],
    outcomes: List[str],
    start_date: date,
    end_date: date,
    base_url: str = None,
) -> List[Mapping[str, Any]]:
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/ordinances"
    # Builds the query params
    params = {
        "start_date": start_date.strftime("%Y-%d-%m"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    if len(text) > 0:
        params["text"] = text
    if len(institution) > 0:
        params["institution"] = institution
    if len(courts) > 0:
        params["courts"] = courts
    if len(measures) > 0:
        params["measures"] = measures
    params["outcomes"] = outcomes
    # Performs the request
    response: Response = requests.get(url, params=params)
    hits = get_json_response(response)
    # Parses timestamps
    for hit in hits:
        try:
            hit["timestamp"] = datetime.fromisoformat(hit["timestamp"]).strftime(
                "%d/%m/%Y"
            )
        except:
            try:
                hit["timestamp"] = datetime.fromtimestamp(
                    float(hit["timestamp"])
                ).strftime("%d/%m/%Y")
            except Exception as e:
                pass
    return hits


def edit_publication_date(
    doc_id: str, publication_date: date, base_url: str = None
) -> None:
    if base_url is None:
        base_url = _get_search_engine_url()
    # Gets the service URL
    url: str = base_url + "/dates/" + doc_id
    params = {"publication_date": publication_date.strftime("%Y-%m-%d")}
    response: Response = requests.put(url, params=params)
    get_json_response(response)
