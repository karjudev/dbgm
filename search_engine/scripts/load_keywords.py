from pathlib import Path
from typing import Iterable, List, Mapping
import typer
import srsly

from app.elastic.db import (
    ES_INDEX_KEYWORDS,
    ES_MAPPING_KEYWORDS,
    bulk_upload,
    connect_elasticsearch,
    is_index_populated,
)


def __build_percolate_query(
    keyword: str, entity: str, minimum_percentage: int, measures: List[str]
) -> Mapping:
    return {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "content": {
                                "query": keyword,
                                "analyzer": "italian",
                                "operator": "AND",
                                "minimum_should_match": f"{minimum_percentage}%",
                            }
                        }
                    },
                    {
                        "nested": {
                            "path": "measures",
                            "query": {"terms": {"measures.measure": measures}},
                        }
                    },
                ]
            }
        },
        "keyword": keyword,
        "entity": entity,
    }


def __json_to_body(
    filepath: Path, minimum_percentage: int = 60
) -> Iterable[Mapping[str, str]]:
    content = srsly.read_json(filepath)
    for entity, data in content.items():
        measures = data["measures"]
        keywords = data["keywords"]
        yield __build_percolate_query(
            keyword=entity,
            entity=entity,
            minimum_percentage=minimum_percentage,
            measures=measures,
        )
        for keyword in keywords:
            yield __build_percolate_query(
                keyword=keyword,
                entity=entity,
                minimum_percentage=minimum_percentage,
                measures=measures,
            )


def main(filepath: Path, index: str = ES_INDEX_KEYWORDS) -> None:
    # Connects to Elasticsearch
    client = connect_elasticsearch(index=index, mapping=ES_MAPPING_KEYWORDS)
    typer.echo("Connected to Elasticsearch")
    # Checks that index is populated
    if is_index_populated(client, index=index):
        typer.echo("Keyword index is already populated.")
    else:
        # Inserts keywords in bulk
        bulk_upload(client=client, records=__json_to_body(filepath), index=index)
        typer.echo("Keyword index populated")


if __name__ == "__main__":
    typer.run(main)
