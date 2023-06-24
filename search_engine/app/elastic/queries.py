from datetime import date
from typing import List, Mapping, Optional, Tuple
from elasticsearch import Elasticsearch
from app.elastic.db import ES_INDEX_ORDINANCES


def retrieve_ordinances_user(
    client: Elasticsearch,
    username: str,
    search_from: int,
    index: str = ES_INDEX_ORDINANCES,
) -> List[Mapping]:
    body = {
        "query": {"term": {"username": username}},
        "sort": {"timestamp": "desc"},
        "from": search_from,
    }
    results = client.search(body=body, index=index)
    return [
        {"doc_id": result["_id"], **result["_source"]}
        for result in results["hits"]["hits"]
    ]


def stats_ordinances(client: Elasticsearch, index: str = ES_INDEX_ORDINANCES) -> int:
    """Statistics about the documents.

    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        index (str, optional): Index name. Defaults to ES_INDEX_ORDINANCES.

    Returns:
        int: Number of documents.
    """
    # Simple count of distinct documents
    return client.count(index=index)["count"]


def query_ordinances(
    client: Elasticsearch,
    start_date: date,
    end_date: date,
    text: Optional[str],
    institution: Optional[str],
    courts: Optional[List[str]],
    measures: Optional[List[str]],
    outcomes: Optional[List[str]],
    index: str = ES_INDEX_ORDINANCES,
    content_weight: int = 4,
    dictionary_weight: int = 3,
    pos_weight: int = 2,
    ner_weight: int = 1,
    fields: List[str] = None,
    pre_tag: str = "<b>",
    post_tag: str = "</b>",
    fragment_size: int = 150,
):
    # Default document fields
    if fields is None:
        fields = [
            "institution",
            "content",
            "court",
            "measures",
            "dictionary_keywords",
            "ner_keywords",
            "pos_keywords",
            "publication_date",
        ]
    body = {
        "query": {"bool": {}},
        "highlight": {
            "fields": {"content": {}},
            "pre_tags": [pre_tag],
            "post_tags": [post_tag],
            "fragment_size": fragment_size,
        },
        "_source": fields,
    }
    if text is not None:
        # Fields weighted by priority
        weighted_fields = [
            f"content^{content_weight}",
            f"dictionary_keywords^{dictionary_weight}",
            f"pos_keywords^{pos_weight}",
            f"ner_keywords^{ner_weight}",
        ]
        # Query is a simple multi-match on the weighted fields
        body["query"]["bool"]["should"] = [
            {
                "multi_match": {
                    "query": text,
                    "fields": weighted_fields,
                    "type": "phrase",
                },
            },
            {
                "multi_match": {
                    "query": text,
                    "fields": weighted_fields,
                    "type": "best_fields",
                    "operator": "AND",
                },
            },
            {
                "multi_match": {
                    "query": text,
                    "fields": weighted_fields,
                    "type": "most_fields",  # works better for cases in which the same text is reported into multiple fields
                },
            },
        ]
    # If provided, adds some filters
    filters = [
        {
            "range": {
                "publication_date": {
                    "gte": start_date.strftime("%Y-%m-%d"),
                    "lte": end_date.strftime("%Y-%m-%d"),
                }
            }
        }
    ]
    if courts is not None:
        filters.append({"terms": {"court": courts}})
    if institution is not None:
        filters.append({"term": {"institution.keyword": institution}})
    if measures is not None or outcomes is not None:
        nested_filters = []
        if measures is not None:
            nested_filters.append({"terms": {"measures.measure": measures}})
        if outcomes is not None:
            nested_filters.append({"terms": {"measures.outcome": outcomes}})
        filters.append(
            {
                "nested": {
                    "path": "measures",
                    "query": {"bool": {"must": nested_filters}},
                }
            }
        )
    if len(filters) > 0:
        body["query"]["bool"]["filter"] = filters
    # Performs the query
    response = client.search(body=body, index=index)
    # Collects the results
    results = []
    for hit in response["hits"]["hits"]:
        if "highlight" in hit:
            highlight = "...<br/>".join(hit["highlight"]["content"])
        # If there is nothing to align gets to the first space after 250 chars
        else:
            i = hit["_source"]["content"].index("\n", 250)
            highlight = hit["_source"]["content"][:i] + "..."
        # Reformats source in "HTML-like" format
        hit["_source"]["content"] = hit["_source"]["content"].replace("\n", "<br/>")
        results.append(
            {"highlight": highlight.replace("\n", "<br/>"), **hit["_source"]}
        )
    return results


def edit_publication_date(
    client: Elasticsearch,
    doc_id: str,
    publication_date: date,
    index: str = ES_INDEX_ORDINANCES,
) -> None:
    client.update(
        id=doc_id,
        index=index,
        body={"doc": {"publication_date": publication_date.strftime("%Y-%m-%d")}},
        refresh=True,
    )
