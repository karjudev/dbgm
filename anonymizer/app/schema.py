from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class SpanLabel(Enum):
    """Possible type of span label."""

    TIME = "TIME"
    PER = "PER"
    LOC = "LOC"
    MISC = "MISC"


class Span(BaseModel):
    """Annotated span of text in "Prodigy-like" format."""

    start: int
    end: int
    label: str


class Text(BaseModel):
    """JSON wrapper of a text to be predicted."""

    content: str


class AnnotatedDocument(BaseModel):
    """Annotated document to be use as a training example."""

    username: str
    filename: str
    content: str
    predicted: List[Span]
    ground_truth: List[Span]
    timestamp: Optional[int | str]
