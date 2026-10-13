"""CLI orchestration. All network access is behind the explicit update option."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
import tarfile
import urllib.error
import zlib
from pathlib import Path

from . import __version__, paths, terminal
from .database import Database, definition_files, read_file
from .export import FORMATS, atomic_write, serialize
from .models import DefinitionError, clean, normalize
from .render import render
from .search import choose, search
from .update import update_database


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pinout", description="Offline electronic component pinouts with fuzzy search."
    )
    p.add_argument("component", nargs="?", help="component ID, alias or partial name")
    p.add_argument(
        "-d", "--details", action="store_true", help="electrical characteristics and pin functions"
    )
    p.add_argument(
        "--pin", action="append", default=[], help="pin number, name or function; repeatable"
    )
    modes = p.add_mutually_exclusive_group()
    modes.add_argument("-l", "--list", action="store_true", help="list components")
    modes.add_argument(
        "-s", "--search", nargs="?", const="", metavar="QUERY", help="list fuzzy matches"
    )
    modes.add_argument(
        "-i", "--interactive", action="store_true", help="open the interactive fuzzy finder"
    )
    modes.add_argument("-u", "--update", action="store_true", help="sync cache from pinout-pages")
    modes.add_argument(
        "--validate", type=Path, metavar="PATH", help="validate JSON/YAML file or directory"
    )
    modes.add_argument(
        "-a", "--about", action="store_true", help="version, database and config locations"
    )
    p.add_argument("--no-interactive", action="store_true", help="never prompt; useful in scripts")
    p.add_argument("--format", choices=FORMATS, default=None, help="output format (default text)")
    p.add_argument(
        "--export", type=Path, metavar="PATH", help="save UTF-8 output; infer format from extension"
    )
    p.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    p.add_argument("--no-color", dest="color", action="store_const", const="never")
    p.add_argument("--ascii", action="store_true", help="use ASCII instead of Unicode borders")
    p.add_argument("--width", type=int, help="override terminal width (12-1000 columns)")
    p.add_argument(
        "--config-dir", type=Path, help="directory containing components/ custom definitions"
    )
    p.add_argument("--data-dir", type=Path, help="remote cache directory")
    p.add_argument(
        "--custom",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="extra JSON/YAML file or directory",
    )
    p.add_argument("-V", "--version", action="version", version=f"pinout-cli {__version__}")
    return p


def run(argv=None) -> int:
    p = parser()
    args = p.parse_args(argv)
    if args.width is not None and not 12 <= args.width <= 1000:
        p.error("--width must be between 12 and 1000")
    config = (args.config_dir or paths.config_dir()).expanduser()
    data = (args.data_dir or paths.data_dir()).expanduser()
    if args.component in {"update", "about", "help"} and len(argv or sys.argv[1:]) == 1:
        if args.component == "help":
            p.print_help()
            return 0
        setattr(args, args.component, True)
        args.component = None
    if args.about:
        print(
            f"pinout-cli {__version__}\nOffline hardware pinout reference\nConfig: {config}\nCache: {data}\nDatabase: https://github.com/norbertsawe/pinout-pages"
        )
        return 0
    if args.update:
        count = update_database(data)
        print(f"Updated {count} component definitions in {data / 'database.json'}")
        return 0
    if args.validate:
        if not args.validate.exists():
            raise DefinitionError(f"path does not exist: {args.validate}")
        files = definition_files(args.validate)
        if not files:
            raise DefinitionError("no JSON/YAML definitions found")
        db = Database()
        for file in files:
            definitions = read_file(file)
            if db.components.keys() & definitions.keys():
                raise DefinitionError(f"{file}: duplicate component IDs across files")
            db.merge(definitions)
        db.reindex()
        print(f"Valid: {len(db.components)} components in {len(files)} files")
        return 0
    db = Database.load(data, config, [path.expanduser() for path in args.custom])
    for warning in db.warnings:
        print(f"Warning: {clean(warning)}", file=sys.stderr)
    query = args.component or ""
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not args.no_interactive
    if args.interactive and not interactive:
        raise DefinitionError("interactive search requires terminal input and output")
    if (
        args.list
        or args.search is not None
        or (not query and not interactive and not args.interactive)
    ):
        if args.pin or args.details:
            raise DefinitionError("--pin and --details require a selected component")
        found = search(db, args.search if args.search is not None else query)
        if args.export:
            raise DefinitionError("--export requires a selected component")
        if args.format == "json":
            print(
                json.dumps(
                    [{"id": c.id, "name": c.name, "package": c.package} for c in found], indent=2
                )
            )
        elif args.format not in {None, "text"}:
            raise DefinitionError("component lists support --format text or json")
        else:
            for component in found:
                print(f"{component.id:24} {component.name}")
        return 0 if found else 1
    component = None if args.interactive else db.exact(query)
    if component is None:
        if interactive:
            component = choose(db, query, sys.stdout)
            if component is None:
                return 0
        else:
            matches = search(db, query, 10)
            if len(matches) == 1 and normalize(query) in normalize(matches[0].id):
                component = matches[0]
            else:
                print(
                    f"No exact component match for {clean(query)!r}. Choose an ID:", file=sys.stderr
                )
                for match in matches:
                    print(f"  {match.id} - {match.name}", file=sys.stderr)
                return 1
    selected = None
    if args.pin:
        if any(not normalize(q) for q in args.pin):
            raise DefinitionError("--pin requires a pin number, name or function")
        selected = tuple(
            pin
            for pin in component.pins
            if any(
                normalize(q) == normalize(pin.number)
                or normalize(q) == normalize(pin.name)
                or any(normalize(q) in normalize(f) for f in pin.functions)
                for q in args.pin
            )
        )
        if not selected:
            raise DefinitionError(f"no pins match {args.pin!r} on {component.id}")
    width = terminal.width(args.width)
    format = args.format or (
        {".json": "json", ".yaml": "yaml", ".yml": "yaml", ".csv": "csv", ".md": "markdown"}.get(
            args.export.suffix.lower(), "text"
        )
        if args.export
        else "text"
    )
    if args.export or format != "text":
        output = serialize(component, format, details=args.details, width=width, pins=selected)
        if args.export:
            atomic_write(args.export.expanduser(), output)
            print(f"Exported {component.id} to {args.export}", file=sys.stderr)
        else:
            sys.stdout.write(output)
    else:
        sys.stdout.write(
            render(
                component,
                width=width,
                color=terminal.color_enabled(args.color, sys.stdout),
                unicode=not args.ascii and terminal.unicode_enabled(sys.stdout),
                details=args.details,
                pins=selected,
            )
        )
    return 0


def main(argv=None) -> int:
    terminal.initialize()
    try:
        return run(argv)
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        # Redirect stdout so interpreter shutdown does not flush the broken pipe again.
        import os

        sys.stdout = open(os.devnull, "w")
        return 0
    except (
        DefinitionError,
        OSError,
        UnicodeError,
        urllib.error.URLError,
        tarfile.TarError,
        http.client.HTTPException,
        EOFError,
        zlib.error,
    ) as exc:
        print(f"pinout: {clean(str(exc))}", file=sys.stderr)
        return 2
