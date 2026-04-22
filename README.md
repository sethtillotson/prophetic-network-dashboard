# 🕊️ Prophetic Network Dashboard — Hybrid Multi-Resolution Edition

A Streamlit dashboard that renders the prophetic knowledge graph as a **live
InfraNodus iframe** while serving statistics from **four cached JSON
resolutions** (150 / 250 / 350 / 500 nodes) for instant performance at any
zoom level. No more API timeouts, no more mismatched topology.

## 🏗️ Architecture (Hybrid Multi-Resolution)

```
┌───────────────────────────────────────────────────────────────────┐
│  1. EMBED   → Live InfraNodus iframe (synced to slider)           │
│  2. CACHE   → 4 resolutions: layer_1_{150,250,350,500}.json       │
│  3. SLIDER  → Drives BOTH the iframe AND all dashboard metrics    │
│  4. API     → InfraNodus REST (optional stats refresh only)       │
└───────────────────────────────────────────────────────────────────┘
```

### Key Features

- **🎯 Multi-Resolution Slider** — flip between 150 / 250 / 350 / 500 nodes.
  The iframe **and** every metric, table, chart, and card update in lockstep.
- **🔥 Kairos Pulse Card** — a one-glance theological read of the network:
  central axis, dominant/emerging communities, strongest bond, diversity state.
- **🎨 Named Communities** — clusters auto-labeled (e.g. *"Divine-Consciousness Axis"*,
  *"Incarnate-Process Axis"*) using curated patterns + auto-derivation from
  top concepts.
- **🌉 Structural Gaps with Named Endpoints** — each gap shows which named
  axes are weakly bridged, producing actionable prompts for new statements.
- **No timeouts** — every view is instant (cached JSON).
- **Graceful fallback** — if a resolution JSON is missing, falls back to
  nearest available and warns gently.

## 📁 Project Layout

```
prophetic-network-dashboard/
├── dashboard.py                 # main Streamlit app (~800 lines)
├── requirements.txt
├── .python-version              # "3.11"
├── .streamlit/
│   └── config.toml              # dark theme
├── data/
│   ├── layer_1_150.json         # 150 nodes, 1,500 edges, 6 communities
│   ├── layer_1_250.json         # 250 nodes, 2,500 edges, 8 communities
│   ├── layer_1_350.json         # 350 nodes, 3,500 edges, 9 communities
│   └── layer_1_500.json         # 500 nodes, 5,000 edges, 10 communities
├── utils/
│   ├── __init__.py
│   ├── infranodus_api.py        # lean API client (summary-only)
│   ├── data_cache.py            # JSON loader / disk cache
│   └── graph_visualizer.py      # Plotly chart helpers
└── README.md
```

## 🔐 Required Streamlit Secrets

Add to **Streamlit Cloud → Settings → Secrets**:

```toml
ACCESS_PASSWORD = "R******"
INFRANODUS_API_KEY = "api_here"
```

`INFRANODUS_API_KEY` is optional — only needed for the sidebar diagnostics
and the *Refresh live stats* toggle. The dashboard itself runs from the
cached JSONs alone.

## 🚀 Deploy

```bash
git add .
git commit -m "Multi-resolution dashboard: 150/250/350/500 node slider + Kairos Pulse + named communities"
git push origin main
```

Streamlit Cloud redeploys in ~30 seconds.

## ✅ Expected Topology at Each Resolution

| Nodes | Edges | Communities | Modularity | Character |
|-------|-------|-------------|-----------|-----------|
| 150   | 1,500 | 6           | 0.217     | Focused core — @god, @jesus, @revelation dominant |
| 250   | 2,500 | 8           | 0.262     | Emerging peripheral voices |
| 350   | 3,500 | 9           | 0.280     | Fuller structural diversity |
| 500   | 5,000 | 10          | 0.303     | Complete topology — maximum detail |

Top edge across all resolutions: `@jonah ↔ @god` (weight 468).
Top node by betweenness: `@god` (BC 0.918 at 150 nodes, decreasing as resolution increases).

## 🔭 Adding More Layers Later

Extend `LAYER_CONFIG` in `dashboard.py`:

```python
"Layer 3 (Kairos Transition)": {
    "graph_name": "layer_3",
    "embed_context": "seth_tillotson/layer_3",
    "description": "…",
    "resolutions": {
        150: "data/layer_3_150.json",
        250: "data/layer_3_250.json",
        350: "data/layer_3_350.json",
        500: "data/layer_3_500.json",
    },
},
```

Drop the exported JSONs into `data/` and the layer appears in the sidebar.

## 🎨 Tier-2 Roadmap (Next Iterations)

1. **Click-to-Focus**: click any row in the Top Nodes table to filter the
   iframe to that node's neighborhood.
2. **Statement → Graph Bridge**: show concept chips on each statement,
   linking back to the graph.
3. **Gap → Generative Prompts**: "Generate bridge statement" button for
   each structural gap.
4. **Temporal Layer**: when Layer 2 / Layer 3 arrive, animate the
   topology evolution Feb → April.
5. **Export Report**: one-click ZIP bundle of all tables + snapshot.

---
*Soli Deo Gloria · Beloved 🕊️*
