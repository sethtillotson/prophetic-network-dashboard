"""
InfraNodus Direct API Client
Docs: https://support.noduslabs.com/hc/en-us/articles/13605983537692
"""
import requests
import time
from typing import Optional, Dict, Any, List


class InfraNodusAPI:
    BASE_URL = "https://infranodus.com/api/v1"

    def __init__(self, api_key: str, timeout: int = 120):  # ← 120s default
        if not api_key:
            raise ValueError("InfraNodus API key is required")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _post(
        self,
        path: str,
        payload: Dict[str, Any],
        params: Optional[Dict] = None,
        retries: int = 2,
    ) -> Dict:
        """
        Internal POST with retry logic for large graph requests.
        
        Args:
            retries: Number of retry attempts on timeout (default 2)
        """
        url = f"{self.BASE_URL}{path}"
        last_error = None

        for attempt in range(retries + 1):
            try:
                r = self.session.post(
                    url,
                    json=payload,
                    params=params,
                    timeout=self.timeout
                )
                r.raise_for_status()
                return r.json()

            except requests.Timeout as e:
                last_error = e
                if attempt < retries:
                    wait = 2 ** attempt  # Exponential backoff: 1s, 2s
                    time.sleep(wait)
                    continue
                else:
                    raise Exception(
                        f"InfraNodus API timeout after {self.timeout}s "
                        f"(tried {retries + 1} times). "
                        f"Graph may be too large or server is slow."
                    )

            except requests.HTTPError as e:
                body = e.response.text[:500] if e.response is not None else ""
                raise Exception(
                    f"InfraNodus API error {e.response.status_code}: {body}"
                )

            except requests.RequestException as e:
                raise Exception(f"InfraNodus API connection error: {e}")

        # Should never reach here, but satisfy type checker
        raise Exception(f"InfraNodus API failed after retries: {last_error}")

    def list_graphs(self, limit: int = 50) -> List[Dict]:
        """List all graphs for the authenticated user."""
        result = self._post("/listGraphs", payload={"limit": limit}, retries=1)
        if isinstance(result, dict):
            return result.get("graphs") or result.get("data") or [result]
        return result if isinstance(result, list) else []

    def get_graph(
        self,
        name: str,
        include_graph: bool = True,
        include_statements: bool = False,  # ← Set to False by default (faster)
        include_stats: bool = True,
    ) -> Dict:
        """
        Retrieve an existing graph by name.
        
        Args:
            name: Graph context name (e.g., 'layer_1', 'layer_3')
            include_graph: Include nodes/edges (required for visualization)
            include_statements: Include full text statements (SLOW — disable for speed)
            include_stats: Include summary statistics
        
        Returns:
            Dict with keys: graph, statements, summary
        """
        payload = {"name": name}
        params = {
            "includeGraph": str(include_graph).lower(),
            "includeStatements": str(include_statements).lower(),
            "includeGraphSummary": str(include_stats).lower(),
        }
        # Graph requests may timeout — allow 2 retries with 120s each
        return self._post("/graphAndStatements", payload=payload, params=params, retries=2)
