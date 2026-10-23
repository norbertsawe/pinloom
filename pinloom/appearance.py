"""Offline terminal silhouettes, inferred only from explicit package families.

These drawings illustrate package appearance. They never assign pin numbers or
claim to be a footprint drawing; the separate catalog pin map remains authoritative.
"""

import re

from .models import Component


def package_family(component: Component) -> str | None:
    package = component.package.upper()
    if component.category == "boards" or "BOARD HEADERS" in package or "UNO R3 HEADERS" in package:
        return "board"
    if "RECEPTACLE" in package and "USB" in component.name.upper():
        return "usb"
    if re.search(r"(?:^|_)(?:X?F?BGA|WLCSP|CSP)[-_]", package):
        return "ball-grid"
    if re.search(r"(?:^|_)(?:[A-Z]*QFN|[A-Z]*DFN|[A-Z]*LGA|WSON|[A-Z]*LFCSP)[-_]", package):
        return "leadless"
    if re.search(r"(?:^|_)(?:[A-Z]*QFP|PLCC)[-_]", package):
        return "quad"
    if re.search(r"(?:^|_)(?:P?DIP|SOIC|[A-Z]*SSOP|[A-Z]*SOP|SO|MSOP|TSOP)[-_]", package):
        return "dual"
    if re.search(r"(?:^|_)TO-?(?:220|247)(?:[-_]|$)", package):
        return "tabbed"
    if re.search(r"(?:^|_)(?:T?SOT)-?223(?:[-_]|$)", package):
        return "tabbed-smd"
    if re.search(r"(?:^|_)TO-?92(?:[-_]|$)", package):
        return "round-transistor"
    if re.search(r"(?:^|_)(?:T?SOT)-?23(?:[-_]|$)", package):
        return "small-smd"
    if component.layout["type"] == "header":
        return "header"
    return None


ART = {
    "dual": [
        "       .----------------.",
        "      /                /|",
        "     +----------------+ |",
        "  ===|                | |===",
        "  ===|       IC       | |===",
        "  ===|                | /===",
        "     +----------------+/",
    ],
    "quad": [
        "        | | | | |",
        "     +--+-+-+-+-+--+",
        "  ---|             |---",
        "  ---|     IC      |---",
        "  ---|             |---",
        "     +--+-+-+-+-+--+",
        "        | | | | |",
    ],
    "leadless": [
        "       .------------.",
        "      /            /|",
        "     +------------+ |",
        "     |     IC     | |",
        "     |            | /",
        "     +------------+/",
        "       pads underneath",
    ],
    "ball-grid": [
        "     +---------------+",
        "     | o o o o o o o |",
        "     | o o o o o o o |",
        "     | o o o o o o o |",
        "     | o o o o o o o |",
        "     +---------------+",
        "       underside balls",
    ],
    "tabbed": [
        "        +---------+",
        "        |    O    |",
        "        +---------+",
        "        |         |",
        "        |         |",
        "        +---------+",
        "          |  |  |",
        "          |  |  |",
    ],
    "tabbed-smd": [
        "           +-----+",
        "           | tab |",
        "        +--+-----+--+",
        "        |           |",
        "        +-----------+",
        "          |   |   |",
    ],
    "round-transistor": [
        "          .-------.",
        "        /           \\",
        "        |           |",
        "        +-----------+",
        "          |   |   |",
        "          |   |   |",
    ],
    "small-smd": [
        "           |     |",
        "        +-----------+",
        "        |           |",
        "        +-----------+",
        "              |",
    ],
    "board": [
        "     +---------------------+",
        "     | o                 o |",
        "     | o    +-------+    o |",
        "     | o    |  MCU  |    o |",
        "     | o    +-------+    o |",
        "     | o                 o |",
        "     +---------------------+",
    ],
    "usb": [
        "      .----------------.",
        "     /                /|",
        "    +----------------+ |",
        "    |   ----------   | /",
        "    +----------------+/",
    ],
    "header": [
        "       +-----------+",
        "       | o o o o o |",
        "       | o o o o o |",
        "       +-----------+",
    ],
}


def appearance(component: Component, width: int = 80) -> list[str]:
    family = package_family(component)
    if family is None:
        return []
    lines = ART[family]
    # Skip rather than break a silhouette when the terminal is too narrow.
    if max(map(len, lines)) > width:
        return []
    return lines.copy()
