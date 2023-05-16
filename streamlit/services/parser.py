import re
from typing import Dict, Any

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from tika import parser


def _normalize_text(text: str) -> str:
    """Normalizes common expressions in the text to a common form.

    :param text: Plain text.
    :return: Text with normalized expressions.
    """
    # Removes filenames etc.
    text = re.sub(
        r"^[\w,\s-]+\.[A-Za-z]{2,4}$", "", text, flags=re.MULTILINE | re.IGNORECASE
    )
    # Removes occurrences like "N°", "N. ordinanza", "N° 2022/124 SIUS"
    text = re.sub(
        r"n\s*([.°])?\s*\d+/\d+\s*s(ius|iep|\d+)",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    # Normalizes common terms
    text = re.sub(
        r"^\s*o\s*r\s*d\s*i\s*n\s*a\s*n\s*z\s*a\s*$",
        "ORDINANZA",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*d\s*i\s*s\s*p\s*o\s*n\s*e\s*$",
        "DISPONE",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*o\s*s\s*s\s*e\s*r\s*v\s*a\s*$",
        "OSSERVA",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*(p\.?\s*q\.?\s*m\.?)|(per\s*questi\s*motivi)\s*$",
        "PER QUESTI MOTIVI",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    return text


def _parse_text(text: str) -> str:
    """Parses the text.

    :param text: Plain text to parse.
    :return: Cleaned, normalized text.
    """
    # Normalizes the text
    text = _normalize_text(text)
    # Output text
    output_text: str = ""
    # List of sections of the documents
    for line in text.splitlines():
        # Cleans up redundant spaces
        line: str = " ".join(line.split())
        # Discards empty lines
        if len(line) == 0:
            continue
        output_text += line + "\n"
    return output_text


@st.cache_resource
def _get_tika_url() -> str:
    """Constructs the URL to connect to Apache Tika.

    :return: URL of Apache Tika.
    """
    host: str = st.secrets["tika"]["host"]
    port: int = int(st.secrets["tika"]["port"])
    return f"http://{host}:{port}"


@st.cache_data
def parse_document(uploaded_file: UploadedFile) -> str:
    """Parses an uploaded document by means of Apache Tika.

    :param uploaded_file: File uploaded by the user.
    :return: Plain text of the file
    """
    # URL to Tika
    tika_url: str = _get_tika_url()
    # Reads the data from the user
    data: bytes = uploaded_file.getvalue()
    # Parses the content with Apache Tika
    parsed: Dict[str, Any] = parser.from_buffer(data, tika_url)
    # Returns the content
    text: str = parsed["content"]
    # Performs a preliminary heuristic normalization
    text = _parse_text(text)
    # Returns the normalized document
    return text
