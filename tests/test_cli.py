import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def invoke(tmp_path, *args):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pinloom",
            *args,
            "--data-dir",
            str(tmp_path / "cache"),
            "--config-dir",
            str(tmp_path / "config"),
        ],
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=15,
    )


def test_details_cli_and_pipes_are_plain(tmp_path):
    result = invoke(tmp_path, "pico", "-d", "--pin", "24", "--ascii")
    assert result.returncode == 0 and not result.stderr
    assert "SPI0 SCK" in result.stdout
    assert "\x1b" not in result.stdout
    assert "Pin 25" not in result.stdout


def test_search_json_and_unknown_exit_codes(tmp_path):
    result = invoke(tmp_path, "--search", "esp32", "--format", "json")
    assert result.returncode == 0
    assert {c["id"] for c in json.loads(result.stdout)} >= {"esp32", "esp32s3", "esp32c3"}
    result = invoke(tmp_path, "zxqzzqzxqz")
    assert result.returncode == 1 and "No exact component" in result.stderr
    result = invoke(tmp_path, "--interactive")
    assert result.returncode == 2 and "requires terminal" in result.stderr


@pytest.mark.parametrize("filename", ["pico.json", "pico.yaml", "pico.csv", "pico.md", "pico.txt"])
def test_export_paths_with_spaces(tmp_path, filename):
    target = tmp_path / "directory with spaces" / filename
    result = invoke(tmp_path, "pico", "--export", str(target))
    assert result.returncode == 0 and not result.stdout
    assert target.exists() and "\x1b" not in target.read_text(encoding="utf-8")
    if target.suffix in {".json", ".yaml"}:
        reloaded = invoke(tmp_path, "pico", "--custom", str(target), "--format", "json")
        assert reloaded.returncode == 0 and len(json.loads(reloaded.stdout)["pico"]["pins"]) == 40


@pytest.mark.parametrize(
    "args",
    [
        ("pico", "--pin", "missing"),
        ("pico", "--width", "1"),
        ("--details",),
        ("pico", "--pin", "---"),
    ],
)
def test_invalid_arguments_exit_two(tmp_path, args):
    result = invoke(tmp_path, *args)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_cli_validation_and_json_custom(tmp_path):
    result = invoke(tmp_path, "--validate", str(ROOT / "examples/custom.yaml"))
    assert result.returncode == 0 and "Valid: 1" in result.stdout
    result = invoke(
        tmp_path, "lab-sensor", "--custom", str(ROOT / "examples/custom.json"), "--details"
    )
    assert result.returncode == 0 and "Pull up to 3.3 V" in result.stdout


def test_noninteractive_no_args_lists_without_cache(tmp_path):
    result = invoke(tmp_path)
    assert result.returncode == 0 and "atmega328p" in result.stdout
    assert not (tmp_path / "cache").exists()


def test_categories_filter_and_pagination(tmp_path):
    result = invoke(tmp_path, "--categories", "--format", "json")
    categories = json.loads(result.stdout)
    assert result.returncode == 0 and sum(categories.values()) == 2088
    assert categories["sensors"] == 193
    first = invoke(tmp_path, "--list", "--category", "sensors", "--limit", "2", "--format", "json")
    second = invoke(
        tmp_path,
        "--list",
        "--category",
        "sensors",
        "--limit",
        "2",
        "--offset",
        "2",
        "--format",
        "json",
    )
    a, b = json.loads(first.stdout), json.loads(second.stdout)
    assert len(a) == len(b) == 2
    assert not ({c["id"] for c in a} & {c["id"] for c in b})
    text = invoke(tmp_path, "--list", "--category", "sensors", "--limit", "2", "--width", "40")
    assert "of 193" in text.stdout
    assert max(map(len, text.stdout.splitlines())) <= 40
    assert "\x1b" not in text.stdout


@pytest.mark.parametrize("args", [("--limit", "0"), ("--offset", "-1"), ("--category", "missing")])
def test_browse_rejects_bad_filters(tmp_path, args):
    result = invoke(tmp_path, *args)
    assert result.returncode == 2 and "Traceback" not in result.stderr


def test_picture_controls_and_contrast(tmp_path):
    text = invoke(tmp_path, "ne555", "--color", "always")
    assert text.returncode == 0 and "\x1b[1;33mSupply:" in text.stdout
    assert "PACKAGE APPEARANCE" in text.stdout
    plain = invoke(tmp_path, "ne555", "--no-color", "--no-art")
    assert plain.returncode == 0 and "\x1b" not in plain.stdout
    assert "PACKAGE APPEARANCE" not in plain.stdout
    assert "Power pins: VCC (8)" in plain.stdout
