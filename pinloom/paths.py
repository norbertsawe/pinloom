"""Platform-native locations, retaining access to configurations from before the rename."""

import os
import sys
from pathlib import Path


def preferred(primary: Path, legacy: Path) -> Path:
    """Read the old location only until a new location exists; never create either."""
    return legacy if not primary.exists() and legacy.exists() else primary


def override(suffix: str) -> Path | None:
    value = os.environ.get(f"PINLOOM_{suffix}") or os.environ.get(f"PINOUT_{suffix}")
    return Path(value).expanduser() if value else None


def config_dir() -> Path:
    explicit = override("CONFIG_DIR")
    if explicit is not None:
        return explicit
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return preferred(root / "pinloom", root / "pinout")


def data_dir() -> Path:
    explicit = override("DATA_DIR")
    if explicit is not None:
        return explicit
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
        return preferred(root / "pinloom" / "data", root / "pinout" / "data")
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return preferred(root / "pinloom", root / "pinout")
