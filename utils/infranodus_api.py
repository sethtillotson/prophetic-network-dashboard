"""
InfraNodus Direct API Client
Docs: https://support.noduslabs.com/hc/en-us/articles/13605983537692
"""
import requests
from typing import Optional, Dict, Any, List


class InfraNodusAPI:
    BASE_URL = "https://infranodus.com/api/v1"

    def __init__(self, api_key: str, timeout: int = 30):
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

    def _post(self, path: str, payload: Dict[str, Any], params: Optional[Dict] = None) -> Dict:
        url = f"{self.BASE_URL}{path}"
        try:
            r = self.session.post(url, json=payload, params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            body = e.response.text[:500] if e.response is not None else ""
            raise Exception(f"InfraNodus API error {e.response.status_code}: {body}")
        except requests.Timeout:
            raise Exception(f"InfraNodus API timeout after {self.timeout}s")
        except requests.RequestException as e:
            raise Exception(f"InfraNodus API connection error: {e}")

    def list_graphs(self, limit: int = 50) -> List[Dict]:
        """List all graphs for the authenticated user."""
        result = self._post("/listGraphs", payload={"limit": limit})
        # Response is typically {"graphs": [...]} or a list directly
        if isinstance(result, dict):
            return result.get("graphs") or result.get("data") or [result]
        return result if isinstance(result, list) else []

    def get_graph(
        self,
        name: str,
        include_graph: bool = True,
        include_statements: bool = True,
        include_stats: bool = True,
    ) -> Dict:
        """Retrieve an existing graph by name, including nodes, edges, and statements."""
        payload = {"name": name}
        params = {
            "includeGraph": str(include_graph).lower(),
            "includeStatements": str(include_statements).lower(),
            "includeGraphSummary": str(include_stats).lower(),
        }
        return self._post("/graphAndStatements", payload=payload, params=params)
