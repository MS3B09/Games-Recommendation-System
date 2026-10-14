"""Generate a configuration-independent public contract without database access."""

import argparse
import json
from pathlib import Path

from game_discovery.api.main import create_app
from game_discovery.core.settings import Settings
from game_discovery.db.readiness import CatalogReadiness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("backend/openapi.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    app = create_app(Settings(), catalog_probe=CatalogReadiness)
    content = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != content:
            parser.exit(1, "Public API contract is stale; regenerate it.\n")
    else:
        args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
