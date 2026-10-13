"""Bounded archive reader: never extract paths or links onto the filesystem."""

import io
import json
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath

from .database import MAX_FILE_BYTES, Database, decode
from .export import atomic_write
from .models import DefinitionError

REMOTE_URL = "https://codeload.github.com/norbertsawe/pinout-pages/tar.gz/refs/heads/main"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 32 * 1024 * 1024


def parse_archive(payload: bytes) -> dict:
    db = Database()
    expanded = 0
    files = 0
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for index, member in enumerate(archive):
            if index > 2000:
                raise DefinitionError("archive contains too many entries")
            parts = PurePosixPath(member.name).parts
            if (
                member.name.startswith(("/", "\\"))
                or ".." in parts
                or "\\" in member.name
                or any(":" in p for p in parts)
            ):
                raise DefinitionError("unsafe archive path")
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise DefinitionError("archive contains a link or special file")
            expanded += member.size
            if expanded > MAX_EXPANDED_BYTES:
                raise DefinitionError("archive exceeds expanded size limit")
            if len(parts) != 3 or parts[1] != "database" or not member.isfile():
                continue
            suffix = PurePosixPath(parts[-1]).suffix.lower()
            if suffix not in {".json", ".yaml", ".yml"}:
                continue
            if member.size > MAX_FILE_BYTES:
                raise DefinitionError("database file exceeds size limit")
            stream = archive.extractfile(member)
            if stream is None:
                raise DefinitionError("cannot read database file")
            definitions = decode(stream.read(MAX_FILE_BYTES + 1).decode("utf-8-sig"), suffix)
            if db.components.keys() & definitions.keys():
                raise DefinitionError("duplicate component IDs in remote archive")
            db.merge(definitions)
            files += 1
    if not files or not db.components:
        raise DefinitionError("archive contains no database definitions")
    db.reindex()
    return {key: c.to_dict() for key, c in db.components.items()}


def update_database(directory: Path) -> int:
    request = urllib.request.Request(REMOTE_URL, headers={"User-Agent": "pinout-cli/2.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise DefinitionError("download exceeds archive size limit")
    definitions = parse_archive(payload)
    # Verify aliases together with bundled components before accepting the snapshot.
    db = Database.bundled()
    db.merge(decode(json.dumps(definitions)), remote=True)
    db.reindex()
    snapshot = json.dumps(definitions, indent=2, ensure_ascii=False) + "\n"
    if len(snapshot.encode("utf-8")) > MAX_FILE_BYTES:
        raise DefinitionError("merged database exceeds cache size limit")
    atomic_write(directory / "database.json", snapshot)
    return len(definitions)
