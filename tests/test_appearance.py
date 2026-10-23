"""Illustrations must never claim unknown geometry or alter electrical data."""

from dataclasses import replace

import pytest

from pinloom.appearance import appearance, package_family
from pinloom.export import serialize
from pinloom.render import render


@pytest.mark.parametrize(
    "package,family",
    [
        ("PDIP-8", "dual"),
        ("SOIC-8_3.9x4.9mm_P1.27mm", "dual"),
        ("TSSOP-16", "dual"),
        ("LQFP-64", "quad"),
        ("QFN-32-1EP", "leadless"),
        ("Bosch_LGA-8_2.5x2.5mm", "leadless"),
        ("BGA-100", "ball-grid"),
        ("TO-220-3", "tabbed"),
        ("SOT-223", "tabbed-smd"),
        ("TO-92_Inline", "round-transistor"),
        ("SOT-23-5", "small-smd"),
        ("Unspecified custom package", None),
    ],
)
def test_only_explicit_known_packages_get_a_silhouette(db, package, family):
    component = replace(db.exact("ne555"), package=package)
    assert package_family(component) == family
    assert bool(appearance(component)) == (family is not None)


def test_package_sketch_comes_before_unchanged_pin_grid(db):
    component = db.exact("ne555")
    text = render(component, width=80)
    assert text.index("PACKAGE APPEARANCE") < text.index("PINOUT") < text.index("KEY DETAILS")
    assert "Illustrative silhouette" in text
    assert "Power pins: VCC (8)" in text
    assert "Ground pins: GND (1)" in text
    assert "Decouple the supply" in text
    assert "GND | 1   8 | [PWR] VCC" in text
    assert "PACKAGE APPEARANCE" not in render(component, show_appearance=False)
    assert "PACKAGE APPEARANCE" not in render(component, width=12)


def test_contrast_is_added_after_wrapping_and_exports_stay_plain(db):
    component = db.exact("ne555")
    color = render(component, color=True)
    assert "\x1b[1;36m" in color  # heading
    assert "\x1b[1;33mSupply:" in color
    assert "\x1b[39m" in color  # ground uses terminal's default foreground
    assert "\x1b" not in serialize(component, "text")
    assert "PACKAGE APPEARANCE" not in serialize(component, "text", show_appearance=False)
    assert serialize(component, "json", show_appearance=False) == serialize(component, "json")


def test_reserved_pin_notes_are_visible_without_details(db):
    text = render(db.exact("esp32"))
    assert "Reserved" in text
