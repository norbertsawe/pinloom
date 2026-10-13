"""Versioned component definitions. Pin numbers include header IDs."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


class DefinitionError(ValueError):
    """A database definition cannot be used safely."""


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def clean(value: str) -> str:
    value = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", value)
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)
    return "".join(c for c in value if c in "\n\t" or (c.isprintable() and c != "\x1b"))


def string(value: Any, label: str, required: bool = False) -> str:
    if not isinstance(value, str) or (required and not value.strip()):
        raise DefinitionError(f"{label} must be {'a nonempty' if required else 'a'} string")
    result = clean(value).strip()
    if required and not result:
        raise DefinitionError(f"{label} must contain printable text")
    return result


def strings(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise DefinitionError(f"{label} must be a list of strings")
    return tuple(string(v, label, True) for v in value)


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    kind: str
    description: str
    functions: tuple[str, ...] = ()
    voltage: str = ""
    notes: tuple[str, ...] = ()

    @classmethod
    def parse(cls, raw: Any) -> Pin:
        if not isinstance(raw, dict):
            raise DefinitionError("each pin must be an object")
        kind = raw.get("kind", "digital")
        if not isinstance(kind, str) or kind not in {
            "power",
            "ground",
            "digital",
            "analog",
            "communication",
            "control",
            "nc",
        }:
            raise DefinitionError(f"unknown pin kind: {kind!r}")
        number = raw.get("number")
        if isinstance(number, int) and not isinstance(number, bool):
            number = str(number)
        return cls(
            string(number, "pin.number", True),
            string(raw.get("name"), "pin.name", True),
            kind,
            string(raw.get("description"), "pin.description", True),
            strings(raw.get("functions", []), "pin.functions"),
            string(raw.get("voltage", ""), "pin.voltage"),
            strings(raw.get("notes", []), "pin.notes"),
        )


@dataclass(frozen=True)
class Component:
    id: str
    name: str
    description: str
    category: str = "legacy"
    package: str = "Unspecified"
    aliases: tuple[str, ...] = ()
    voltage: str = "See manufacturer documentation"
    electrical: dict[str, str] = field(default_factory=dict)
    notes: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    pins: tuple[Pin, ...] = ()
    layout: dict[str, Any] = field(default_factory=lambda: {"type": "table"})
    ascii_art: str = ""

    @classmethod
    def parse(cls, key: str, raw: Any) -> Component:
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key):
            raise DefinitionError(f"invalid component ID: {key!r}")
        if not isinstance(raw, dict):
            raise DefinitionError(f"{key}: definition must be an object")
        version = raw.get("schema_version", 1)
        if type(version) is not int or version not in (1, 2):
            raise DefinitionError(f"{key}: unsupported schema_version")
        pin_data = raw.get("pins", [])
        if not isinstance(pin_data, list):
            raise DefinitionError(f"{key}: pins must be a list")
        pins = tuple(Pin.parse(p) for p in pin_data)
        numbers = [p.number for p in pins]
        if len(numbers) != len(set(numbers)):
            raise DefinitionError(f"{key}: duplicate pin numbers")
        art = string(raw.get("ascii_art", ""), "ascii_art")
        if not pins and not art:
            raise DefinitionError(f"{key}: provide pins or legacy ascii_art")
        if raw.get("schema_version") == 2 and not pins:
            raise DefinitionError(f"{key}: version 2 requires structured pins")
        layout = raw.get("layout", {"type": "table"})
        if (
            not isinstance(layout, dict)
            or not isinstance(layout.get("type"), str)
            or layout.get("type")
            not in {
                "dip",
                "dual",
                "header",
                "table",
            }
        ):
            raise DefinitionError(f"{key}: invalid layout type")
        layout = dict(layout)
        if "orientation" in layout:
            layout["orientation"] = string(layout["orientation"], "layout.orientation", True)
        if layout["type"] == "dip" and (len(pins) % 2 or not pins):
            raise DefinitionError(f"{key}: DIP layout requires an even pin count")
        if layout["type"] in {"dual", "header"}:
            rows = layout.get("rows")
            if not isinstance(rows, list) or not rows:
                raise DefinitionError(f"{key}: layout.rows must contain pairs of pin numbers")
            used = []
            for row in rows:
                if not isinstance(row, list) or len(row) != 2:
                    raise DefinitionError(f"{key}: each layout row must be a pair")
                for n in row:
                    if n is not None:
                        if not isinstance(n, str) or n not in numbers:
                            raise DefinitionError(f"{key}: unknown layout pin {n!r}")
                        used.append(n)
            if sorted(used) != sorted(numbers):
                raise DefinitionError(f"{key}: layout must include every pin exactly once")
        electrical = raw.get("electrical", {})
        if not isinstance(electrical, dict):
            raise DefinitionError(f"{key}: electrical must be an object")
        electrical = {
            string(k, "electrical key", True): string(v, "electrical value", True)
            for k, v in electrical.items()
        }
        return cls(
            key,
            string(raw.get("name"), "name", True),
            string(raw.get("description"), "description", True),
            string(raw.get("category", "legacy"), "category", True),
            string(raw.get("package", "Unspecified"), "package", True),
            strings(raw.get("aliases", []), "aliases"),
            string(raw.get("voltage", "See manufacturer documentation"), "voltage", True),
            electrical,
            strings(raw.get("notes", []), "notes"),
            strings(raw.get("sources", []), "sources"),
            pins,
            layout,
            art,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("id")
        data["schema_version"] = 2 if self.pins else 1
        for key in ("aliases", "notes", "sources"):
            data[key] = list(data[key])
        data["pins"] = list(data["pins"])
        for pin in data["pins"]:
            pin["functions"] = list(pin["functions"])
            pin["notes"] = list(pin["notes"])
        if not data["ascii_art"]:
            data.pop("ascii_art")
        return data
