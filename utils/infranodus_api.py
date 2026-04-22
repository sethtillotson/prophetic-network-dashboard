"""
InfraNodus API client — lean, stats-focused.

The hybrid dashboard renders the live graph via iframe, so this client only
needs to support:
    • list_graphs()            — sidebar diagnostics
    • get_graph_summary()      — fast stats refresh (no graph body, no statements)

Both are implemented as POST requests against the official v1 endpoints with
a 120-second timeout, retries, and robust error messages.

Reference:
    https://support.noduslabs.com/hc/en-us/articles/13605983537692
    https://infranodus.com/api/docs
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


class InfraNodusAPI:
    BASE_URL = "https://infranodus.com/api/v1"

    def __init__(self, api_key: str, timeout: int = 120):
        if not api_key:
            raise ValueError("InfraNodus API key is required.")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ProphetticNetworkDashboard/1.0",
        })

    # ──────────────────────────────────────────────────────────────────────
    #  low-level helper with retry + back-off
    # ──────────────────────────────────────────────────────────────────────
    def _post(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 2,
    ) -> Any:
        url = f"{self.BASE_URL}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                r = self.session.post(
                    url,
                    json=payload or {},
                    params=params or {},
                    timeout=self.timeout,
                )
                if r.status_code >= 400:
                    # surface the server message whenever possible
                    try:
                        body = r.json()
                    except ValueError:
                        body = r.text
                    raise RuntimeError(
                        f"InfraNodus API {r.status_code} on {path}: {body}"
                    )
                # 2xx
                if not r.content:
                    return None
                try:
                    return r.json()
                except ValueError:
                    return r.text
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                if attempt < retries:
                    time.sleep(2 ** attempt)  # 1s, 2s
                    continue
                raise RuntimeError(
                    f"InfraNodus API timeout on {path} after {retries + 1} attempts: {exc}"
                )
            except Exception as exc:
                last_exc = exc
                raise

        if last_exc:  # pragma: no cover
            raise last_exc

    # ──────────────────────────────────────────────────────────────────────
    #  Public methods
    # ──────────────────────────────────────────────────────────────────────
    def list_graphs(self, limit: int = 50) -> List[Dict[str, Any]] | Dict[str, Any]:
        """POST /listGraphs — retrieve the user's graphs."""
        data = self._post("/listGraphs", {"limit": limit})
        # some endpoints wrap the list inside {"graphs": [...]}
        if isinstance(data, dict) and "graphs" in data:
            return data["graphs"]
        return data

    def get_graph_summary(self, name: str) -> Dict[str, Any]:
        """POST /graphAndStatements with all heavy payloads disabled.

        Returns only the summary metadata (top nodes, clusters, gaps,
        modularity, diversity stats). Used for an *optional* live refresh —
        the cached JSON already contains all this information.
        """
        payload = {"name": name}
        params = {
            "includeGraph": "false",
            "includeStatements": "false",
            "includeGraphSummary": "true",
        }
        result = self._post("/graphAndStatements", payload, params, retries=2)
        if isinstance(result, dict):
            return result.get("graph") or result
        return {}

    def get_graph_full(self, name: str) -> Dict[str, Any]:
        """POST /graphAndStatements with the full graph body.

        Kept for parity with the old client. Prefer the cached JSON file —
        this call can exceed 60 seconds for Layer 1.
        """
        payload = {"name": name}
        params = {
            "includeGraph": "true",
            "includeStatements": "false",
            "includeGraphSummary": "true",
        }
        return self._post("/graphAndStatements", payload, params, retries=2) or {}
