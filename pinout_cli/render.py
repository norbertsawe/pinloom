"""Width-aware diagrams with semantic labels that also work without color."""

from __future__ import annotations

import textwrap

from .models import Component, Pin

KINDS = {
    "power": ("PWR", "31"),
    "ground": ("GND", "90"),
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
    return f"\x1b[{KINDS[pin.kind][1]}m{text}\x1b[0m" if color else text


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


def render(
    component: Component,
    *,
    width: int = 80,
    color: bool = False,
    unicode: bool = False,
    details: bool = False,
    pins: tuple[Pin, ...] | None = None,
) -> str:
    width = max(12, width)
    lines = wrapped(f"{component.name} [{component.id}]", width)
    lines += wrapped(component.description, width)
    lines += wrapped(f"Package: {component.package} | Supply: {component.voltage}", width)
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
        for pin in pins:
            lines += [
                paint(line, pin, color) for line in wrapped(f"{pin.number} {label(pin)}", width)
            ]
    lines.append("")
    lines += wrapped(
        "PWR power | GND ground | IO digital | ANA analog | BUS interface | CTL control | NC unused",
        width,
    )
    if details:
        lines.append("")
        lines += wrapped("Electrical characteristics", width)
        for key, value in component.electrical.items():
            lines += wrapped(f"  {key}: {value}", width)
        for note in component.notes:
            lines += wrapped(f"Note: {note}", width)
        for pin in pins if pins is not None else component.pins:
            lines.append("")
            lines += wrapped(
                f"Pin {pin.number} - {pin.name} [{KINDS[pin.kind][0]}]: {pin.description}", width
            )
            if pin.functions:
                lines += wrapped(f"  Functions: {', '.join(pin.functions)}", width)
            if pin.voltage:
                lines += wrapped(f"  Voltage: {pin.voltage}", width)
            for note in pin.notes:
                lines += wrapped(f"  Note: {note}", width)
        if not component.pins:
            lines += wrapped("This legacy definition has no structured pin details.", width)
        for source in component.sources:
            lines += wrapped(f"Source: {source}", width)
    return "\n".join(lines).rstrip() + "\n"
