"""Profile loading and management."""

import json
from pathlib import Path


def load_profile(path: str | None) -> dict | None:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def save_profile(profile: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)
