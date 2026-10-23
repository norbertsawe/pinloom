import copy
import json
import urllib.request
from pathlib import Path

import jsonschema
import pytest

from pinloom.database import Database, decode, read_file
from pinloom.models import Component, DefinitionError

ROOT = Path(__file__).resolve().parents[1]


def test_offline_first_use_has_requested_families(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("lookup tried to access the network")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    db = Database.load(tmp_path / "data", tmp_path / "config")
    assert len(db.components) >= 2088
    for key in (
        "atmega328p",
        "uno",
        "nano",
        "esp32",
        "esp32s3",
        "esp32c3",
        "esp8266",
        "stm32",
        "nucleo-f401re",
        "pico",
        "ne555",
        "74hc595",
        "lm358",
        "mcp23017",
        "ne5532",
        "pcm5102a",
        "usb-a",
        "usb-c",
        "raspberry-pi-40",
        "swd",
        "jtag",
        "icsp",
    ):
        component = db.exact(key)
        assert component and component.pins and component.sources and component.package
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "config").exists()


def test_catalog_matches_schema():
    schema = json.loads((ROOT / "docs/component.schema.json").read_text())
    for file in (ROOT / "pinloom/data").glob("*.json"):
        jsonschema.validate(json.loads(file.read_text(encoding="utf-8")), schema)
    jsonschema.validate(json.loads((ROOT / "examples/custom.json").read_text()), schema)


def test_custom_precedence_and_utf8_bom(tmp_path, write_definition):
    config, data = tmp_path / "config", tmp_path / "data"
    write_definition(data / "database.json", "ne555", {"name": "remote"})
    write_definition(config / "components/board.json", "ne555", {"name": "config"})
    explicit = write_definition(tmp_path / "explicit.json", "ne555", {"name": "explicit"})
    explicit.write_text(explicit.read_text(encoding="utf-8"), encoding="utf-8-sig")
    assert Database.load(data, config).exact("ne555").name == "config"
    assert Database.load(data, config, [explicit]).exact("ne555").name == "explicit"


def test_corrupt_cache_is_reported_and_bundled_still_loads(tmp_path):
    (tmp_path / "database.json").write_text("not json")
    db = Database.load(tmp_path, tmp_path / "config")
    assert db.exact("pico").pins
    assert len(db.warnings) == 1


def test_conflicting_cache_alias_does_not_disable_lookup(tmp_path, write_definition):
    write_definition(tmp_path / "database.json", "conflict", {"aliases": ["pico"]})
    db = Database.load(tmp_path, tmp_path / "config")
    assert db.exact("pico").id == "pico"
    assert "conflict" not in db.components
    assert "ambiguous alias" in db.warnings[0]


def test_invalid_implicit_custom_warns_but_explicit_errors(tmp_path):
    path = tmp_path / "components/bad.json"
    path.parent.mkdir()
    path.write_text("{}")
    assert Database.load(tmp_path / "data", tmp_path).warnings
    with pytest.raises(DefinitionError):
        Database.load(tmp_path / "data", tmp_path, [path])


def test_legacy_remote_cannot_downgrade_bundled_data(tmp_path):
    legacy = {
        "ne555": {"name": "legacy", "description": "Old timer", "ascii_art": "\x1b[31mART\x1b[0m"},
        "old-part": {"name": "Old part", "description": "legacy", "ascii_art": "ART"},
    }
    (tmp_path / "database.json").write_text(json.dumps(legacy))
    db = Database.load(tmp_path, tmp_path / "config")
    assert len(db.exact("ne555").pins) == 8
    assert db.exact("old-part").ascii_art == "ART"


@pytest.mark.parametrize(
    "updates",
    [
        {"schema_version": 99},
        {"schema_version": True},
        {"pins": "not an array"},
        {"pins": []},
        {"aliases": "wrong"},
        {"layout": {"type": "qfn"}},
        {"layout": {"type": []}},
        {"layout": {"type": "table", "orientation": 1}},
        {"electrical": []},
        {"sources": [1]},
        {"name": "\x1b[31m"},
    ],
)
def test_invalid_shapes_raise_definition_errors(record, updates):
    record.update(updates)
    with pytest.raises(DefinitionError):
        decode(json.dumps({"custom": record}))


def test_duplicate_pins_and_incomplete_layout_rejected(record):
    record["pins"].append(copy.deepcopy(record["pins"][0]))
    with pytest.raises(DefinitionError, match="duplicate pin"):
        Component.parse("custom", record)
    record["pins"].pop()
    record["layout"] = {"type": "dual", "rows": [["1", "2"]]}
    with pytest.raises(DefinitionError, match="every pin"):
        Component.parse("custom", record)


def test_normalized_aliases_and_collisions(db, record):
    assert db.exact("ESP32-S3").id == "esp32s3"
    assert db.exact("Arduino Uno").id == "uno"
    assert db.exact("hc-sr04").id == "hcsr04"
    record["aliases"] = ["pico"]
    db.merge({"custom": Component.parse("custom", record)})
    with pytest.raises(DefinitionError, match="ambiguous alias"):
        db.reindex()


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
def test_duplicate_mapping_keys_rejected(suffix):
    text = '{"a": 1, "a": 2}' if suffix == ".json" else "a: 1\na: 2\n"
    with pytest.raises(DefinitionError, match="duplicate mapping key"):
        decode(text, suffix)


def test_yaml_object_constructors_rejected():
    with pytest.raises(DefinitionError):
        decode('!!python/object/apply:os.system ["echo bad"]', ".yaml")


def test_json_yaml_examples_equivalent():
    assert read_file(ROOT / "examples/custom.json") == read_file(ROOT / "examples/custom.yaml")
