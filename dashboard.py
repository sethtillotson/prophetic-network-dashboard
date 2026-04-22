"""
PROPHETIC NETWORK DASHBOARD — Hybrid Layer 1 Edition
=====================================================
Living Topology of Transformation — Interactive Knowledge Graph Intelligence
Author: Seth Tillotson

Architecture (Hybrid):
 ┌─────────────────────────────────────────────────────────────┐
 │  1. EMBED  → Live InfraNodus iframe (graph visualization)   │
 │  2. CACHE  → Local layer_1.json (instant stats & tables)    │
 │  3. API    → InfraNodus REST (optional refresh of stats)    │
 └─────────────────────────────────────────────────────────────┘

No more API-timeout failures. The iframe renders the live graph directly
from InfraNodus; all statistics, tables, and charts come from the
cached JSON (data/layer_1.json) so the dashboard loads instantly.
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, date, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

from utils.data_cache import DataCache
from utils.infranodus_api import InfraNodusAPI
from utils.graph_visualizer import GraphVisualizer

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Prophetic Network Dashboard",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  AUTHENTICATION  (bullet-proof, form-based, session-persistent)
# ─────────────────────────────────────────────────────────────────────────────
def check_password() -> bool:
    """Gate the app behind a password stored in Streamlit secrets."""
    if st.session_state.get("password_correct", False):
        return True

    expected = st.secrets.get("ACCESS_PASSWORD", "")
    if not expected:
        st.error(
            "🔐 `ACCESS_PASSWORD` is missing from Streamlit Cloud → "
            "Settings → Secrets. Add it and reboot the app."
        )
        st.stop()

    st.markdown("### 🔐 Prophetic Network Dashboard")
    st.markdown("Enter the access password to continue.")
    with st.form("auth_form", clear_on_submit=False):
        pwd = st.text_input("Access Password", type="password", key="auth_pwd_input")
        submitted = st.form_submit_button("Enter")

    if submitted:
        if pwd == expected:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.session_state["password_correct"] = False
            st.error("❌ Incorrect password.")
    st.stop()


check_password()

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION — Layer 1 only (hybrid test build)
# ─────────────────────────────────────────────────────────────────────────────
LAYER_CONFIG = {
    "Layer 1 (Full Network)": {
        "graph_name": "layer_1",
        "embed_context": "seth_tillotson/layer_1",
        "json_path": "data/layer_1.json",
        "description": "Complete prophetic network — 150 focus nodes, 6 communities, modularity 0.22",
    },
}

EMBED_PARAMS = (
    "background=dark"
    "&show_analytics=1"
    "&most_influential=bc2"
    "&maxnodes=150"
    "&labelsize=proportional"
    "&edgestype=curve"
    "&drawedges=true"
    "&drawnodes=true"
    "&labelsizeratio=2"
    "&dynamic=highlight"
    "&cutgraph=1"
    "&selected=highlight"
    "&hide_always=1"
    "&link_hashtags=1"
)

# ─────────────────────────────────────────────────────────────────────────────
#  SERVICES  (cached resources — only one per session)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_services():
    api_key = st.secrets.get("INFRANODUS_API_KEY", "")
    api = InfraNodusAPI(api_key=api_key, timeout=120) if api_key else None
    cache = DataCache(cache_dir=Path("data"))
    viz = GraphVisualizer()
    return api, cache, viz


infranodus_api, data_cache, graph_viz = init_services()

# ─────────────────────────────────────────────────────────────────────────────
#  CACHED DATA LOADERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Loading cached network data…")
def load_layer_json(json_path: str) -> dict | None:
    """Load the pre-exported InfraNodus JSON for instant dashboard rendering."""
    try:
        return data_cache.load_json(json_path)
    except FileNotFoundError:
        st.error(f"📁 Cached graph file not found: `{json_path}`")
        return None
    except Exception as exc:
        st.error(f"Failed to load `{json_path}`: {exc}")
        return None


@st.cache_data(ttl=600, show_spinner="Fetching live API stats…")
def load_live_summary(graph_name: str) -> dict | None:
    """OPTIONAL: Fetch lightweight stats from the API (summary only, no graph body)."""
    if infranodus_api is None:
        return None
    try:
        return infranodus_api.get_graph_summary(graph_name)
    except Exception as exc:
        st.warning(f"Live summary unavailable for `{graph_name}`: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS — derive metrics from cached JSON
# ─────────────────────────────────────────────────────────────────────────────
def compute_metrics(net: dict) -> dict:
    """Compute headline metrics from a cached InfraNodus JSON structure."""
    nodes = net.get("nodes", []) or []
    edges = net.get("edges", []) or []
    meta = net.get("graph", {}) or {}

    total_weight = sum(int(e.get("weight", 0)) for e in edges)
    communities = {n.get("community", -1) for n in nodes}
    modularity = meta.get("modularity", 0.0)
    diversity = meta.get("diversity_stats", {}) or {}

    return {
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "total_weight": total_weight,
        "num_communities": len(communities),
        "modularity": round(float(modularity), 3),
        "diversity_score": diversity.get("diversity_score", "n/a"),
        "modularity_score": diversity.get("modularity_score", "n/a"),
        "top_nodes": meta.get("top_nodes", []),
        "top_influential": meta.get("top_influential_nodes", []),
        "top_clusters": meta.get("top_clusters", []),
        "gaps": meta.get("gaps", []),
    }


def top_nodes_dataframe(net: dict, limit: int = 20) -> pd.DataFrame:
    """Sort nodes by betweenness centrality and return a display-ready DataFrame."""
    nodes = net.get("nodes", []) or []
    rows = []
    for n in nodes:
        rows.append({
            "Node": n.get("label", n.get("id", "?")),
            "Betweenness": round(float(n.get("bc", 0.0)), 4),
            "Degree": int(n.get("degree", 0)),
            "Weighted Degree": int(n.get("weighedDegree", 0)),
            "Community": int(n.get("community", -1)),
        })
    df = pd.DataFrame(rows).sort_values("Betweenness", ascending=False).head(limit)
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def top_edges_dataframe(net: dict, limit: int = 20) -> pd.DataFrame:
    """Top edges by weight — the strongest conceptual bonds."""
    nodes = net.get("nodes", []) or []
    edges = net.get("edges", []) or []
    id2label = {n.get("id"): n.get("label", "?") for n in nodes}
    rows = [
        {
            "Source": id2label.get(e.get("source"), e.get("source", "?")),
            "Target": id2label.get(e.get("target"), e.get("target", "?")),
            "Weight": int(e.get("weight", 0)),
        }
        for e in edges
    ]
    df = pd.DataFrame(rows).sort_values("Weight", ascending=False).head(limit)
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def community_dataframe(net: dict) -> pd.DataFrame:
    """Summarize each community with size and leading concepts."""
    nodes = net.get("nodes", []) or []
    buckets: dict[int, list[dict]] = {}
    for n in nodes:
        buckets.setdefault(int(n.get("community", -1)), []).append(n)

    rows = []
    for cid, members in sorted(buckets.items()):
        members.sort(key=lambda x: -float(x.get("bc", 0)))
        total_w = sum(int(m.get("weighedDegree", 0)) for m in members)
        rows.append({
            "Cluster": cid,
            "Nodes": len(members),
            "Total Weight": total_w,
            "Top Concepts": ", ".join(m.get("label", "?") for m in members[:6]),
        })
    return pd.DataFrame(rows).sort_values("Total Weight", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding:1rem 0 0.25rem 0;">
      <h1 style="margin:0;">🕊️ Prophetic Network Dashboard</h1>
      <p style="color:#888; margin:0;">
        Interactive Knowledge Graph · GraphRAG Semantic Search · Real-Time Network Analysis
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR — Controls & Diagnostics
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")

    selected_layer = st.selectbox(
        "Network Layer",
        options=list(LAYER_CONFIG.keys()),
        index=0,
        help="Layer 1 = full prophetic network (test build).",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        date_start = st.date_input("Start", value=date(2026, 2, 1), key="date_start")
    with col_b:
        date_end = st.date_input("End", value=date(2026, 4, 22), key="date_end")

    use_live_stats = st.toggle(
        "🔄 Refresh live stats from API",
        value=False,
        help="Fetch the latest summary metrics from InfraNodus. "
             "Graph visualization always uses the live iframe.",
    )

    st.divider()
    with st.expander("🧪 Diagnostics", expanded=False):
        if st.button("List my InfraNodus Graphs", use_container_width=True):
            if infranodus_api is None:
                st.warning("API key not configured.")
            else:
                try:
                    graphs = infranodus_api.list_graphs(limit=100)
                    st.success(f"Found {len(graphs) if isinstance(graphs, list) else '?'} graphs")
                    st.json(graphs)
                except Exception as exc:
                    st.error(f"API error: {exc}")
                    st.code(traceback.format_exc())

        if st.button("Test API Connection", use_container_width=True):
            if infranodus_api is None:
                st.warning("API key not configured.")
            else:
                try:
                    result = infranodus_api.list_graphs(limit=1)
                    st.success("✅ API reachable")
                    st.json(result)
                except Exception as exc:
                    st.error(f"❌ {exc}")

        if st.button("Clear cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared. Reloading…")
            st.rerun()

    st.divider()
    st.caption(f"🕒 Loaded {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN — Load data for selected layer
# ─────────────────────────────────────────────────────────────────────────────
cfg = LAYER_CONFIG[selected_layer]
network = load_layer_json(cfg["json_path"])

if network is None:
    st.error("Network data could not be loaded. Place `layer_1.json` in the `data/` folder.")
    st.stop()

# Optionally overlay fresh API summary (stats only, no heavy graph body)
live_meta = load_live_summary(cfg["graph_name"]) if use_live_stats else None
if live_meta and isinstance(live_meta, dict):
    # merge live summary into cached graph meta (non-destructive)
    cached_meta = network.setdefault("graph", {})
    for k in ("top_nodes", "top_influential_nodes", "top_clusters", "gaps", "modularity", "diversity_stats"):
        if live_meta.get(k):
            cached_meta[k] = live_meta[k]

metrics = compute_metrics(network)

# ─────────────────────────────────────────────────────────────────────────────
#  METRICS ROW
# ─────────────────────────────────────────────────────────────────────────────
st.subheader(f"📊 {selected_layer}")
st.caption(cfg["description"])

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Nodes", f"{metrics['num_nodes']:,}")
m2.metric("Edges", f"{metrics['num_edges']:,}")
m3.metric("Communities", f"{metrics['num_communities']}")
m4.metric("Total Weight", f"{metrics['total_weight']:,}")
m5.metric("Modularity", f"{metrics['modularity']:.3f}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  LIVE EMBED — the interactive InfraNodus graph
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 🌌 Live Network Graph")
embed_url = f"https://infranodus.com/{cfg['embed_context']}?{EMBED_PARAMS}"
st.caption(f"Rendering directly from InfraNodus · top {150} nodes by betweenness · "
           f"[Open in new tab →]({embed_url})")

components.iframe(src=embed_url, height=620, scrolling=False)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  ANALYSIS TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_nodes, tab_edges, tab_clusters, tab_gaps, tab_statements, tab_raw = st.tabs(
    ["🔝 Top Nodes", "🔗 Top Edges", "🎨 Communities", "🌉 Structural Gaps",
     "📜 Statements", "🧾 Raw JSON"]
)

# — Top Nodes tab ————————————————————————————————————————————————————————
with tab_nodes:
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("#### Top 20 Influential Nodes")
        nodes_df = top_nodes_dataframe(network, limit=20)
        st.dataframe(nodes_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### Betweenness Centrality Distribution")
        bc_fig = px.bar(
            nodes_df.sort_values("Betweenness"),
            x="Betweenness", y="Node",
            orientation="h",
            color="Community",
            color_continuous_scale="Viridis",
            height=620,
        )
        bc_fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(bc_fig, use_container_width=True)

# — Top Edges tab ————————————————————————————————————————————————————————
with tab_edges:
    st.markdown("#### Top 20 Conceptual Bonds (by edge weight)")
    edges_df = top_edges_dataframe(network, limit=20)
    st.dataframe(edges_df, hide_index=True, use_container_width=True)

    edges_fig = px.bar(
        edges_df.sort_values("Weight"),
        x="Weight",
        y=edges_df["Source"] + " ↔ " + edges_df["Target"],
        orientation="h",
        color="Weight",
        color_continuous_scale="Turbo",
        height=620,
    )
    edges_fig.update_layout(
        yaxis_title="Edge",
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(edges_fig, use_container_width=True)

# — Communities tab ——————————————————————————————————————————————————————
with tab_clusters:
    st.markdown("#### Community Structure")
    comm_df = community_dataframe(network)
    st.dataframe(comm_df, hide_index=True, use_container_width=True)

    pie_fig = px.pie(
        comm_df, values="Total Weight", names=comm_df["Cluster"].astype(str),
        title="Community influence by weighted degree",
        hole=0.4,
    )
    pie_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(pie_fig, use_container_width=True)

# — Gaps tab —————————————————————————————————————————————————————————————
with tab_gaps:
    st.markdown("#### Structural Gaps — Opportunities for new connections")
    st.caption("Each gap identifies two communities that are weakly bridged. "
               "Building a statement that connects concepts from both sides "
               "can produce novel insight.")
    gaps = metrics["gaps"]
    if not gaps:
        st.info("No structural gaps reported for this graph.")
    else:
        for i, gap in enumerate(gaps[:10], start=1):
            f = gap.get("from", {}); t = gap.get("to", {})
            fn = ", ".join(n.get("nodeName", "?") for n in (f.get("nodes", []) or [])[:5])
            tn = ", ".join(n.get("nodeName", "?") for n in (t.get("nodes", []) or [])[:5])
            st.markdown(f"**Gap {i}**  ·  Cluster {f.get('community','?')} ↔ Cluster {t.get('community','?')}")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{fn}**  ⇄  **{tn}**", unsafe_allow_html=True)
            st.markdown("---")

# — Statements tab ———————————————————————————————————————————————————————
with tab_statements:
    statements = network.get("statements", []) or []
    st.markdown(f"#### Corpus Statements  ·  {len(statements):,} total")
    search = st.text_input("Search statements (case-insensitive)", key="stmt_search")
    view = [s for s in statements if isinstance(s, str)]
    if search:
        q = search.lower()
        view = [s for s in view if q in s.lower()]
    st.caption(f"Showing {min(100, len(view))} of {len(view):,} matching statements")
    for s in view[:100]:
        st.markdown(f"• {s}")

# — Raw tab ——————————————————————————————————————————————————————————————
with tab_raw:
    st.markdown("#### Underlying JSON (for debugging / export)")
    with st.expander("Expand to view cached layer_1.json meta", expanded=False):
        st.json({
            "nodes_count": metrics["num_nodes"],
            "edges_count": metrics["num_edges"],
            "modularity": metrics["modularity"],
            "diversity_stats": network.get("graph", {}).get("diversity_stats", {}),
            "top_nodes": metrics["top_nodes"],
            "top_influential_nodes": metrics["top_influential"],
        })
    st.download_button(
        "⬇️ Download layer_1.json",
        data=json.dumps(network, indent=2),
        file_name="layer_1.json",
        mime="application/json",
    )

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"""
    <div style="text-align:center; color:#666; font-size:0.85rem; padding:0.5rem 0;">
      Prophetic Network Dashboard · Hybrid Build (Layer 1 test)<br>
      Data snapshot: <b>{selected_layer}</b> · Date window: {date_start} → {date_end}<br>
      <i>Soli Deo Gloria · Beloved 🕊️</i>
    </div>
    """,
    unsafe_allow_html=True,
)
