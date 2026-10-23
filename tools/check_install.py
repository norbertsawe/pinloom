"""Exercise the user installer outside the checkout, with spaces in every path."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="pinloom installer ") as temporary:
        root = Path(temporary)
        source = root / "source with spaces"
        shutil.copytree(
            ROOT,
            source,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "__pycache__",
                "*.egg-info",
                "build",
                "dist",
                ".pytest_cache",
                ".ruff_cache",
            ),
        )
        binary_dir = root / "user commands"
        environment = root / "private environment"
        if os.name == "nt":
            args = [
                "-NoPath",
                "-NoYaml",
                "-PythonExe",
                sys.executable,
                "-InstallDir",
                str(environment),
                "-BinDir",
                str(binary_dir),
            ]
            subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(source / "setup.ps1"),
                    *args,
                ],
                check=True,
                cwd=root,
            )
            # Also exercise cmd.exe forwarding and an upgrade into an existing environment.
            # Quote every argument for cmd.exe (Windows filenames cannot contain ").
            batch = " ".join('"' + value + '"' for value in [str(source / "setup.cmd"), *args])
            subprocess.run("cmd.exe /d /c call " + batch, check=True, cwd=root)
        else:
            subprocess.run(
                [
                    "bash",
                    str(source / "setup.sh"),
                    "--no-path",
                    "--no-yaml",
                    "--install-dir",
                    str(environment),
                    "--bin-dir",
                    str(binary_dir),
                ],
                env={**os.environ, "PYTHON": sys.executable},
                check=True,
                cwd=root,
            )
        executable = binary_dir / ("pinloom.exe" if os.name == "nt" else "pinloom")
        env = {**os.environ, "PATH": str(binary_dir) + os.pathsep + os.environ.get("PATH", "")}
        assert shutil.which("pinloom", path=env["PATH"])
        result = subprocess.run(
            [
                str(executable),
                "--list",
                "--format",
                "json",
                "--config-dir",
                str(root / "config"),
                "--data-dir",
                str(root / "data"),
            ],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        assert len(json.loads(result.stdout)) >= 2088
        shells = (
            [
                ["cmd.exe", "/d", "/c", "pinloom --version"],
                ["powershell.exe", "-NoProfile", "-Command", "pinloom --version"],
            ]
            if os.name == "nt"
            else [["sh", "-c", "pinloom --version"]]
        )
        for shell in shells:
            result = subprocess.run(
                shell, cwd=root, env=env, check=True, capture_output=True, text=True
            )
            assert "Pinloom " in result.stdout
        # A relocated checkout must not break the installed command.
        shutil.rmtree(source)
        subprocess.run(
            [
                str(executable),
                "ne555",
                "--ascii",
                "--no-color",
                "--config-dir",
                str(root / "config"),
                "--data-dir",
                str(root / "data"),
            ],
            cwd=root,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        print(
            "Installer smoke test passed: spaces, shell discovery, offline catalog, removed checkout"
        )


if __name__ == "__main__":
    main()
