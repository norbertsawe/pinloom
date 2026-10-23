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

You need **Python 3.10 or newer**, Git, and internet access for installation.
Pinout lookups work offline afterward. Install Python from
[python.org](https://www.python.org/downloads/) if it is missing. On Debian/Ubuntu,
`sudo apt install python3-venv` fixes missing `venv`/`ensurepip` support.

Clone the repository once:

```sh
git clone https://github.com/norbertsawe/pinloom.git
cd pinloom
```

On Windows, use PowerShell or Command Prompt for setup. WSL uses the Linux
instructions inside WSL. Choose the commands for your terminal below. Setup installs Pinloom in a private
user environment, exposes only the `pinloom` command, and **adds it to PATH
automatically for future terminals**. No administrator access or environment
activation is needed. The extra PATH command in each block makes it available
immediately in the terminal you are using now.

### Linux and macOS — bash or zsh

```sh
bash setup.sh
export PATH="$HOME/.local/bin:$PATH"
pinloom --version
pinloom ne555
```

Setup configures bash, zsh, POSIX login profiles and fish. It respects `ZDOTDIR`
and `XDG_CONFIG_HOME`. Rerunning it replaces its own marked PATH block without
duplicating entries or replacing your other settings.

To choose a Python interpreter: `PYTHON=python3.12 bash setup.sh`.

### Linux and macOS — fish

```fish
bash setup.sh
fish_add_path "$HOME/.local/bin"
pinloom --version
pinloom ne555
```

### Windows — PowerShell

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
$env:Path = "$env:LOCALAPPDATA\Pinloom\bin;$env:Path"
pinloom --version
pinloom ne555
```

This bypass applies only to the setup process; it does not change your saved
execution policy. Setup adds the command directory to your **user PATH** while
preserving existing entries. It does not use `setx` or change the machine PATH.
To choose Python, add `-PythonExe 'C:\Python312\python.exe'` to the setup command.

### Windows — Command Prompt (cmd.exe)

```bat
setup.cmd
pinloom --version
pinloom ne555
```

`setup.cmd` also refreshes PATH in the current Command Prompt. If you run it from
another batch file, use `call setup.cmd` so the calling script continues afterward.

### Installation locations

| System | Private Python environment | Command directory added to PATH |
| --- | --- | --- |
| Linux | `~/.local/share/pinloom/venv` | `~/.local/bin` |
| macOS | `~/Library/Application Support/pinloom/venv` | `~/.local/bin` |
| Windows | `%LOCALAPPDATA%\Pinloom\venv` | `%LOCALAPPDATA%\Pinloom\bin` |

Linux respects `XDG_DATA_HOME` for the private environment. The installed command
keeps working if you move or remove the checkout; do not move the private
virtual environment itself. To update, pull the repository changes and rerun setup.

### If the command is still not found

First check that setup finished successfully. Open a new terminal; on Windows,
fully close and reopen Windows Terminal or VS Code if a new tab still inherits
an old PATH. You can instead refresh the current terminal with the appropriate
command below:

| Terminal | Make Pinloom available now | Check the resolved command |
| --- | --- | --- |
| bash / zsh | `export PATH="$HOME/.local/bin:$PATH"` | `command -v pinloom` |
| fish | `fish_add_path "$HOME/.local/bin"` | `type -p pinloom` |
| PowerShell | `$env:Path = "$env:LOCALAPPDATA\Pinloom\bin;$env:Path"` | `Get-Command pinloom` |
| Command Prompt | `set "PATH=%LOCALAPPDATA%\Pinloom\bin;%PATH%"` | `where pinloom` |

To repair persistent PATH entries without downloading or reinstalling:

```sh
# Linux / macOS, from the checkout
python3 tools/install.py --path-only
```

```powershell
# Windows, from the checkout
py -3 tools\install.py --path-only
```

If you prefer to manage PATH yourself, use `bash setup.sh --no-path` or
`.\setup.ps1 -NoPath`. Advanced installs can use `python3 tools/install.py --help`
(`py -3 tools\install.py --help` on Windows) to choose installation directories
or omit optional YAML support.

Already using [pipx](https://pipx.pypa.io/)? From the checkout, run
`pipx install ".[yaml]"`, then `pipx ensurepath`, and open a new terminal.
This is an alternative to the setup scripts; you only need one installation method.

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

Version 3 renames the distribution, Python module and command to `pinloom`.
Use the setup instructions above to install into a private user environment.
Update shell aliases and scripts to call `pinloom`. The old `pinout` executable
is not installed by this project. If you still have this project's old
`pinout-cli` distribution, uninstall it using its original environment's Python
after installing Pinloom: `python -m pip uninstall pinout-cli`.

New configuration and cache folders use `pinloom`; `PINLOOM_CONFIG_DIR` and
`PINLOOM_DATA_DIR` are the preferred overrides. Existing `pinout` folders remain
readable until a new folder exists, and `PINOUT_CONFIG_DIR` / `PINOUT_DATA_DIR`
remain accepted for migration. New environment variables take precedence. No
files are moved or deleted automatically. `pinloom --about` shows the active paths.
The separately maintained `pinout-pages` database keeps its existing URL.
