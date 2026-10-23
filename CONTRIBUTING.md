# Contributing

Use Python 3.10 or newer. Install development dependencies in a virtual environment:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .\.venv\Scripts\Activate.ps1
# cmd.exe: .venv\Scripts\activate.bat
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
python tools/check_wheel.py
```

Keep parsing, database loading, terminal rendering and CLI handling in their own
modules. Regression tests should exercise observable behavior, especially package
orientation, pin functions, offline installation, custom input and failed updates.
The CI matrix runs these checks on Windows, Linux and macOS with Python 3.10/3.12/3.14.
An installed wheel must work outside the checkout, without a populated cache.

Catalog changes belong in `pinout-pages/database`; see [the data guide](docs/database.md).
Validate and sync them into this repository before building a release:

```sh
pinloom --validate ../pinout-pages/database
python tools/sync_database.py ../pinout-pages/database
```

Report hardware issues with the exact component, package, board revision and source
reference. Report terminal issues with OS, shell, terminal emulator, Python version,
encoding, terminal width and whether output was redirected.
