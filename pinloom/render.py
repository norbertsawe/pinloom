"""Width-aware diagrams with semantic labels that also work without color."""

from __future__ import annotations

import textwrap

from .appearance import appearance
from .models import Component, Pin

KINDS = {
    "power": ("PWR", "31"),
    "ground": ("GND", "39"),
    "digital": ("IO", "32"),
    "analog": ("ANA", "33"),
    "communication": ("BUS", "36"),
    "control": ("CTL", "35"),
    "nc": ("NC", "90"),
}


def wrapped(text: str, width: int) -> list[str]:
    result = []
    for line in text.splitlines() or [""]:
        result.extend(
            textwrap.wrap(line, width=width, break_long_words=True, break_on_hyphens=False) or [""]
        )
    return result


def paint(text: str, pin: Pin, color: bool) -> str:
    return f"\x1b[1m\x1b[{KINDS[pin.kind][1]}m{text}\x1b[0m" if color else text


def label(pin: Pin) -> str:
    return f"[{KINDS[pin.kind][0]}] {pin.name}"


def diagram(component: Component, width: int, color: bool, unicode: bool) -> list[str]:
    pins = component.pins
    if not pins:
        return wrapped(component.ascii_art, width)
    by_number = {p.number: p for p in pins}
    layout_type = component.layout["type"]
    if layout_type == "dip":
        half = len(pins) // 2
        rows = [(pins[i].number, pins[-i - 1].number) for i in range(half)]
    else:
        rows = component.layout.get("rows", [])
    nwidth = max(len(p.number) for p in pins)
    lwidth = max(len(label(p)) for p in pins)
    # Never truncate pin names. Narrow windows receive a complete vertical list.
    required = 2 * lwidth + 2 * nwidth + 11
    if not rows or required > width:
        lines = []
        for pin in pins:
            for line in wrapped(f"{pin.number:>{nwidth}} {label(pin)}", width):
                lines.append(paint(line, pin, color))
        return lines
    tl, tr, bl, br, h, v = (
        ("┌", "┐", "└", "┘", "─", "│") if unicode else ("+", "+", "+", "+", "-", "|")
    )
    interior = nwidth * 2 + 5
    lines = [" " * (lwidth + 1) + tl + h * interior + tr]
    for left, right in rows:
        lp = by_number[left] if left else None
        rp = by_number[right] if right else None
        ll = label(lp).rjust(lwidth) if lp else " " * lwidth
        rl = label(rp).ljust(lwidth) if rp else " " * lwidth
        lines.append(
            (paint(ll, lp, color) if lp else ll)
            + f" {v} {(left or ''):>{nwidth}}   {(right or ''):<{nwidth}} {v} "
            + (paint(rl, rp, color) if rp else rl)
        )
    lines.append(" " * (lwidth + 1) + bl + h * interior + br)
    return lines


def highlight(text: str, style: str, color: bool) -> str:
    return f"\x1b[{style}m{text}\x1b[0m" if color else text


def section(title: str, width: int, color: bool, unicode: bool) -> list[str]:
    return (
        [""]
        + [highlight(line, "1;36", color) for line in wrapped(title, width)]
        + [highlight(("─" if unicode else "-") * min(width, 48), "36", color)]
    )


def connections(pins: tuple[Pin, ...], kind: str) -> str:
    groups: dict[str, list[str]] = {}
    for pin in pins:
        if pin.kind == kind:
            groups.setdefault(pin.name, []).append(pin.number)
    return "; ".join(f"{name} ({', '.join(numbers)})" for name, numbers in groups.items())


def render(
    component: Component,
    *,
    width: int = 80,
    color: bool = False,
    unicode: bool = False,
    details: bool = False,
    pins: tuple[Pin, ...] | None = None,
    show_appearance: bool = True,
) -> str:
    width = max(12, width)
    selected = component.pins if pins is None else pins
    lines = [
        highlight(line, "1;36", color)
        for line in wrapped(f"{component.name} [{component.id}]", width)
    ]
    lines += wrapped(component.description, width)
    lines.append("")
    lines += wrapped(f"Package: {component.package}", width)
    lines += wrapped(f"Category: {component.category} | Pins: {len(component.pins)}", width)
    lines += [
        highlight(line, "1;33", color) for line in wrapped(f"Supply: {component.voltage}", width)
    ]
    sketch = appearance(component, width) if show_appearance else []
    if sketch:
        lines += section("PACKAGE APPEARANCE", width, color, unicode)
        lines += sketch
        lines += wrapped(
            "Illustrative silhouette; lead positions/count are simplified. "
            "Not to scale or a wiring reference.",
            width,
        )
    lines += section("PINOUT", width, color, unicode)
    lines += wrapped(
        component.layout.get(
            "orientation", "Pin map; see manufacturer drawing for physical orientation."
        ),
        width,
    )
    lines.append("")
    if pins is None:
        lines += diagram(component, width, color, unicode)
    else:
        lines += wrapped(f"Showing {len(selected)} of {len(component.pins)} pins", width)
        for pin in selected:
            lines += [
                paint(line, pin, color) for line in wrapped(f"{pin.number} {label(pin)}", width)
            ]
    lines.append("")
    lines += wrapped(
        "PWR power | GND ground | IO digital | ANA analog | BUS interface | CTL control | NC unused",
        width,
    )
    if component.pins:
        lines += section("KEY DETAILS", width, color, unicode)
        for kind, heading in (("power", "Power pins"), ("ground", "Ground pins")):
            summary = connections(selected, kind)
            if summary:
                lines += [
                    highlight(line, "1;31" if kind == "power" else "1", color)
                    for line in wrapped(f"{heading}: {summary}", width)
                ]
        for key, value in component.electrical.items():
            if key.casefold() == "supply" and value == component.voltage:
                continue
            lines += wrapped(f"{key}: {value}", width)
        imported = any("Adapted from KiCad symbol" in note for note in component.notes)
        notes = (
            component.notes
            if not imported or details
            else (
                "Imported symbol pin map; use the datasheet for electrical limits and alternate functions.",
            )
        )
        for note in notes:
            lines += [highlight(line, "1;33", color) for line in wrapped(f"Note: {note}", width)]
        # Surface existing connection restrictions without inventing hardware limits.
        if not details:
            for pin in selected:
                for note in pin.notes:
                    if any(
                        word in note.casefold()
                        for word in ("reserved", "do not", "input only", "input-only", "not 5 v")
                    ):
                        lines += [
                            highlight(line, "1;33", color)
                            for line in wrapped(f"Pin {pin.number}: {note}", width)
                        ]
    if details:
        lines += section("PIN FUNCTIONS & ELECTRICAL DETAILS", width, color, unicode)
        for pin in selected:
            lines.append("")
            lines += [
                paint(line, pin, color)
                for line in wrapped(
                    f"Pin {pin.number} - {pin.name} [{KINDS[pin.kind][0]}]: {pin.description}",
                    width,
                )
            ]
            if pin.functions:
                lines += wrapped(f"  Functions: {', '.join(pin.functions)}", width)
            if pin.voltage:
                lines += [
                    highlight(line, "1;33", color)
                    for line in wrapped(f"  Voltage: {pin.voltage}", width)
                ]
            for note in pin.notes:
                lines += wrapped(f"  Note: {note}", width)
        if not component.pins:
            lines += wrapped("This legacy definition has no structured pin details.", width)
    sources = component.sources if details else component.sources[:1]
    if sources:
        lines += section("REFERENCES", width, color, unicode)
        for source in sources:
            lines += wrapped(f"Source: {source}", width)
    if not details:
        lines.append("")
        lines += wrapped("Use -d for all pin functions, electrical notes and source links.", width)
    return "\n".join(lines).rstrip() + "\n"
