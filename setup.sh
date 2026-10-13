#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_exe="${PYTHON:-python3}"
"$python_exe" -m venv "$project_root/.venv"
"$project_root/.venv/bin/python" -m pip install "$project_root[yaml]"
"$project_root/.venv/bin/pinout" --version
printf 'Installed: %s/.venv/bin/pinout\n' "$project_root"
printf 'Run: "%s/.venv/bin/pinout" pico -d\n' "$project_root"
printf 'Add %s/.venv/bin to your PATH to run pinout anywhere.\n' "$project_root"
