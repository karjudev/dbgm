from pathlib import Path
from typing import Any, Iterator, List, Mapping, Optional, Tuple
from tqdm import tqdm
import typer
import srsly
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import scan
from services.anonymizer import predict_annotations, correct_annotations
from services.search_engine import send_ordinance


app = typer.Typer()


@app.command()
def upload(
    filepath: Path,
    anonymizer_url: str = "http://localhost:8080",
    search_url: str = "http://localhost:8081",
) -> None:
    for record in tqdm(srsly.read_jsonl(filepath)):
        # Extracts parameters
        timestamp: str = record["timestamp"]
        username: str = record["username"]
        filename: str = record["filename"]
        text: str = record["content"]
        ground_truth: List[Mapping] = record["ground_truth"]
        institution = record["institution"]
        court: str = record["court"]
        measures: List[Mapping] = record["measures"]
        # Creates the record in the Documents (anonymization) Elasticsearch
        try:
            predicted: List[Mapping] = predict_annotations(
                text, base_url=anonymizer_url
            )
            doc_id = correct_annotations(
                username,
                filename,
                text,
                predicted,
                ground_truth,
                timestamp=timestamp,
                base_url=anonymizer_url,
            )
            # Creates the record in the Ordinances (search engine) Elasticsearch
            send_ordinance(
                doc_id,
                username,
                filename,
                institution,
                court,
                text,
                ground_truth,
                measures,
                timestamp=timestamp,
                base_url=search_url,
            )
        except ValueError as e:
            print(e)
            continue


def __scan_index(
    client: Elasticsearch, index: str
) -> Iterator[Tuple[str, Mapping[str, Any]]]:
    query = {"sort": {"timestamp": "asc"}}
    for hit in scan(client, index=index, query=query):
        yield hit["_id"], hit["_source"]


def __get_item(
    client: Elasticsearch, index: str, doc_id: str, fields: List[str]
) -> Optional[Mapping[str, Any]]:
    try:
        result = client.get(index=index, id=doc_id, _source=fields)
        return result["_source"]
    except NotFoundError:
        return None


def __merge_indices(
    anon_es: Elasticsearch,
    search_es: Elasticsearch,
    anon_index: str = "documents",
    search_index: str = "ordinances",
) -> Iterator[Mapping[str, Any]]:
    for doc_id, anon_hit in __scan_index(anon_es, index=anon_index):
        search_hit = __get_item(
            search_es,
            index=search_index,
            doc_id=doc_id,
            fields=[
                "institution",
                "court",
                "measures",
                "dictionary_keywords",
                "ner_keywords",
                "pos_keywords",
            ],
        )
        if search_hit is None:
            typer.echo(
                f"Document {anon_hit['filename']} not found in the search engine.",
                err=True,
            )
        else:
            yield {"doc_id": doc_id, **anon_hit, **search_hit}


@app.command()
def download(
    filepath: Path,
    anonymizer_es: str = "http://localhost:9200",
    search_es: str = "http://localhost:9201",
) -> None:
    anonymizer = Elasticsearch(anonymizer_es)
    search = Elasticsearch(search_es)
    srsly.write_jsonl(filepath, __merge_indices(anonymizer, search))


if __name__ == "__main__":
    app()
