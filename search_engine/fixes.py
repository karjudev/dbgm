from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Mapping
import requests
import typer
import srsly
from tqdm import tqdm


def __get_data(records: Iterable[Mapping]) -> Iterator[Mapping]:
    for record in records:
        data = record["_source"]
        timestamp = data["timestamp"]
        try:
            timestamp = datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d")
        except:
            try:
                timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
            except:
                pass
        yield record["_id"], {
            "timestamp": timestamp,
            "filename": data["filename"],
            "username": data["username"],
            "institution": data["institution"],
            "court": data["court"],
            "content": data["content"],
            "measures": data["measures"],
            "publication_date": data["publication_date"],
        }


def main(
    input_filename: Path,
    host: str,
    port: int,
) -> None:
    base_url = f"http://{host}:{port}/ordinances"
    records = srsly.read_jsonl(input_filename)
    records = __get_data(records)
    for doc_id, data in tqdm(records):
        url = f"{base_url}/{doc_id}"
        response = requests.put(url, json=data)
        response.raise_for_status()


if __name__ == "__main__":
    typer.run(main)
