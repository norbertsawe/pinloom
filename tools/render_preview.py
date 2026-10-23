"""Render the real ANSI terminal output as a reproducible README SVG, without dependencies."""

import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pinloom.database import Database  # noqa: E402
from pinloom.render import render  # noqa: E402

COLORS = {
    "31": "#ff7b72",
    "32": "#7ee787",
    "33": "#e3b341",
    "35": "#d2a8ff",
    "36": "#79c0ff",
    "39": "#e6edf3",
    "90": "#8b949e",
}


def main():
    text = render(Database.bundled().exact("ne555"), color=True, unicode=False, width=80)
    lines = ["$ pinloom ne555"] + text.splitlines()
    plain = re.sub(r"\x1b\[[0-9;]+m", "", "\n".join(lines))
    width = int(max(map(len, plain.splitlines())) * 8.5 + 48)
    height = len(lines) * 20 + 76
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Pinloom terminal component view</title>',
        '<desc id="desc">NE555 with a package silhouette, pinout grid, supply, power and ground connections, and electrical notes.</desc>',
        f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117"/>',
        f'<path d="M12 0H{width - 12}Q{width} 0 {width} 12V40H0V12Q0 0 12 0" fill="#161b22"/>',
        '<circle cx="20" cy="20" r="5" fill="#ff7b72"/><circle cx="38" cy="20" r="5" fill="#e3b341"/><circle cx="56" cy="20" r="5" fill="#7ee787"/>',
        '<g font-family="DejaVu Sans Mono,Consolas,monospace" font-size="14" xml:space="preserve">',
        '<text x="80" y="25" fill="#e6edf3">Pinloom / offline hardware reference</text>',
    ]
    foreground, bold = COLORS["39"], False
    for row, line in enumerate(lines):
        svg.append(f'<text x="24" y="{68 + row * 20}">')
        for part in re.split(r"(\x1b\[[0-9;]+m)", line):
            if part.startswith("\x1b["):
                for code in part[2:-1].split(";"):
                    if code == "0":
                        foreground, bold = COLORS["39"], False
                    elif code == "1":
                        bold = True
                    elif code in COLORS:
                        foreground = COLORS[code]
            elif part:
                svg.append(
                    f'<tspan fill="{foreground}" font-weight="{700 if bold else 400}">{escape(part)}</tspan>'
                )
        svg.append("</text>")
    svg += ["</g>", "</svg>"]
    (ROOT / "docs/preview.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
