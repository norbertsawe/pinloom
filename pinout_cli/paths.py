"""Platform-native locations without creating directories during lookups."""

import os
import sys
from pathlib import Path


def config_dir() -> Path:
    if os.environ.get("PINOUT_CONFIG_DIR"):
        return Path(os.environ["PINOUT_CONFIG_DIR"]).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "pinout"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "pinout"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pinout"


def data_dir() -> Path:
    if os.environ.get("PINOUT_DATA_DIR"):
        return Path(os.environ["PINOUT_DATA_DIR"]).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "pinout"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "pinout" / "data"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "pinout"
