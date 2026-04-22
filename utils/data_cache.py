"""
Lightweight disk-backed cache for InfraNodus JSON exports.

Primary role in the hybrid architecture: load the pre-exported
`data/layer_1.json` file so the dashboard renders instantly without any
API round-trip. Secondary role: persist optional API responses so the
dashboard degrades gracefully if InfraNodus is unreachable.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class DataCache:
    """Disk-backed JSON cache keyed by graph name."""

    def __init__(self, cache_dir: Path | str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────
    #  Direct file I/O
    # ──────────────────────────────────────────────────────────────────────
    def load_json(self, relative_path: str) -> Dict[str, Any]:
        """Load a JSON file by path (relative to project root or absolute)."""
        path = Path(relative_path)
        if not path.is_absolute() and not path.exists():
            path = self.cache_dir.parent / relative_path
        if not path.exists():
            # one more fallback: inside the cache dir itself
            path = self.cache_dir / Path(relative_path).name
        if not path.exists():
            raise FileNotFoundError(f"JSON not found: {relative_path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, name: str, data: Dict[str, Any]) -> Path:
        """Persist a JSON payload under the cache directory."""
        path = self.cache_dir / f"{name}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    # ──────────────────────────────────────────────────────────────────────
    #  Introspection
    # ──────────────────────────────────────────────────────────────────────
    def exists(self, name: str) -> bool:
        return (self.cache_dir / f"{name}.json").exists()

    def age_seconds(self, name: str) -> Optional[float]:
        p = self.cache_dir / f"{name}.json"
        if not p.exists():
            return None
        return (datetime.utcnow().timestamp() - p.stat().st_mtime)

    def list_cached(self) -> list[str]:
        return sorted(p.stem for p in self.cache_dir.glob("*.json"))
