"""Portable text, round-trip definitions and tabular export."""

import csv
import io
import json
import os
import tempfile
from pathlib import Path

from .models import Component, DefinitionError
from .render import render

FORMATS = ("text", "json", "yaml", "csv", "markdown")


def serialize(component: Component, format: str, *, details=False, width=80, pins=None) -> str:
    data = {component.id: component.to_dict()}
    if pins is not None:
        # Selected pins have no complete footprint, so use a table on reload.
        numbers = {p.number for p in pins}
        data[component.id]["pins"] = [
            p for p in data[component.id]["pins"] if p["number"] in numbers
        ]
        data[component.id]["layout"] = {"type": "table", "orientation": "Selected pins only."}
        data[component.id].pop("ascii_art", None)
    if format == "json":
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if format == "yaml":
        try:
            import yaml
        except ImportError as exc:
            raise DefinitionError('YAML requires pip install "pinout-cli[yaml]"') from exc
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    if format == "text":
        return render(component, details=details, width=width, pins=pins)
    selected = component.pins if pins is None else pins
    if format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["number", "name", "kind", "description", "functions", "voltage", "notes"])
        for pin in selected:
            writer.writerow(
                [
                    pin.number,
                    pin.name,
                    pin.kind,
                    pin.description,
                    "; ".join(pin.functions),
                    pin.voltage,
                    "; ".join(pin.notes),
                ]
            )
        return output.getvalue()
    if format == "markdown":

        def cell(s):
            return s.replace("|", "\\|").replace("\n", "<br>")

        lines = [
            f"# {component.name}",
            "",
            component.description,
            "",
            f"Package: {component.package}. Supply: {component.voltage}.",
            "",
            "| Pin | Name | Kind | Functions | Voltage | Description |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for pin in selected:
            lines.append(
                "| "
                + " | ".join(
                    cell(v)
                    for v in (
                        pin.number,
                        pin.name,
                        pin.kind,
                        ", ".join(pin.functions),
                        pin.voltage,
                        pin.description,
                    )
                )
                + " |"
            )
        if details:
            lines += ["", "```text", render(component, details=True, width=width, pins=pins), "```"]
        return "\n".join(lines) + "\n"
    raise DefinitionError(f"unknown format: {format}")


def atomic_write(path: Path, text: str):
    """Replace one file only after a complete UTF-8 write; retain old data on failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".pinout-",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
