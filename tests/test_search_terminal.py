import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from pinout_cli import paths, terminal
from pinout_cli.search import choose, search


def test_fuzzy_and_partial_search(db):
    assert search(db, "atmeg328p")[0].id == "atmega328p"
    matches = search(db, "esp32")
    assert matches[0].id == "esp32"
    assert {c.id for c in matches} == {"esp32", "esp32s3", "esp32c3"}
    assert search(db, "555")[0].id == "ne555"
    assert search(db, "zxqzzqzxqz") == []


def test_interactive_refinement_selection_and_cancellation(db, monkeypatch):
    answers = iter(["pico", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert choose(db, "esp32", io.StringIO()).id == "pico"
    monkeypatch.setattr("builtins.input", lambda _: "q")
    assert choose(db, "esp32", io.StringIO()) is None

    def eof(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert choose(db, "esp32", io.StringIO()) is None


class Stream(io.StringIO):
    def isatty(self):
        return True


def test_color_negotiation_and_encoding(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    assert terminal.color_enabled("auto", Stream())
    assert not terminal.color_enabled("auto", io.StringIO())
    monkeypatch.setenv("NO_COLOR", "")
    assert not terminal.color_enabled("auto", Stream())
    assert terminal.color_enabled("always", Stream())
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("TERM", "dumb")
    assert not terminal.color_enabled("auto", Stream())
    assert not terminal.unicode_enabled(io.StringIO())

    class UTF8Stream(Stream):
        encoding = "utf-8"

    assert terminal.unicode_enabled(UTF8Stream())


def test_width_is_refreshed_after_resize(monkeypatch):
    monkeypatch.setattr(terminal.shutil, "get_terminal_size", lambda _: os.terminal_size((40, 20)))
    assert terminal.width() == 40
    monkeypatch.setattr(terminal.shutil, "get_terminal_size", lambda _: os.terminal_size((120, 20)))
    assert terminal.width() == 120
    assert terminal.width(55) == 55


@pytest.mark.parametrize("platform", ["windows", "linux", "macos"])
def test_platform_config_locations(monkeypatch, tmp_path, platform):
    for name in ("PINOUT_CONFIG_DIR", "PINOUT_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    # Patch only inside the calls: changing os.name globally breaks pathlib on Windows.
    with (
        patch.object(paths.os, "name", "nt" if platform == "windows" else "posix"),
        patch.object(paths.sys, "platform", "darwin" if platform == "macos" else "linux"),
    ):
        with patch.object(paths, "Path", type(tmp_path)):
            config, data = paths.config_dir(), paths.data_dir()
    if platform == "windows":
        assert config == tmp_path / "roaming/pinout"
        assert data == tmp_path / "local/pinout"
    elif platform == "linux":
        assert config == tmp_path / "xdg-config/pinout"
        assert data == tmp_path / "xdg-data/pinout"
    else:
        assert config == Path.home() / "Library/Application Support/pinout"
        assert data == config / "data"


def test_environment_location_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("PINOUT_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("PINOUT_DATA_DIR", str(tmp_path / "data"))
    assert paths.config_dir() == tmp_path / "config"
    assert paths.data_dir() == tmp_path / "data"
