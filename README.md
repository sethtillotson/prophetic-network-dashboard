# 🕊️ Prophetic Network Dashboard — Hybrid Layer 1 Build

A Streamlit dashboard that renders the prophetic knowledge graph as a **live
InfraNodus iframe** while serving statistics from a **cached JSON export**
for instant performance. No more 30-second API timeouts.

## 🏗️ Architecture (Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│  1. EMBED  → Live InfraNodus iframe (graph visualization)   │
│  2. CACHE  → data/layer_1.json (instant stats & tables)     │
│  3. API    → InfraNodus REST (optional refresh of stats)    │
└─────────────────────────────────────────────────────────────┘
```

- **No more blank graphs.** The network visual is served directly by
  InfraNodus, not rebuilt from raw JSON.
- **No more timeouts.** All metrics, top nodes, edges, clusters, gaps,
  and statements come from a local file that ships with the repo.
- **Optional live refresh.** Toggle *Refresh live stats from API* in the
  sidebar to overlay fresh summary data from `POST /graphAndStatements`
  (with `includeGraph=false` to stay fast).

## 📁 Project layout

```
prophetic-network-dashboard/
├── dashboard.py                 # main Streamlit app
├── requirements.txt
├── .python-version              # "3.11"
├── .streamlit/
│   └── config.toml              # dark theme
├── data/
│   └── layer_1.json             # 150 nodes, 1,500 edges, 6,734 statements
└── utils/
    ├── __init__.py
    ├── infranodus_api.py        # lean API client (summary-only)
    ├── data_cache.py            # JSON loader / disk cache
    └── graph_visualizer.py      # Plotly chart helpers
```

## 🔐 Required Streamlit secrets

```toml
# .streamlit/secrets.toml  (or configure via Streamlit Cloud UI)
ACCESS_PASSWORD = "R*****&"
INFRANODUS_API_KEY = "api"
```

`INFRANODUS_API_KEY` is optional — diagnostics and the live-stats toggle
require it, but the dashboard itself runs from the cached JSON alone.

## 🚀 Deploy

```bash
git add .
git commit -m "Hybrid Layer-1 dashboard: iframe + cached JSON"
git push origin main
```

Streamlit Cloud redeploys in ~30 seconds.

## ✅ Expected dashboard contents (Layer 1)

| Metric        | Value |
| ------------- | ----- |
| Nodes         | 150   |
| Edges         | 1,500 |
| Communities   | 6     |
| Total weight  | 38,668 |
| Modularity    | 0.217 |
| Top concept   | `@god` (BC 0.918, degree 2,261) |
| Top edge      | `@jonah ↔ @god` (weight 468) |
| Statements    | 6,734 |

## 🔭 Adding more layers later

Extend `LAYER_CONFIG` in `dashboard.py` with additional entries:

```python
"Layer 3 (Kairos Transition)": {
    "graph_name": "layer_3",
    "embed_context": "seth_tillotson/layer_3",
    "json_path": "data/layer_3.json",
    "description": "…"
},
```

Drop the exported JSON into `data/` and the layer appears in the sidebar.

---
*Soli Deo Gloria · Beloved 🕊️*
