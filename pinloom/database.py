"""Offline-first loading, explicit remote updates, and validated user overrides."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from .models import Component, DefinitionError, normalize

MAX_FILE_BYTES = 32 * 1024 * 1024


def decode(text: str, suffix: str = ".json") -> dict[str, Component]:
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise DefinitionError(f"duplicate mapping key: {k}")
            result[k] = v
        return result

    try:
        if suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise DefinitionError('YAML requires pip install "pinloom[yaml]"') from exc

            class UniqueLoader(yaml.SafeLoader):
                pass

            def mapping(loader, node):
                loader.flatten_mapping(node)
                return unique(loader.construct_pairs(node, deep=True))

            UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
            raw: Any = yaml.load(text, Loader=UniqueLoader)
        else:
            raw = json.loads(text, object_pairs_hook=unique)
        if not isinstance(raw, dict) or not raw:
            raise DefinitionError(
                "file must contain a nonempty mapping of component IDs to definitions"
            )
        return {k: Component.parse(k, v) for k, v in raw.items()}
    except DefinitionError:
        raise
    except (ValueError, TypeError, RecursionError) as exc:
        raise DefinitionError(str(exc)) from exc
    except Exception as exc:
        if exc.__class__.__module__.startswith("yaml"):
            raise DefinitionError(str(exc)) from exc
        raise


def read_file(path: Path) -> dict[str, Component]:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise DefinitionError(f"{path}: exceeds {MAX_FILE_BYTES} bytes")
    return decode(path.read_text(encoding="utf-8-sig"), path.suffix)


def definition_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            raise DefinitionError(f"{path}: expected JSON or YAML")
        return [path]
    if not path.exists():
        return []
    return sorted(
        p for p in path.iterdir() if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml"}
    )


class Database:
    def __init__(self):
        self.components: dict[str, Component] = {}
        self.warnings: list[str] = []
        self.index: dict[str, str] = {}

    def merge(self, definitions: dict[str, Component], *, remote: bool = False):
        for key, component in definitions.items():
            if (
                remote
                and key in self.components
                and self.components[key].pins
                and not component.pins
            ):
                continue
            self.components[key] = component

    def reindex(self):
        self.index = {}
        for key in self.components:
            token = normalize(key)
            if token in self.index and self.index[token] != key:
                raise DefinitionError(f"ambiguous normalized IDs: {key} and {self.index[token]}")
            self.index[token] = key
        for key, component in self.components.items():
            for alias in component.aliases:
                token = normalize(alias)
                if not token:
                    raise DefinitionError(f"{key}: empty normalized alias")
                if token in self.index and self.index[token] != key:
                    raise DefinitionError(
                        f"ambiguous alias {alias!r}: {key} and {self.index[token]}"
                    )
                self.index[token] = key

    def exact(self, query: str) -> Component | None:
        key = self.index.get(normalize(query))
        return self.components.get(key) if key else None

    @classmethod
    def bundled(cls) -> Database:
        db = cls()
        for entry in sorted(resources.files("pinloom.data").iterdir(), key=lambda p: p.name):
            if entry.name.endswith(".json"):
                db.merge(decode(entry.read_text(encoding="utf-8")))
        db.reindex()
        return db

    @classmethod
    def load(cls, data: Path, config: Path, custom: list[Path] | None = None) -> Database:
        db = cls.bundled()
        cached = (
            [data / "database.json"]
            if (data / "database.json").exists()
            else definition_files(data / "database")
        )
        for path in cached:
            previous = dict(db.components)
            try:
                db.merge(read_file(path), remote=True)
                db.reindex()
            except (OSError, UnicodeError, DefinitionError) as exc:
                db.components = previous
                db.warnings.append(f"Ignoring invalid cache {path}: {exc}")
        for path in definition_files(config / "components"):
            try:
                db.merge(read_file(path))
            except (OSError, UnicodeError, DefinitionError) as exc:
                db.warnings.append(f"Ignoring invalid custom definition {path}: {exc}")
        for path in custom or []:
            if not path.exists():
                raise DefinitionError(f"custom path does not exist: {path}")
            files = definition_files(path)
            if not files:
                raise DefinitionError(f"no component definitions found: {path}")
            for file in files:
                db.merge(read_file(file))
        db.reindex()
        return db
