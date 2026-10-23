"""Verify a built wheel from a fresh environment outside the source tree."""

import json
import os
import subprocess
import tempfile
import venv
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheel = sorted((root / "dist").glob("pinloom-*.whl"))[-1]
with zipfile.ZipFile(wheel) as archive:
    assert not any(n.startswith("pinout_cli/") for n in archive.namelist())
    entry_points = next(n for n in archive.namelist() if n.endswith("/entry_points.txt"))
    commands = archive.read(entry_points).decode()
    assert "pinloom = pinloom.cli:main" in commands
    assert "pinout =" not in commands

with tempfile.TemporaryDirectory(prefix="pinloom-wheel-") as temporary:
    directory = Path(temporary)
    venv.create(directory / "env", with_pip=True)
    python = directory / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, cwd=directory)
    result = subprocess.run(
        [
            str(python),
            "-m",
            "pinloom",
            "--list",
            "--format",
            "json",
            "--config-dir",
            str(directory / "config"),
            "--data-dir",
            str(directory / "data"),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=directory,
    )
    components = json.loads(result.stdout)
    assert len(components) >= 2088, len(components)
    subprocess.run(
        [str(python), "-m", "pinloom", "pico", "--details", "--ascii"],
        check=True,
        cwd=directory,
        stdout=subprocess.DEVNULL,
    )
    command = directory / "env" / ("Scripts/pinloom.exe" if os.name == "nt" else "bin/pinloom")
    version = subprocess.run(
        [str(command), "--version"], check=True, capture_output=True, text=True, cwd=directory
    )
    expected_version = wheel.name.split("-")[1]
    assert f"Pinloom {expected_version}" in version.stdout
    preview = subprocess.run(
        [
            str(command),
            "ne555",
            "--color",
            "always",
            "--ascii",
            "--config-dir",
            str(directory / "config"),
            "--data-dir",
            str(directory / "data"),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=directory,
    )
    assert "PACKAGE APPEARANCE" in preview.stdout
    assert "Power pins: VCC (8)" in preview.stdout
    assert "\x1b[1;33mSupply:" in preview.stdout
    print(f"Wheel smoke test passed: {len(components)} offline components")
