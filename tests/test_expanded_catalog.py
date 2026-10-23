"""Catalog growth, importer edge cases, and browsing at realistic catalog size."""

import io

import pytest

from pinout_cli.browse import catalog_view, category_view
from pinout_cli.search import choose, search
from tools.import_kicad import REVISION, symbols


def test_expansion_is_2000_real_pin_maps_with_provenance(db):
    imported = [
        c for c in db.components.values() if any("Adapted from KiCad symbol" in n for n in c.notes)
    ]
    assert len(imported) == 2000
    assert len(db.components) == 2088
    assert sum(len(c.pins) for c in db.components.values()) == 39934
    assert len({c.category for c in imported}) == 13
    for component in imported:
        assert component.pins
        assert component.layout["type"] == "table"
        assert "http" in component.sources[0]
        assert REVISION in component.sources[1]
        assert component.package != "Unspecified"


def test_importer_combines_units_and_skips_demorgan_duplicates(tmp_path):
    path = tmp_path / "fixture.lib"
    path.write_text("""DEF Dual U 0 5 Y Y 2 F N
F2 "Package_SO:SOIC-8" 0 0 50 H I C CNN
X VCC 8 0 0 100 R 50 50 0 1 W
X ~RESET 1 0 0 100 R 50 50 1 1 I
X OUT 7 0 0 100 R 50 50 2 1 O
X inverted_body 1 0 0 100 R 50 50 1 2 I
ENDDEF
""")
    record = list(symbols(path))[0]
    assert record["pins"] == {"8": ("VCC", "W"), "1": ("~RESET", "I"), "7": ("OUT", "O")}
    assert not record.get("conflict")
    path.write_text(path.read_text().replace("ENDDEF", "X OTHER 1 0 0 100 R 50 50 2 1 I\nENDDEF"))
    assert list(symbols(path))[0]["conflict"]


@pytest.mark.parametrize("width", [12, 40, 80])
def test_catalog_views_fit_narrow_terminals(db, width):
    components = search(db, "")[:3]
    text = catalog_view(components, total=2088, width=width)
    assert all(len(line) <= width for line in text.splitlines())
    assert all(
        len(line) <= width for line in category_view(db.components.values(), width).splitlines()
    )
    assert "\x1b" not in text


def test_finder_pages_beyond_first_twelve(db, monkeypatch):
    answers = iter(["n", "p", "n", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    output = io.StringIO()
    assert choose(db, "", output).id == search(db, "")[12].id
    assert "page 2" in output.getvalue()


def test_full_catalog_fits_reloadable_cache(db, tmp_path):
    import json

    from pinout_cli.database import MAX_FILE_BYTES, read_file

    path = tmp_path / "database.json"
    path.write_text(
        json.dumps({k: c.to_dict() for k, c in db.components.items()}, indent=2), encoding="utf-8"
    )
    assert path.stat().st_size < MAX_FILE_BYTES
    assert len(read_file(path)) == 2088


def test_imported_sensor_and_converter_physical_pins(db):
    # Source pin maps include non-sequential symbol units and separate ground pads.
    bme = {p.number: p.name for p in db.exact("bme280").pins}
    assert bme == {
        "1": "GND",
        "2": "CSB",
        "3": "SDI",
        "4": "SCK",
        "5": "SDO",
        "6": "VDDIO",
        "7": "GND",
        "8": "VDD",
    }
    adc = {p.number: p.name for p in db.exact("ad7606").pins}
    assert len(adc) == 64
    assert adc["1"] == "AVCC" and adc["23"] == "Vdrive"
    assert adc["42"] == "REFIN/REFOUT" and adc["64"] == "V8GND"
