# Expanded catalog provenance

The original 88 hand-curated records are preserved. The 2,000 added records in
`pinout_cli/data/kicad_*.json` are adapted from the KiCad community symbol library,
revision `4e17d7595f9691d45d97aea8ad64572652fb5bed` (2020-10-02):
https://github.com/KiCad/kicad-symbols/tree/4e17d7595f9691d45d97aea8ad64572652fb5bed

This is a historical, reproducible snapshot, not the latest KiCad library.
Each record links its manufacturer datasheet and exact upstream library file.
Only concrete base symbols with an assigned footprint, datasheet URL, description
and non-conflicting numbered pins are selected. Symbols with unnamed connected
terminals are excluded. Symbol aliases and wildcard part
names are excluded. Existing normalized IDs and aliases retain priority.
Round-robin selection across families prevents MCU variants dominating the catalog.

The importer combines all symbol units and common pins, skips duplicate De Morgan
body styles, sorts physical pad numbers, retains signal labels and marks electrical
types in descriptions. Unnamed pins are labeled `Unnamed`. KiCad `~` notation is
preserved (active-low/overbar markers). Pin kinds are conservative display groups,
not a statement of voltage tolerance. Every package uses a logical table; no
footprint orientation or physical pin positions are inferred from schematic
symbol coordinates. Supply limits and multiplexing tables require the datasheet.
These records have not each been independently checked against the datasheets.

## Reproduce

```sh
git clone https://github.com/KiCad/kicad-symbols.git /tmp/kicad-symbols
git -C /tmp/kicad-symbols checkout 4e17d7595f9691d45d97aea8ad64572652fb5bed
python tools/import_kicad.py /tmp/kicad-symbols
pinout --validate pinout_cli/data
```

The script refuses another revision and validates the combined catalog before
writing. It can be rerun without changing the generated files. No KiCad software
or network access is required for ordinary CLI use.

## Attribution and license

Copyright KiCad library contributors. The imported catalog files are adaptations
of the KiCad symbol library and are distributed under **CC BY-SA 4.0 with the
KiCad exception**, separately from the application's MIT-licensed code. Changes
include selection, JSON conversion, combining symbol units, label formatting,
pin classification, and descriptions. Retain this attribution when redistributing
the imported collection.

See [upstream license and exception](licenses/KiCad-LICENSE.md) and the
[CC BY-SA 4.0 legal text](licenses/CC-BY-SA-4.0.txt).

The original catalog is maintained by pinout-pages; this supplemental import is
maintained here. Syncing the original catalog preserves the imported files.
Remote updates merge with the bundled catalog and do not remove the additions.
