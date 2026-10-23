#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_exe="${PYTHON:-python3}"
if ! command -v "$python_exe" >/dev/null 2>&1; then
    printf 'Python 3.10+ is required. Install Python, then rerun bash setup.sh.\n' >&2
    exit 1
fi
exec "$python_exe" "$project_root/tools/install.py" "$@"
