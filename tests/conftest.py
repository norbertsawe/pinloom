import json

import pytest

from pinloom.database import Database


@pytest.fixture
def db(tmp_path):
    return Database.load(tmp_path / "data", tmp_path / "config")


@pytest.fixture
def record(db):
    result = db.exact("ne555").to_dict()
    result["aliases"] = []
    return result


@pytest.fixture
def write_definition(record):
    def write(path, key="custom", changes=None):
        definition = dict(record)
        definition.update(changes or {})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({key: definition}), encoding="utf-8")
        return path

    return write
