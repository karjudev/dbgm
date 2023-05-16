from pickle import TUPLE2
from typing import List, Mapping, Optional, Tuple

import torch
from transformers import PreTrainedTokenizer

from app.schema import Span


# Encoding used to convert list of labels to integer and viceversa
LABEL2ID: Mapping[str, int] = {
    "O": 0,
    "B-LOC": 1,
    "I-LOC": 2,
    "B-MISC": 3,
    "I-MISC": 4,
    "B-ORG": 5,
    "I-ORG": 6,
    "B-PER": 7,
    "I-PER": 8,
    "B-TIME": 9,
    "I-TIME": 10,
}
ID2LABEL: Mapping[int, str] = {idx: label for label, idx in LABEL2ID.items()}


def spans_to_labels(
    spans: List[Span], offsets: List[Tuple[int, int]] | torch.Tensor
) -> torch.Tensor:
    """Converts "Prodigy-like" spans to a tensor of encoded integer labels.

    Args:
        spans (List[Span]): List of Prodigy spans.
        offsets (List[Tuple[int, int]] | torch.Tensor): Offset mapping.
        For each token in the document, its (start, end) character offsets.

    Returns:
        torch.Tensor: Tensor of encoded labels for each character.
    """
    label_ids = [LABEL2ID["O"]] * len(offsets)
    for span in spans:
        i = 1
        while i < len(offsets) - 1 and offsets[i][0] < span.start:
            i += 1
        # If we reached the last offset we have to continue with the next span
        if i == len(offsets) - 1:
            continue
        # The target label is reported only in multiclass setting
        label = span.label
        # Assigns the "B"-label
        label_ids[i] = LABEL2ID[f"B-{label}"]
        i += 1
        # Assigns the "I"-labels
        while i < len(offsets) - 1 and offsets[i][1] <= span.end:
            label_ids[i] = LABEL2ID[f"I-{label}"]
            i += 1
    return torch.tensor(label_ids)


def labels_to_spans(
    labels: List[int] | torch.Tensor, offsets: List[Tuple[int, int]] | torch.Tensor
) -> List[Span]:
    """Converts an encoded list of integer labels into a list of "Prodigy-like" spans.

    Args:
        labels (List[int] | torch.Tensor): List or tensor with integer labels.
        offsets (List[Tuple[int, int]] | torch.Tensor): Offset mapping.
        For each token in the document, its (start, end) character offsets.

    Returns:
        List[Span]: List of Prodigy spans.
    """
    spans = []
    # Use features of the `List` type.
    if isinstance(labels, torch.Tensor):
        labels = labels.tolist()
    # Removes `[CLS]` and `[SEP]` tokens
    labels = labels[1:-1]
    offsets = offsets[1:-1]
    # Running index over the elements of `labels`
    i = 0
    while i < len(labels):
        # Searches for the start index
        while i < len(labels) and labels[i] == LABEL2ID["O"]:
            i += 1
        # If we reached the end of the list we are over
        if i == len(labels):
            break
        start = int(offsets[i][0])
        label = ID2LABEL[labels[i]][2:]
        # Searches for the end index
        try:
            i = labels.index(LABEL2ID["O"], i)
        except ValueError:
            i = len(labels)
        end = int(offsets[i - 1][1])
        # Creates a new span
        span = Span(start=start, end=end, label=label)
        spans.append(span)
    return spans


def encode_text(
    text: str, tokenizer: PreTrainedTokenizer, max_length: int = 512
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Encodes text for BERT prediction and training.

    Args:
        text (str): String to encode.
        tokenizer (PreTrainedTokenizer): Tokenizer to use.
        max_length (int, optional): Maximum length of an example. Defaults to 512.

    Returns:
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: Input IDs, attention mask and offset mapping.
    """
    output = tokenizer(
        text,
        padding=True,
        max_length=max_length,
        truncation=True,
        return_attention_mask=True,
        return_offsets_mapping=True,
        return_overflowing_tokens=True,
        return_special_tokens_mask=False,
        return_token_type_ids=False,
        return_length=False,
        return_tensors="pt",
    )
    return output["input_ids"], output["attention_mask"], output["offset_mapping"]
