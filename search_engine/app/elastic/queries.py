from datetime import date
from typing import List, Mapping, Tuple
from elasticsearch import Elasticsearch
from app.elastic.db import ES_INDEX_ORDINANCES, ES_INDEX_KEYWORDS


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
    text: str | None,
    keywords: List[str] | None,
    concepts: List[str] | None,
    institution: List[str] | None,
    courts: List[str] | None,
    measures: List[str] | None,
    outcome: bool | None,
    index: str = ES_INDEX_ORDINANCES,
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
            "publication_date",
            "dictionary_keywords",
            "textrank_keywords",
            "juridic_keywords",
            "juridic_concepts",
        ]
    # Query body with aggregation
    body = {
        "query": {"bool": {}},
        "highlight": {
            "fields": {"content": {}},
            "pre_tags": [pre_tag],
            "post_tags": [post_tag],
            "fragment_size": fragment_size,
        },
        "aggs": {
            "keywords": {"terms": {"field": "juridic_keywords", "size": 100_000}},
            "concepts": {"terms": {"field": "juridic_concepts", "size": 100_000}},
            "by_institution": {
                "terms": {"field": "institution"},
                "aggs": {
                    "by_court": {
                        "terms": {"field": "court"},
                        "aggs": {
                            "by_year": {
                                "date_histogram": {
                                    "field": "publication_date",
                                    "calendar_interval": "year",
                                },
                                "aggs": {
                                    "nested_measure": {
                                        "nested": {"path": "measures"},
                                        "aggs": {
                                            "by_measure": {
                                                "terms": {"field": "measures.measure"},
                                                "aggs": {
                                                    "by_outcome": {
                                                        "terms": {
                                                            "field": "measures.outcome"
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
                },
            },
        },
        "_source": fields,
    }
    if text is not None:
        # Query is a simple multi-match on the weighted fields
        body["query"]["bool"]["must"] = {"match": {"content": text}}
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
    if keywords is not None:
        filters.append(
            {"bool": {"must": [{"term": {"juridic_keywords": kw}} for kw in keywords]}}
        )
    if concepts is not None:
        filters.append(
            {"bool": {"must": [{"term": {"juridic_concepts": cp}} for cp in concepts]}}
        )
    if courts is not None:
        filters.append({"terms": {"court": courts}})
    if institution is not None:
        filters.append({"term": {"institution": institution}})
    if measures is not None or outcome is not None:
        nested_filters = []
        if measures is not None:
            nested_filters.append({"terms": {"measures.measure": measures}})
        if outcome is not None:
            nested_filters.append({"term": {"measures.outcome": outcome}})
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
    print(body, flush=True)
    # Performs the query
    response = client.search(body=body, index=index)
    # Collects the hits (for list view)
    hits = []
    for hit in response["hits"]["hits"]:
        if "highlight" in hit:
            highlight = " ".join(hit["highlight"]["content"]).replace("\n", "<br/>")
        # If there is nothing to align gets to the first space after 250 chars
        else:
            highlight = "..."
        hits.append({"highlight": highlight, **hit["_source"]})
    # Collects the aggregations (for map view)
    aggregations = dict()
    for institution in response["aggregations"]["by_institution"]["buckets"]:
        institution_key = institution["key"]
        courts = dict()
        for court in institution["by_court"]["buckets"]:
            court_key = court["key"]
            years = dict()
            for year in court["by_year"]["buckets"]:
                year_number = int(year["key_as_string"].split("-", maxsplit=1)[0])
                year_count = year["doc_count"]
                # Skips un-meaningful years
                if year_count == 0:
                    continue
                measures = dict()
                for measure in year["nested_measure"]["by_measure"]["buckets"]:
                    measure_key = measure["key"]
                    outcomes = {"true": 0, "false": 0}
                    for outcome in measure["by_outcome"]["buckets"]:
                        outcome_key = outcome["key_as_string"]
                        outcome_count = outcome["doc_count"]
                        outcomes[outcome_key] = outcome_count
                    measures[measure_key] = outcomes
                years[year_number] = measures
            courts[court_key] = years
        aggregations[institution_key] = courts
    # Collects juridic keywords and concepts
    keywords = [
        bucket["key"] for bucket in response["aggregations"]["keywords"]["buckets"]
    ]
    concepts = [
        bucket["key"] for bucket in response["aggregations"]["concepts"]["buckets"]
    ]
    # Collects the number of hits
    num_hits = response["hits"]["total"]["value"]
    return aggregations, hits, keywords, concepts, num_hits


def edit_publication_date(
    client: Elasticsearch,
    doc_id: str,
    publication_date: date,
    index: str = ES_INDEX_ORDINANCES,
) -> None:
    # Updates the publication date of a certain document.
    try:
        client.update(
            id=doc_id,
            index=index,
            body={"doc": {"publication_date": publication_date.strftime("%Y-%m-%d")}},
            refresh=True,
        )
        return True
    except:
        return False


def extract_keywords(
    client: Elasticsearch,
    content: str,
    measures: List[Mapping],
    index: str = ES_INDEX_KEYWORDS,
) -> Tuple[List[str], List[str]]:
    # Query for percolation and keyword extraction
    body = {
        "size": 0,
        "query": {
            "percolate": {
                "field": "query",
                "document": {"content": content, "measures": measures},
            }
        },
        "aggs": {
            "keywords": {"terms": {"field": "keyword.keyword"}},
            "entities": {"terms": {"field": "entity.keyword"}},
        },
    }
    response = client.search(body=body, index=index)
    # Collects the results
    keywords = [
        bucket["key"] for bucket in response["aggregations"]["keywords"]["buckets"]
    ]
    entities = [
        bucket["key"] for bucket in response["aggregations"]["entities"]["buckets"]
    ]
    return keywords, entities
