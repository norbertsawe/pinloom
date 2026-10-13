"""Deterministic partial-name and typo search with no network calls."""

from difflib import SequenceMatcher

from .database import Database
from .models import Component, clean, normalize


def search(db: Database, query: str, limit: int | None = None) -> list[Component]:
    token = normalize(query)
    scored = []
    partial_ids = set()
    for component in db.components.values():
        terms = [normalize(t) for t in (component.id, component.name, *component.aliases)]
        if not token or any(token in term for term in terms):
            partial_ids.add(component.id)
        score = (
            max(
                1.0
                if token == t
                else 0.95
                if t.startswith(token)
                else 0.85
                if token in t
                else SequenceMatcher(None, token, t).ratio()
                for t in terms
            )
            if token
            else 1.0
        )
        if score >= 0.48:
            scored.append((score, component))
    if partial_ids:
        scored = [row for row in scored if row[1].id in partial_ids]
    scored.sort(key=lambda row: (-row[0], row[1].id))
    return [row[1] for row in scored[:limit]]


def choose(db: Database, query: str, output) -> Component | None:
    """Line-based fuzzy finder for cmd.exe, PowerShell and POSIX terminals."""
    while True:
        candidates = search(db, query, 20)
        output.write(f"\nMatches for {clean(query) or '(all components)'}:\n")
        for index, component in enumerate(candidates, 1):
            output.write(f"  {index:2}. {component.id} - {component.name}\n")
        output.flush()
        try:
            answer = input("Number, new search, or q to cancel: ").strip()
        except EOFError:
            return None
        if answer.casefold() in {"q", "quit", "exit"}:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            return candidates[int(answer) - 1]
        if answer:
            match = db.exact(answer)
            if match:
                return match
            query = answer
