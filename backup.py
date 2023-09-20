from pathlib import Path
from typing import Iterable, Iterator, Mapping
import typer
import srsly
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk


app = typer.Typer()


def __scan_elasticsearch(client: Elasticsearch, index: str) -> Iterator[Mapping]:
    return scan(client, index=index, preserve_order=True)


def __bulk_elasticsearch(
    client: Elasticsearch, index: str, records: Iterable[Mapping]
) -> None:
    return bulk(client, actions=records, index=index)


@app.command()
def download(hostname: str, port: int, index: str, filename: Path) -> None:
    client = Elasticsearch(hosts=[{"host": hostname, "port": port}])
    records = __scan_elasticsearch(client, index)
    srsly.write_jsonl(filename, records)


@app.command()
def upload(hostname: str, port: int, index: str, filename: Path) -> None:
    client = Elasticsearch(hosts=[{"host": hostname, "port": port}])
    records = srsly.read_jsonl(filename)
    __bulk_elasticsearch(client, index, records)


@app.command()
def test_set(
    filename: Path,
    anonymizer_host: str = "localhost",
    anonymizer_port: int = 9200,
    anonymizer_index: str = "documents",
    search_host: str = "localhost",
    search_port: int = 9201,
    search_index: str = "ordinances",
    avoid_court: str = "Genova",
    max_size: int = 200,
) -> None:
    anonymizer_es = Elasticsearch(
        hosts=[{"host": anonymizer_host, "port": anonymizer_port}]
    )
    search_es = Elasticsearch(hosts=[{"host": search_host, "port": search_port}])
    # Query to search documents that avoid a certain court
    search_query = {
        "size": max_size,
        "_source": ["_id"],
        "query": {
            "bool": {
                "filter": [
                    {"term": {"institution": "Tribunale di Sorveglianza"}},
                    {"bool": {"must_not": {"term": {"court": avoid_court}}}},
                ]
            }
        },
    }
    response = search_es.search(body=search_query, index=search_index)
    # IDs of the documents responding to the query
    doc_ids = [hit["_id"] for hit in response["hits"]["hits"]]
    # Searches for the docs and extracts content and entities
    anonymizer_query = {
        "size": max_size,
        "_source": ["timestamp", "content", "ground_truth"],
        "query": {"ids": {"values": doc_ids}},
    }
    response = anonymizer_es.search(body=anonymizer_query, index=anonymizer_index)
    # Collects search results
    documents = (
        {
            "timestamp": hit["_source"]["timestamp"],
            "text": hit["_source"]["content"],
            "entities": hit["_source"]["ground_truth"],
        }
        for hit in response["hits"]["hits"]
    )
    srsly.write_jsonl(filename, documents)


if __name__ == "__main__":
    app()
