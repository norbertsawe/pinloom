# pinout-cli

Look up electronic component pinouts from your terminal, even offline.
Includes **88 components and 1,315 pins**, with diagrams, electrical notes and
alternate functions for common microcontrollers, boards, ICs and connectors.

Supports **Python 3.10+** on Windows 10/11, Linux and macOS.

```text
NE555 (PDIP-8)
            +-------+
  [GND] GND | 1   8 | [PWR] VCC
 [ANA] TRIG | 2   7 | [CTL] DISCH
   [IO] OUT | 3   6 | [ANA] THRES
 [CTL] /RST | 4   5 | [ANA] CONT
            +-------+
```

## Installation

Clone the repository:

```sh
git clone https://github.com/norbertsawe/pinout-cli.git
cd pinout-cli
```

**Linux / macOS**

```sh
bash setup.sh
./.venv/bin/pinout pico -d
echo 'export PATH="$PATH:'"$(pwd)/.venv/bin"'"' >> ~/.zshrc  
```

**Windows PowerShell**

```powershell
.\setup.ps1
.\.venv\Scripts\pinout.exe pico -d
```

**Windows Command Prompt**

```bat
setup.cmd
.venv\Scripts\pinout.exe pico -d
```

The scripts install into `.venv` without administrator privileges. Add `.venv/bin`
(Linux/macOS) or `.venv\Scripts` (Windows) to your PATH to use `pinout` anywhere.
If PowerShell blocks the script, run `setup.cmd`. To choose a Windows interpreter,
use `.\setup.ps1 -PythonExe 'C:\Python312\python.exe'`.

Already using [pipx](https://pipx.pypa.io/)? Install from the checkout with
`pipx install ".[yaml]"`. For a manual installation, create a virtual environment
and run `python -m pip install ".[yaml]"`. Omit `[yaml]` for JSON-only support.

## Usage

```sh
pinout pico                        # Show a pinout
pinout "Arduino Uno" -d             # Include electrical notes and pin functions
pinout --search esp32               # List matching components
pinout -i esp32                     # Choose a component interactively
pinout 555                         # Look up an alias
pinout pico --pin SPI -d            # Filter by pin function
pinout atmega328p --pin 17 -d       # Inspect a physical pin
pinout --list                      # List the catalog
pinout --update                    # Update the cached database
pinout --help                      # Show all options
```

Names and aliases ignore case and punctuation. Partial or misspelled names open
an interactive finder in a terminal: choose a number, enter a new search, or press
`q` to cancel. Scripts and redirected output never prompt; ambiguous queries
return suggestions. Use `--no-interactive` to disable prompts explicitly.

Diagrams label power, ground, I/O, analog, interface, control and unused pins.
Narrow terminals show a complete vertical list. Use `--ascii` for ASCII borders,
`--width 40` to override terminal sizing, or `--no-color` for plain output.
`NO_COLOR` is supported, and piped output is plain by default. Run a query again
after resizing to reflow its output.

## Exports and custom pinouts

```sh
pinout pico --export pico.json
pinout ne555 --export timer.yaml
pinout uno --export uno.csv
pinout esp32s3 -d --export esp32.md
pinout pico --format json
pinout --validate examples/custom.json
pinout --custom examples/custom.yaml my-sensor -d
```

Exports support **text, JSON, YAML, CSV and Markdown**. The file extension selects
the format; `--format` overrides it. JSON/YAML exports can be loaded as custom
components. `--pin` can also limit an export to selected pins.

Place JSON/YAML definitions in your config directory's `components` subdirectory
for automatic loading. Run `pinout --about` to see your paths, or use
`--config-dir` and `--data-dir` to override them.

| Platform | Config | Cache |
| --- | --- | --- |
| Windows | `%APPDATA%\pinout` | `%LOCALAPPDATA%\pinout` |
| Linux | `~/.config/pinout` | `~/.local/share/pinout` |
| macOS | `~/Library/Application Support/pinout` | Config directory's `data` subdirectory |

Linux also respects `XDG_CONFIG_HOME` and `XDG_DATA_HOME`. All platforms support
`PINOUT_CONFIG_DIR` and `PINOUT_DATA_DIR`. See the [database guide](docs/database.md)
for the schema, examples, loading precedence and update behavior.

## Component database

The bundled catalog comes from [pinout-pages](https://github.com/norbertsawe/pinout-pages)
and works immediately offline. `--update` refreshes a separate cache while keeping
custom definitions intact.

Coverage includes Arduino Uno/Nano, ATmega328P, ESP32/S3/C3, ESP8266, Blue Pill,
NUCLEO-F401RE, Pico/RP2040, 555 timers, 74HC logic, LM358/NE5532 amplifiers,
MCP23017, PCM5102A, ADCs/DACs, USB connectors, Raspberry Pi GPIO and SWD/JTAG/ICSP.
Browse the [complete catalog](https://github.com/norbertsawe/pinout-pages/blob/main/CATALOG.md)
for all supported packages and source references.

Each entry identifies its package or board revision and pin orientation.
Other packages and clone boards may differ; use the linked reference for design
limits and footprint dimensions.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, packaging and database
updates. CI runs checks on Windows, Linux and macOS with Python 3.10, 3.12 and 3.14.
