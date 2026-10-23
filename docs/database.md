# Component definitions

The authoritative catalog lives in [pinout-pages](https://github.com/norbertsawe/pinout-pages).
Its `database/*.json` files map stable component IDs to records. The CLI also
bundles 2,000 supplemental KiCad-derived entries; see [provenance](catalog-provenance.md).
The CLI packages a validated snapshot in `pinout_cli/data`, so fresh installations work offline.
Use `python tools/sync_database.py ../pinout-pages/database` to refresh that snapshot
after reviewing database changes. Ordinary lookup never accesses the network.

## Adding a component

Copy [the JSON example](../examples/custom.json) or [the YAML example](../examples/custom.yaml).
Use one record per exact package or board revision, with the manufacturer's pin
numbers and a clear orientation. Do not alias an IC package to a development board
with different pins. Describe pin functions, supply limits, signal voltage limits,
boot straps and reserved connections. Include the datasheet or schematic in `sources`.
Treat operating recommendations separately from absolute maximum ratings.

Run `pinout --validate path/to/file.json` before installing a custom definition.
Place it under the `components` subdirectory of the config location printed by
`pinout --about`, or use `pinout --custom path/to/file.json my-sensor -d`.
`--custom` accepts directories and can be repeated. UTF-8 (including an optional
BOM) is accepted. Files in a directory are loaded in filename order.
YAML requires the optional `yaml` extra. YAML uses a safe loader, and duplicate
mapping keys are rejected in both formats.

## Fields and diagrams

[component.schema.json](component.schema.json) documents the full v2 catalog format.
`pins` is an array of records with string `number`, `name`, semantic `kind`, and
`description`; optional fields are `functions`, `voltage`, and `notes`.
Integer pin numbers are accepted and converted to strings. Header IDs such as
`J1.4` and USB-C contacts such as `A5` remain strings.

Kinds are `power`, `ground`, `digital`, `analog`, `communication`, `control`, and `nc`.
A multiplexed GPIO has one display kind; all available functions belong in
`functions`. Functions may require configuration and cannot necessarily run
simultaneously. PWM/ADC/bus labels do not establish electrical tolerance.

Layouts:

- `dip`: ordered pins, first half down the left and second half up the right.
  Use top-view counterclockwise numbering for DIP, SOIC and similar two-sided ICs.
- `dual`: explicit `rows` of two pin numbers, in physical top-to-bottom order.
- `header`: explicit rows for odd/even or other connector numbering.
- `table`: logical pin map for packages or connector groups without a faithful
  two-column diagram. It must identify physical orientation in the accompanying text.

Each row can contain a `null` placeholder. Every defined pin must occur exactly
once in an explicit row layout. Narrow terminals use a complete stacked list,
without abbreviating pin names. A QFN table is not a package footprint diagram.

## Loading and compatibility

Precedence is bundled catalog, remote cache, config `components`, then explicit
`--custom` paths. A custom component with the same ID replaces the entire record;
use a new ID for a different package. Canonical IDs and aliases normalize punctuation
and case. Conflicting aliases are reported as errors rather than picking a device.
Invalid implicit config files/cache files generate warnings; an invalid explicit
custom file is an error.

Legacy `name`, `description`, `ascii_art` records still load. The renderer strips
embedded terminal controls and reports that detailed pins are unavailable. Old
remote records cannot replace a richer bundled definition. Catalog v2 records also
retain clean `ascii_art` for older pinout-cli versions; new versions render `pins`.

## Updating

`pinout --update` reads only the `database` files from the pinout-pages archive over
HTTPS. It bounds download/file/expanded sizes, rejects traversal paths, links,
invalid records, duplicate IDs and ambiguous aliases, and never extracts archive
paths. It validates the full snapshot before atomically replacing `database.json`.
On failure the previous cache remains intact and the command exits nonzero.
Updates modify the remote cache; custom definitions are kept in the config directory.

## Source notes

The original catalog has been migrated into structured records. IC package pin
facts were cross-checked with the KiCad 10 symbol library and manufacturer references;
board headers were checked against vendor pinout guides. `sources` links accompany
the records. Blue Pill and HC-SR04 entries describe specific common reference
layouts; clone boards can differ. GPIO multiplexing tables list commonly used
functions rather than every possible vendor peripheral mapping.

Useful primary references include [Pico documentation](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf),
[ESP32 DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html),
[ESP32-S3 v1.0](https://docs.espressif.com/projects/esp-idf/en/v4.4.3/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html),
[Arduino Uno](https://docs.arduino.cc/resources/pinouts/A000066-full-pinout.pdf),
[Nucleo MB1136](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf),
and [PCM5102A](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf).
