#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_exe="${PYTHON:-python3}"
"$python_exe" -m venv "$project_root/.venv"
"$project_root/.venv/bin/python" -m pip install "$project_root[yaml]"
"$project_root/.venv/bin/pinloom" --version
printf 'Installed: %s/.venv/bin/pinloom\n' "$project_root"
printf 'Run: "%s/.venv/bin/pinloom" pico -d\n' "$project_root"
printf 'Add %s/.venv/bin to your PATH to run pinloom anywhere.\n' "$project_root"
