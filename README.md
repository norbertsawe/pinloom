# Pinloom

Look up electronic component pinouts from your terminal, even offline.
Includes **2,088 components and 39,934 pins**, with diagrams, electrical notes and
alternate functions for common microcontrollers, boards, ICs and connectors.

Supports **Python 3.10+** on Windows 10/11, Linux and macOS.

![Pinloom terminal view with package sketch, contrasting headings and pin grid](docs/preview.svg)

```text
NE555 (PDIP-8) [ne555]
Supply: 4.5-16 V

PACKAGE APPEARANCE
       .----------------.
      /                /|
     +----------------+ |
  ===|                | |===
  ===|       IC       | |===
  ===|                | /===
     +----------------+/
Illustrative silhouette; not a footprint or wiring reference.

PINOUT
            +-------+
  [GND] GND | 1   8 | [PWR] VCC
 [ANA] TRIG | 2   7 | [CTL] DISCH
   [IO] OUT | 3   6 | [ANA] THRES
 [CTL] /RST | 4   5 | [ANA] CONT
            +-------+

KEY DETAILS
Power pins: VCC (8)
Ground pins: GND (1)
Note: Decouple the supply close to the IC. RESET is active low.
```

## Installation

Clone the repository:

```sh
git clone https://github.com/norbertsawe/pinloom.git
cd pinloom
```

**Linux / macOS**

```sh
bash setup.sh
./.venv/bin/pinloom pico -d
```
Adding it  to path(i.e if you are using zsh)
```
echo 'export PATH="$PATH:'"$(pwd)/.venv/bin"'"' >> ~/.zshrc  
```

**Windows PowerShell**

```powershell
.\setup.ps1
.\.venv\Scripts\pinloom.exe pico -d
```

**Windows Command Prompt**

```bat
setup.cmd
.venv\Scripts\pinloom.exe pico -d
```

The scripts install into `.venv` without administrator privileges. Add `.venv/bin`
(Linux/macOS) or `.venv\Scripts` (Windows) to your PATH to use `pinloom` anywhere.
If PowerShell blocks the script, run `setup.cmd`. To choose a Windows interpreter,
use `.\setup.ps1 -PythonExe 'C:\Python312\python.exe'`.

Already using [pipx](https://pipx.pypa.io/)? Install from the checkout with
`pipx install ".[yaml]"`. For a manual installation, create a virtual environment
and run `python -m pip install ".[yaml]"`. Omit `[yaml]` for JSON-only support.

## Usage

```sh
pinloom pico                        # Show a pinout
pinloom "Arduino Uno" -d             # Include electrical notes and pin functions
pinloom --search esp32               # List matching components
pinloom -i esp32                     # Choose a component interactively
pinloom 555                         # Look up an alias
pinloom pico --pin SPI -d            # Filter by pin function
pinloom atmega328p --pin 17 -d       # Inspect a physical pin
pinloom --categories                # See categories and component counts
pinloom --list --category sensors --limit 20
pinloom --search mcp --limit 10
pinloom --list --offset 20 --limit 20 # Browse the next page
pinloom --list                      # List the catalog
pinloom --update                    # Update the cached database
pinloom --help                      # Show all options
```

Names and aliases ignore case and punctuation. Partial or misspelled names open
an interactive finder in a terminal: choose a number, enter a new search, or press
`q` to cancel. Scripts and redirected output never prompt; ambiguous queries
return suggestions. Use `--no-interactive` to disable prompts explicitly.

Package silhouettes appear above the pinout for recognized IC, transistor,
board and connector packages. They are simplified illustrations, with no physical
pin assignments; use the pin grid and datasheet for wiring. Unknown packages or
very narrow windows omit the picture. `--no-art` hides pictures explicitly.

Bold headings, supply highlighting and semantic pin colors make key information
easier to scan. Power and ground connections, electrical characteristics and
existing connection restrictions appear below the grid. `-d` adds every pin's
functions and notes. No electrical limits are guessed for imported components.

Diagrams label power, ground, I/O, analog, interface, control and unused pins.
Narrow terminals show a complete vertical list. Use `--ascii` for ASCII borders,
`--width 40` to override terminal sizing, or `--no-color` for plain output.
`NO_COLOR` is supported, and piped output is plain by default. Run a query again
after resizing to reflow its output.

## Exports and custom pinouts

```sh
pinloom pico --export pico.json
pinloom ne555 --export timer.yaml
pinloom uno --export uno.csv
pinloom esp32s3 -d --export esp32.md
pinloom pico --format json
pinloom --validate examples/custom.json
pinloom --custom examples/custom.yaml my-sensor -d
```

Exports support **text, JSON, YAML, CSV and Markdown**. The file extension selects
the format; `--format` overrides it. JSON/YAML exports can be loaded as custom
components. `--pin` can also limit an export to selected pins.

Place JSON/YAML definitions in your config directory's `components` subdirectory
for automatic loading. Run `pinloom --about` to see your paths, or use
`--config-dir` and `--data-dir` to override them.

| Platform | Config | Cache |
| --- | --- | --- |
| Windows | `%APPDATA%\pinloom` | `%LOCALAPPDATA%\pinloom` |
| Linux | `~/.config/pinloom` | `~/.local/share/pinloom` |
| macOS | `~/Library/Application Support/pinloom` | Config directory's `data` subdirectory |

Linux also respects `XDG_CONFIG_HOME` and `XDG_DATA_HOME`. All platforms support
`PINLOOM_CONFIG_DIR` and `PINLOOM_DATA_DIR`. See the [database guide](docs/database.md)
for the schema, examples, loading precedence and update behavior.

## Component database

The original 88 entries come from [pinout-pages](https://github.com/norbertsawe/pinout-pages)
and work immediately offline. An additional 2,000 package-specific entries are
adapted from a pinned KiCad symbol library snapshot (2020), bringing the bundled
catalog to 2,088 components. All entries work offline. `--update` refreshes a
separate cache while keeping custom definitions intact.

Coverage includes Arduino Uno/Nano, ATmega328P, ESP32/S3/C3, ESP8266, Blue Pill,
NUCLEO-F401RE, Pico/RP2040, 555 timers, 74HC logic, LM358/NE5532 amplifiers,
MCP23017, PCM5102A, ADCs/DACs, USB connectors, Raspberry Pi GPIO and SWD/JTAG/ICSP.
Browse the [original catalog](https://github.com/norbertsawe/pinout-pages/blob/main/CATALOG.md)
for the original packages and source references. Use `pinloom --categories` or
`pinloom --list --format json` for the complete installed catalog.

Text listings show descriptions, categories, pin counts and packages, with a
20-result default in terminals. Pipes and JSON retain the full list unless
`--limit` is supplied. Combine `--category`, `--search`, `--limit` and `--offset`
to browse. The interactive finder supports `n`/`p` for next/previous pages.

Imported entries preserve symbol pin labels and electrical types, with physical
pad numbers shown in logical tables. They do not include independently verified
supply ratings or every multiplexed function. `pinloom COMPONENT -d` shows the
source links and import notes. See [catalog provenance](docs/catalog-provenance.md)
for reproduction instructions and data licensing.

Each entry identifies its package or board revision and pin orientation.
Other packages and clone boards may differ; use the linked reference for design
limits and footprint dimensions.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, packaging and database
updates. CI runs checks on Windows, Linux and macOS with Python 3.10, 3.12 and 3.14.

## Upgrading from pinout-cli

Version 3 renames the distribution, Python module and command to `pinloom`. Install
from this checkout with `python -m pip install ".[yaml]"` or rerun your platform's
setup script. Update shell aliases and scripts to call `pinloom` or
`python -m pinloom`. The old `pinout` executable is not installed by this project.
If your environment still has this project's old distribution, remove it with
`python -m pip uninstall pinout-cli` after installing Pinloom.

New configuration and cache folders use `pinloom`; `PINLOOM_CONFIG_DIR` and
`PINLOOM_DATA_DIR` are the preferred overrides. Existing `pinout` folders remain
readable until a new folder exists, and `PINOUT_CONFIG_DIR` / `PINOUT_DATA_DIR`
remain accepted for migration. New environment variables take precedence. No
files are moved or deleted automatically. `pinloom --about` shows the active paths.
The separately maintained `pinout-pages` database keeps its existing URL.
