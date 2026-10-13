import csv
import io
import re

import pytest

from pinout_cli import export
from pinout_cli.database import decode
from pinout_cli.export import serialize
from pinout_cli.render import render


@pytest.mark.parametrize("width", [12, 20, 40, 80, 120])
def test_entire_catalog_fits_width_with_all_pin_numbers(db, width):
    for component in db.components.values():
        text = render(component, width=width)
        assert max(map(len, text.splitlines())) <= width, component.id
        assert "\x1b" not in text
        for pin in component.pins:
            assert re.search(rf"(?<!\w){re.escape(pin.number)}(?!\w)", text), (
                component.id,
                pin.number,
            )


def test_dip_orientation_and_colors(db):
    text = render(db.exact("ne555"), color=True, unicode=False, width=100)
    assert "\x1b[31m" in text and "\x1b[90m" in text
    stripped = re.sub(r"\x1b\[[0-9;]+m", "", text)
    assert "GND | 1   8 | [PWR] VCC" in stripped
    assert "/RST | 4   5 | [ANA] CONT" in stripped
    assert "┌" in render(db.exact("ne555"), unicode=True)


@pytest.mark.parametrize("format", ["json", "yaml"])
def test_full_catalog_definition_round_trips(db, format):
    for component in db.components.values():
        text = serialize(component, format)
        reloaded = decode(text, ".yaml" if format == "yaml" else ".json")[component.id]
        assert reloaded == component


@pytest.mark.parametrize("format", ["json", "yaml"])
def test_selected_pin_export_has_reloadable_table_layout(db, format):
    component = db.exact("pico")
    selected = (component.pins[23],)
    result = decode(serialize(component, format, pins=selected), "." + format)["pico"]
    assert result.pins == selected
    assert result.layout["type"] == "table"


def test_csv_contains_functions_and_voltage(db):
    rows = list(csv.DictReader(io.StringIO(serialize(db.exact("pico"), "csv"))))
    assert len(rows) == 40
    assert rows[23]["name"] == "GP18"
    assert "SPI0 SCK" in rows[23]["functions"]
    assert "3.3 V" in rows[23]["voltage"]


def test_atomic_write_failure_preserves_previous_file(tmp_path, monkeypatch):
    path = tmp_path / "keep.json"
    path.write_text("old")

    def fail(*args):
        raise PermissionError("simulated rename failure")

    monkeypatch.setattr(export.os, "replace", fail)
    with pytest.raises(PermissionError):
        export.atomic_write(path, "new")
    assert path.read_text() == "old"
    assert list(tmp_path.iterdir()) == [path]
