"""Extract public fields from verified local M2 snapshots; no database/network access."""

import argparse
import hashlib
import json
from pathlib import Path

from game_discovery.catalog.contracts import Source
from game_discovery.jobs.catalog import MODE_IDS, normalize_payload, write_json

FIELDS = ("steam_appid", "name", "short_description", "type", "is_free", "platforms", "price_overview",
          "release_date", "categories", "genres", "content_descriptors", "header_image")


def export_fixture(source_run: Path, output: Path) -> None:
    collection = json.loads((source_run / "collection.json").read_text(encoding="utf-8"))
    records = []
    for item in sorted(collection["observations"], key=lambda item: item["app_id"]):
        source = Source.model_validate(item["source"])
        body = (source_run / item["snapshot"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != source.sha256:
            raise ValueError("Original snapshot checksum mismatch")
        payload = json.loads(body)
        original = normalize_payload(item["app_id"], payload, source)
        data = payload[str(item["app_id"])]["data"]
        projection = {str(item["app_id"]): {"success": True, "data": {key: data[key] for key in FIELDS if key in data}}}
        projected_data = projection[str(item["app_id"])]["data"]
        projected_data["categories"] = [term for term in data.get("categories", []) if term.get("id") in MODE_IDS]
        if "price_overview" in data:
            projected_data["price_overview"] = {key: data["price_overview"][key] for key in ("currency", "final") if key in data["price_overview"]}
        projected_data["content_descriptors"] = {"ids": data["content_descriptors"]["ids"]}
        projected = normalize_payload(item["app_id"], projection, source)
        if original.model_dump() != projected.model_dump():
            raise ValueError("Projection changed normalized game facts")
        records.append({"app_id": item["app_id"], "original_source": source.model_dump(mode="json"),
                        "payload": projection})
    if len(records) != 40:
        raise ValueError("M2 replay fixture requires all 40 verified observations")
    write_json(output, {"schema_version": 1, "kind": "steam-appdetails-field-projections",
                        "note": "Frozen real-source field projections, not full original HTTP bodies or live prices. "
                                "original_source.sha256 identifies the original locally retained HTTP response.",
                        "records": records})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_fixture(args.source_run, args.output)
