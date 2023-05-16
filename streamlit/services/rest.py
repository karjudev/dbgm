from typing import Any
from requests import Response, HTTPError


def get_json_response(response: Response) -> Any:
    body = response.json()
    try:
        response.raise_for_status()
    except HTTPError:
        raise ValueError(body["detail"])
    return body
