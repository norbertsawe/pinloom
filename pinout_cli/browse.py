"""Compact, width-aware catalog views."""

from collections import Counter

from .render import wrapped


def catalog_view(components, *, total, offset=0, width=80, color=False):
    width = max(12, width)
    heading = (
        f"Components {offset + 1}-{offset + len(components)} of {total}"
        if components
        else "No components found"
    )
    lines = wrapped(heading, width)
    lines.append("-" * min(width, 64))
    for component in components:
        title = component.id
        lines += [f"\x1b[1;36m{line}\x1b[0m" if color else line for line in wrapped(title, width)]
        lines += ["  " + line for line in wrapped(component.description, width - 2)]
        lines += [
            "  " + line
            for line in wrapped(
                f"{component.category} | {len(component.pins)} pins | {component.package}",
                width - 2,
            )
        ]
        lines.append("")
    if offset + len(components) < total:
        lines += wrapped(
            f"Next: --list --offset {offset + len(components)} --limit {len(components)} (keep your search/category filters)",
            width,
        )
    lines += wrapped("Browse: --categories | --category NAME | --search QUERY", width)
    lines += wrapped("Inspect: pinout COMPONENT -d | pinout COMPONENT --pin NUMBER", width)
    return "\n".join(lines) + "\n"


def category_view(components, width=80):
    counts = Counter(c.category for c in components)
    lines = wrapped(
        f"Catalog: {sum(counts.values()):,} components in {len(counts)} categories", width
    )
    lines.append("-" * min(width, 64))
    for category, count in sorted(counts.items()):
        lines += wrapped(f"{category:24} {count:5,}", width)
    lines += [""] + wrapped("Browse a category: pinout --list --category sensors --limit 20", width)
    return "\n".join(lines) + "\n"
