from typing import List, Dict, Union, Tuple

from streamlit_text_label import Selection


def json_to_selections(entities: List[Dict], text: str) -> List[Selection]:
    """Converts JSON to Selection objects.

    Args:
        entities (List[Dict]): List of JSONs.
        text (str): Reference text.

    Returns:
        List[Selection]: List of selections.
    """
    selections: List[Selection] = []
    for entity in entities:
        start: int = entity["start"]
        end: int = entity["end"]
        entity_text: str = text[start:end]
        labels: List[str] = [entity["label"]]
        selection = Selection(start, end, entity_text, labels)
        selections.append(selection)
    return selections


def selections_to_json(text: str, selections: List[Selection]) -> List[Dict]:
    """Converts Selection objects to dictionaries.

    Args:
        text (str): Starting text, used for stripping.
        selections (List[Selection]): List of selections.

    Returns:
        List[Dict]: List of JSONs.
    """
    entries: List[Dict] = []
    for selection in selections:
        start, end, label = selection.start, selection.end, selection.labels[0]
        while text[start].isspace() and start <= len(text):
            start += 1
        while text[end - 1].isspace() and end > 0:
            end -= 1
        entry: Dict = {"start": start, "end": end, "label": label}
        entries.append(entry)
    return entries


def selections_to_annotated_text(
    text: str, selections: List[Selection], redact: bool = False
) -> List[Union[str, Tuple[str]]]:
    """Creates an annotated list of tokens.

    Args:
        text (str): Starting text.
        selections (List[Selection]): List of selections.
        redact (bool, optional): Wether to redact the text inside the selections. Defaults to False.

    Returns:
        List[Union[str, Tuple[str]]]: List of tokens of annotated text.
    """
    # Sorts the list of selections by start from finish to start
    selections.sort(key=lambda x: x.start)
    # Number of selections to consider
    n: int = len(selections)
    # List of tokens to return (initialized with the content before the first annotation)
    tokens: List[Union[str, Tuple[str, str]]] = [text[: selections[0].start]]
    # Substitutes the selected text with the tuple and adds the content until the next annotation
    for i in range(n - 1):
        content: str = selections[i].labels[0] if redact else selections[i].text
        tokens.append((content, selections[i].labels[0]))
        tokens.append(text[selections[i].end : selections[i + 1].start])
    # Finally, adds the content from the last annotation to the end
    content = selections[n - 1].labels[0] if redact else selections[n - 1].text
    tokens.append((content, selections[n - 1].labels[0]))
    tokens.append(text[selections[n - 1].end :])
    return tokens
