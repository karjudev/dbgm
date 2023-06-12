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


def stats_ordinances(
    client: Elasticsearch, index: str = ES_INDEX_ORDINANCES
) -> Tuple[int, int]:
    """Statistics about the documents.

    Args:
        client (Elasticsearch): Connection to Elasticsearch.
        index (str, optional): Index name. Defaults to ES_INDEX_ORDINANCES.

    Returns:
        Tuple[int, int]: Number of documents and of courts.
    """
    # Simple count of distinct documents
    count = client.count(index=index)["count"]
    # Approximated count of distinct court values
    aggs_body = {
        "size": 0,
        "aggregations": {
            "num_courts": {"cardinality": {"field": "court"}},
        },
    }
    response = client.search(body=aggs_body, index=index)
    courts = response["aggregations"]["num_courts"]["value"]
    return count, courts


def count_ordinances_by_type_by_outcome(
    client: Elasticsearch, index: str = ES_INDEX_ORDINANCES
) -> Mapping[str, Mapping[str, Mapping[str, int]]]:
    """Counts the measures per type and per outcome.

    Args:
        client (Elasticsearch): Elasticsearch client.
        index (str, optional): Index in Elasticsearch. Defaults to ES_INDEX_ORDINANCES.

    Returns:
        Mapping[str, Mapping[str, Mapping[str, int]]]: For each court, for each measure type, for each outcome, its count.
    """
    query_body = {
        "size": 0,
        "aggs": {
            "institutions": {
                "terms": {"field": "institution.keyword"},
                "aggs": {
                    "courts": {
                        "terms": {"field": "court"},
                        "aggs": {
                            "measures": {
                                "nested": {"path": "measures"},
                                "aggs": {
                                    "measure_outcome": {
                                        "terms": {
                                            "script": {
                                                "source": "doc['measures.measure'].value + '|' + doc['measures.outcome'].value",
                                                "lang": "painless",
                                            },
                                            "order": {"_key": "asc"},
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
            }
        },
    }
    response = client.search(body=query_body, index=index)
    result = dict()
    for institution_bucket in response["aggregations"]["institutions"]["buckets"]:
        institution = institution_bucket["key"]
        for court_bucket in institution_bucket["courts"]["buckets"]:
            court = court_bucket["key"]
            measures = dict()
            for measure_outcome_bucket in court_bucket["measures"]["measure_outcome"][
                "buckets"
            ]:
                measure, outcome = measure_outcome_bucket["key"].split("|")
                count = measure_outcome_bucket["doc_count"]
                measures.setdefault(measure, dict())[outcome] = count
            result[institution + " - " + court] = measures
    return result


def extract_significant_keywords(
    client: Elasticsearch, index: str = ES_INDEX_ORDINANCES
) -> Mapping[str, Mapping[str, int]]:
    """Extracts the significant keywords for each court.

    Args:
        client (Elasticsearch): Elasticsearch client.
        index (str, optional): Index in Elasticsearch. Defaults to ES_INDEX_ORDINANCES.

    Returns:
        Mapping[str, Mapping[str, int]]: For each court, for each juridic keyword, its frequency.
    """
    # Performs the aggregations
    query_body = {
        "size": 0,
        "aggs": {
            "institutions": {
                "terms": {"field": "institution.keyword"},
                "aggs": {
                    "courts": {
                        "terms": {"field": "court"},
                        "aggs": {
                            "significant_keywords": {
                                "significant_terms": {"field": "dictionary_keywords"}
                            }
                        },
                    }
                },
            }
        },
    }
    response = client.search(query_body, index=index)
    result = dict()
    for institution_bucket in response["aggregations"]["institutions"]["buckets"]:
        institution = institution_bucket["key"]
        for court_bucket in institution_bucket["courts"]["buckets"]:
            court = court_bucket["key"]
            court_refs = {
                bucket["key"]: bucket["score"]
                for bucket in court_bucket["significant_keywords"]["buckets"]
            }
            # Normalizes the scores in the interval [0, 1]
            total_score = sum(court_refs.values()) + 1e-16
            court_refs = {key: score / total_score for key, score in court_refs.items()}
            result[institution + " - " + court] = court_refs
    return result


def query_ordinances(
    client: Elasticsearch,
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
    filters = []
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
