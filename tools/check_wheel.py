"""Verify a built wheel from a fresh environment outside the source tree."""

import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheel = sorted((root / "dist").glob("pinout_cli-*.whl"))[-1]
with tempfile.TemporaryDirectory(prefix="pinout-wheel-") as temporary:
    directory = Path(temporary)
    venv.create(directory / "env", with_pip=True)
    python = directory / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, cwd=directory)
    result = subprocess.run(
        [
            str(python),
            "-m",
            "pinout_cli",
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
        [str(python), "-m", "pinout_cli", "pico", "--details", "--ascii"],
        check=True,
        cwd=directory,
        stdout=subprocess.DEVNULL,
    )
    print(f"Wheel smoke test passed: {len(components)} offline components")
