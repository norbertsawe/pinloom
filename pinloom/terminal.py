"""Portable color negotiation, encoding fallback and current terminal dimensions."""

import os
import shutil
import sys


def initialize():
    if os.name == "nt":
        try:
            from colorama import just_fix_windows_console

            just_fix_windows_console()
        except ImportError:
            pass
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")


def width(override: int | None = None) -> int:
    return max(12, override if override is not None else shutil.get_terminal_size((80, 24)).columns)


def color_enabled(mode: str, stream) -> bool:
    if mode == "never":
        return False
    if mode == "always":
        return True
    return stream.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"


def unicode_enabled(stream) -> bool:
    try:
        "┌─┐│└┘".encode(stream.encoding or "ascii")
        return True
    except (UnicodeError, LookupError):
        return False
