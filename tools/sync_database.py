"""Validate and copy the pinout-pages snapshot into the distributable package."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pinout_cli.database import Database, definition_files, read_file  # noqa: E402
from pinout_cli.export import atomic_write  # noqa: E402
from pinout_cli.models import DefinitionError  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="pinout-pages/database directory")
    args = parser.parse_args()
    files = definition_files(args.source)
    if not files or any(p.suffix != ".json" for p in files):
        parser.error("source must contain JSON catalog files")
    database = Database()
    for path in files:
        definitions = read_file(path)
        if database.components.keys() & definitions.keys():
            raise DefinitionError(f"duplicate IDs in {path}")
        database.merge(definitions)
    database.reindex()
    target = ROOT / "pinout_cli" / "data"
    for path in files:
        atomic_write(target / path.name, path.read_text(encoding="utf-8-sig"))
    # Remove stale bundled categories only inside the known package data directory.
    names = {p.name for p in files}
    for path in target.glob("*.json"):
        if path.name not in names:
            path.unlink()
    print(f"Bundled {len(database.components)} components from {args.source}")


if __name__ == "__main__":
    main()
