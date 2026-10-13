import io
import json
import tarfile
import urllib.error

import pytest

from pinout_cli import update
from pinout_cli.database import Database, read_file
from pinout_cli.models import DefinitionError


def archive(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, payload, kind in entries:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(payload) if kind == tarfile.REGTYPE else 0
            if kind in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                info.linkname = "outside"
            tar.addfile(info, io.BytesIO(payload) if info.size else None)
    return buffer.getvalue()


def valid_archive(record):
    return archive(
        [
            (
                "pinout-pages-main/database/test.json",
                json.dumps({"remote-part": record}).encode(),
                tarfile.REGTYPE,
            )
        ]
    )


def test_update_commits_only_valid_complete_snapshot(record, tmp_path, monkeypatch):
    monkeypatch.setattr(
        update.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(valid_archive(record))
    )
    assert update.update_database(tmp_path) == 1
    assert "remote-part" in read_file(tmp_path / "database.json")
    assert Database.load(tmp_path, tmp_path / "config").exact("remote-part")


@pytest.mark.parametrize(
    "name,kind",
    [
        ("repo/database/../../evil.json", tarfile.REGTYPE),
        ("/repo/database/evil.json", tarfile.REGTYPE),
        ("C:/repo/database/evil.json", tarfile.REGTYPE),
        ("repo\\database\\evil.json", tarfile.REGTYPE),
        ("repo/database/link.json", tarfile.SYMTYPE),
        ("repo/database/link.json", tarfile.LNKTYPE),
        ("repo/database/device", tarfile.CHRTYPE),
    ],
)
def test_archive_rejects_unsafe_members(record, name, kind):
    payload = archive([(name, json.dumps({"custom": record}).encode(), kind)])
    with pytest.raises(DefinitionError):
        update.parse_archive(payload)


def test_failed_download_preserves_cache(tmp_path, monkeypatch):
    path = tmp_path / "database.json"
    path.write_text("previous")

    def fail(*a, **kw):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(update.urllib.request, "urlopen", fail)
    with pytest.raises(urllib.error.URLError):
        update.update_database(tmp_path)
    assert path.read_text() == "previous"


@pytest.mark.parametrize(
    "payload",
    [b"not gzip", archive([]), archive([("repo/database/a.json", b"{}", tarfile.REGTYPE)])],
)
def test_invalid_download_preserves_cache(tmp_path, monkeypatch, payload):
    path = tmp_path / "database.json"
    path.write_text("previous")
    monkeypatch.setattr(update.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(payload))
    with pytest.raises((DefinitionError, tarfile.TarError)):
        update.update_database(tmp_path)
    assert path.read_text() == "previous"


def test_remote_alias_conflict_with_bundle_preserves_cache(tmp_path, record, monkeypatch):
    record["aliases"] = ["pico"]
    path = tmp_path / "database.json"
    path.write_text("previous")
    monkeypatch.setattr(
        update.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(valid_archive(record))
    )
    with pytest.raises(DefinitionError, match="ambiguous alias"):
        update.update_database(tmp_path)
    assert path.read_text() == "previous"


def test_archive_duplicate_component_ids_rejected(record):
    payload = json.dumps({"custom": record}).encode()
    data = archive(
        [
            ("repo/database/a.json", payload, tarfile.REGTYPE),
            ("repo/database/b.json", payload, tarfile.REGTYPE),
        ]
    )
    with pytest.raises(DefinitionError, match="duplicate component IDs"):
        update.parse_archive(data)


def test_size_limits_rejected_before_commit(record, tmp_path, monkeypatch):
    payload = valid_archive(record)
    monkeypatch.setattr(update.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(payload))
    monkeypatch.setattr(update, "MAX_ARCHIVE_BYTES", 4)
    with pytest.raises(DefinitionError, match="download exceeds"):
        update.update_database(tmp_path)
    monkeypatch.setattr(update, "MAX_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(update, "MAX_FILE_BYTES", 4)
    with pytest.raises(DefinitionError, match="file exceeds"):
        update.update_database(tmp_path)
    assert not (tmp_path / "database.json").exists()
