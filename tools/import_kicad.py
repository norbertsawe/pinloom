"""Reproduce 2,000 package-specific entries from the pinned KiCad legacy library.

Usage: python tools/import_kicad.py /path/to/kicad-symbols
Only concrete base symbols with footprints and datasheet links are eligible.
Library aliases and wildcard part numbers are deliberately excluded.
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pinloom.database import Database, decode  # noqa: E402
from pinloom.models import normalize  # noqa: E402

REVISION = "4e17d7595f9691d45d97aea8ad64572652fb5bed"
SOURCE = f"https://github.com/KiCad/kicad-symbols/blob/{REVISION}"
GROUPS = {
    "amplifiers": ("Amplifier_",),
    "data-converters": ("Analog_ADC", "Analog_DAC"),
    "analog-ics": ("Analog.lib", "Analog_Switch", "Reference_"),
    "logic": ("74xx.lib", "74xGxx.lib", "4xxx.lib"),
    "interfaces": ("Interface",),
    "drivers": ("Driver_",),
    "memory": ("Memory_",),
    "regulators": ("Regulator_",),
    "sensors": ("Sensor",),
    "timers": ("Timer",),
    "isolators": ("Isolator",),
    "transistors": ("Transistor_",),
    "microcontrollers": ("MCU_",),
}
TYPES = {
    "I": "Input",
    "O": "Output",
    "B": "Bidirectional",
    "T": "Three-state output",
    "P": "Passive terminal",
    "U": "Unspecified electrical type",
    "W": "Power input",
    "w": "Power output",
    "C": "Open-collector output",
    "E": "Open-emitter output",
    "N": "Not connected",
}


def documentation(path):
    records, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("$CMP "):
            current = {}
            records[line[5:]] = current
        elif current is not None and line[:2] in {"D ", "F "}:
            current[line[0]] = line[2:]
    return records


def symbols(path):
    """Read legacy DEF/F2/X fields; combine all units, using normal body style."""
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DEF "):
            current = {"name": line.split()[1], "footprint": "", "pins": {}}
        elif current is not None and line.startswith("F2 "):
            current["footprint"] = shlex.split(line)[1]
        elif current is not None and line.startswith("X "):
            fields = line.split()
            if int(fields[10]) not in (0, 1):  # De Morgan bodies duplicate physical pins.
                continue
            name, number, electrical = fields[1], fields[2], fields[11]
            # '~' is the legacy empty-name marker; retain useful unnamed terminals.
            name = "Unnamed" if name == "~" else name
            pin = (name, electrical)
            previous = current["pins"].get(number)
            if previous is not None and previous != pin:
                current["conflict"] = True
            current["pins"][number] = pin
        elif current is not None and line == "ENDDEF":
            yield current
            current = None


def pin_record(number, name, electrical, group):
    if electrical == "N":
        kind = "nc"
    elif electrical in {"W", "w"}:
        kind = (
            "ground"
            if re.fullmatch(r"(?:[ADP]?GND|VSS|VSSA|VSSD|VSSIO)", name.upper())
            else "power"
        )
    elif group in {"amplifiers", "data-converters", "analog-ics", "transistors"}:
        kind = "analog"
    else:
        kind = "digital"
    return {
        "number": number,
        "name": name,
        "kind": kind,
        "description": f"{TYPES[electrical]}; symbol signal {name}. See datasheet for limits and configuration.",
        "functions": [name],
    }


def build(source, existing):
    candidates = defaultdict(list)
    seen = set(existing.index)
    for path in sorted(source.glob("*.lib")):
        group = next((g for g, prefixes in GROUPS.items() if path.name.startswith(prefixes)), None)
        if group is None:
            continue
        docs = documentation(path.with_suffix(".dcm"))
        for symbol in symbols(path):
            name, footprint = symbol["name"], symbol["footprint"]
            doc = docs.get(name, {})
            url = doc.get("F", "")
            # x placeholders denote families rather than exact orderable devices.
            if (
                not footprint
                or any(c in name for c in "~*?x")
                or symbol.get("conflict")
                or not url.startswith(("http://", "https://"))
                or not doc.get("D")
            ):
                continue
            key = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if not key or normalize(key) in seen:
                continue
            raw_pins = symbol["pins"]
            if (
                not raw_pins
                or any(t not in TYPES for _, t in raw_pins.values())
                or any(n == "Unnamed" and t != "N" for n, t in raw_pins.values())
            ):
                continue
            pins = [
                pin_record(n, *raw_pins[n], group)
                for n in sorted(raw_pins, key=lambda n: (0, int(n)) if n.isdigit() else (1, n))
            ]
            package = footprint.split(":", 1)[-1]
            candidates[group].append(
                (
                    key,
                    {
                        "schema_version": 2,
                        "name": f"{name} ({package})",
                        "description": doc["D"],
                        "category": group,
                        "package": package,
                        "voltage": "See manufacturer datasheet for operating supply and signal limits",
                        "pins": pins,
                        "layout": {
                            "type": "table",
                            "orientation": "Physical pad numbers from the named package; logical table, not a footprint view. "
                            "Use the datasheet package drawing to locate pin 1 and determine viewing direction.",
                        },
                        "sources": [url, f"{SOURCE}/{path.name}"],
                        "notes": [
                            f"Adapted from KiCad symbol {path.stem}:{name}, revision {REVISION}; CC BY-SA 4.0 with KiCad exception.",
                            "Pin names and electrical types are transcribed from the symbol. Multiplexed functions, "
                            "supply ranges and absolute maximum ratings have not been independently transcribed.",
                            "KiCad ~ markers indicate active-low/overbar notation; see the source symbol and datasheet.",
                        ],
                    },
                )
            )
            seen.add(normalize(key))
    selected = defaultdict(dict)
    # Round-robin across families, so MCU variants cannot dominate the expansion.
    count = 0
    while count < 2000:
        before = count
        for group in sorted(candidates):
            if candidates[group] and count < 2000:
                key, record = candidates[group].pop(0)
                selected[group][key] = record
                count += 1
        if before == count:
            raise ValueError(f"only {count} eligible components")
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != REVISION:
        parser.error(f"expected source revision {REVISION}, got {revision}")
    baseline = Database.bundled()
    baseline.components = {
        k: c
        for k, c in baseline.components.items()
        if not any("Adapted from KiCad symbol" in n for n in c.notes)
    }
    baseline.reindex()
    groups = build(args.source, baseline)
    for records in groups.values():
        baseline.merge(decode(json.dumps(records)))
    baseline.reindex()
    for group, records in groups.items():
        target = ROOT / "pinloom/data" / f"kicad_{group}.json"
        target.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"{group}: {len(records)}")
    print(
        f"Total: {len(baseline.components)} components, "
        f"{sum(len(c.pins) for c in baseline.components.values()):,} pins"
    )


if __name__ == "__main__":
    main()
