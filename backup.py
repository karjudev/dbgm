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


if __name__ == "__main__":
    app()
