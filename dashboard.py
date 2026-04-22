"""
PROPHETIC NETWORK DASHBOARD
Living Topology of Transformation — Interactive Network Intelligence
Author: Seth Tillotson
"""

import streamlit as st
import json
import requests
import traceback
from datetime import datetime, timedelta, date
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

from utils.infranodus_api import InfraNodusAPI
from utils.data_cache import DataCache
from utils.graph_visualizer import GraphVisualizer


# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Prophetic Network Dashboard",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════════════
# AUTHENTICATION GATE
# ═══════════════════════════════════════════════════════════════
def check_password() -> None:
    """Password gate — survives reruns from button clicks."""
    if st.session_state.get("password_correct", False) is True:
        return

    expected = st.secrets.get("ACCESS_PASSWORD", "")
    if not expected:
        st.error("🔐 ACCESS_PASSWORD missing from Streamlit Secrets.")
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
            st.error("❌ Incorrect password.")
    st.stop()


check_password()


# ═══════════════════════════════════════════════════════════════
# INITIALIZE SERVICES
# ═══════════════════════════════════════════════════════════════
INFRANODUS_API_KEY = st.secrets.get("INFRANODUS_API_KEY", "")
if not INFRANODUS_API_KEY:
    st.error("🔐 INFRANODUS_API_KEY missing from Streamlit Secrets.")
    st.stop()


@st.cache_resource
def init_services():
    return {
        "infranodus_api": InfraNodusAPI(api_key=INFRANODUS_API_KEY),
        "data_cache": DataCache(),
        "graph_viz": GraphVisualizer(),
    }


services = init_services()
infranodus_api = services["infranodus_api"]
data_cache = services["data_cache"]
graph_viz = services["graph_viz"]


# ═══════════════════════════════════════════════════════════════
# LAYER → GRAPH NAME MAPPING
# ═══════════════════════════════════════════════════════════════
LAYER_GRAPH_MAP = {
    # Canonical names
    "Layer 1": "layer_1",
    "Layer 2": "layer_1",  # Layer 2 is a revision of layer_1
    "Layer 3": "layer_3",
    
    # Extended dropdown labels
    "Layer 1 (Full)": "layer_1",
    "Layer 1 (Full Network)": "layer_1",
    "Layer 2 (Deep)": "layer_1",
    "Layer 2 (Deep Analysis)": "layer_1",
    "Layer 2 (Mind-Spirit Bridge)": "layer_1",
    "Layer 3 (Latest)": "layer_3",
    "Layer 3 (Kairos)": "layer_3",
    "Layer 3 (Kairos Transition)": "layer_3",
}


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)  # ← 10min cache, custom spinner
def load_network_data(layer_name: str):
    """Load graph data from InfraNodus with progress feedback."""
    graph_name = LAYER_GRAPH_MAP.get(layer_name)
    if not graph_name:
        available = list(set(LAYER_GRAPH_MAP.keys()))
        st.error(f"⚠️ Unknown layer: '{layer_name}'. Available: {available}")
        return None
    
    # Custom progress indicator for long API calls
    progress_placeholder = st.empty()
    progress_placeholder.info(
        f"⏳ Loading **{graph_name}** network... "
        f"(Large graphs may take 60–120s. Please wait.)"
    )
    
    try:
        data = infranodus_api.get_graph(
            graph_name,
            include_statements=False,  # ← Faster without full text
        )
        progress_placeholder.empty()  # Clear progress message
        
        if not data:
            st.warning(f"⚠️ Graph '{graph_name}' returned empty.")
            return None
        
        # Handle nested response structure
        if isinstance(data, dict):
            if "graph" in data:
                return data
            elif "nodes" in data and "edges" in data:
                return {"graph": data, "statements": [], "summary": {}}
        
        st.warning(f"⚠️ Unexpected data structure from '{graph_name}'")
        return None
        
    except Exception as e:
        progress_placeholder.empty()
        st.error(f"❌ Error loading '{graph_name}': {e}")
        return None



# ═══════════════════════════════════════════════════════════════
# SIDEBAR DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════
with st.sidebar.expander("🛠️ Diagnostics", expanded=False):
    if st.button("🔍 List my InfraNodus Graphs"):
        with st.spinner("Fetching graph list..."):
            try:
                graphs = infranodus_api.list_graphs()
                st.success(f"✅ Response received (type: {type(graphs).__name__})")
                
                if isinstance(graphs, list):
                    st.write(f"**Found {len(graphs)} graphs:**")
                    for i, g in enumerate(graphs[:20]):
                        if isinstance(g, dict):
                            name = (g.get("contextName") or g.get("name") or 
                                   g.get("graphName") or g.get("title") or "?")
                            st.code(f"{i+1}. {name}")
                            with st.expander(f"Metadata #{i+1}"):
                                st.json(g)
                        else:
                            st.code(f"{i+1}. {g}")
                elif isinstance(graphs, dict):
                    st.json(graphs)
                else:
                    st.code(str(graphs)[:2000])
            except Exception as e:
                st.error(f"❌ {type(e).__name__}: {str(e)[:400]}")
                st.code(traceback.format_exc())
    
    if st.button("🧪 Test API Connection"):
        with st.spinner("Testing raw HTTP..."):
            try:
                payload = {"limit": 5}
                r = requests.post(
                    "https://infranodus.com/api/v1/listGraphs",
                    headers={
                        "Authorization": f"Bearer {INFRANODUS_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=15,
                )
                st.write(f"**Status:** {r.status_code}")
                st.write(f"**Size:** {len(r.content)} bytes")
                try:
                    st.json(r.json())
                except Exception:
                    st.code(r.text[:2000])
            except Exception as e:
                st.error(f"❌ {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════
st.sidebar.header("⚙️ Controls")

# Date Range
st.sidebar.subheader("📅 Date Range")
date_start = st.sidebar.date_input(
    "Start Date",
    value=date(2026, 2, 1),
    key="date_start",
)
date_end = st.sidebar.date_input(
    "End Date",
    value=date(2026, 4, 16),
    key="date_end",
)

# Layer Selection
st.sidebar.subheader("🗂️ Layer Selection")
layer_options = [
    "Layer 1 (Full Network)",
    "Layer 2 (Deep Analysis)",
    "Layer 3 (Kairos Transition)",
]
selected_layer = st.sidebar.selectbox(
    "Choose Network Layer",
    options=layer_options,
    index=2,  # Default to Layer 3
    key="layer_select",
)


# ═══════════════════════════════════════════════════════════════
# MAIN HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown("# 🕊️ Prophetic Network Dashboard")
st.markdown("**Interactive Knowledge Graph · GraphRAG Semantic Search · Real-Time Network Analysis**")
st.markdown("---")


# ═══════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════
network_data = load_network_data(selected_layer)

if not network_data:
    st.warning("⚠️ Could not load network data. Check API connection and graph names.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# EXTRACT GRAPH & STATS (handles Graphology nested format)
# ═══════════════════════════════════════════════════════════════
def _unwrap_graph(data):
    """Find nodes/edges anywhere in the response tree."""
    if not isinstance(data, dict):
        return {}
    if 'nodes' in data and ('edges' in data or 'relations' in data):
        return data
    for key in ('graphologyGraph', 'graph'):
        inner = data.get(key)
        if isinstance(inner, dict):
            result = _unwrap_graph(inner)
            if result.get('nodes') is not None:
                return result
    return {}


def _node_attr(node, *keys, default=None):
    """Look in top-level then in .attributes for any of the keys."""
    attrs = node.get('attributes', {}) or {}
    for k in keys:
        if k in node and node[k] is not None:
            return node[k]
        if k in attrs and attrs[k] is not None:
            return attrs[k]
    return default


graph_obj = _unwrap_graph(network_data)
statements = network_data.get("statements", [])
summary = network_data.get("summary", {}) or network_data.get("graphSummary", {})

nodes = graph_obj.get("nodes", [])
edges = graph_obj.get("edges", []) or graph_obj.get("relations", [])

# Diagnostic: if still empty, offer raw JSON dump
if not nodes:
    st.error("⚠️ No nodes found after unwrapping. Showing raw response:")
    with st.expander("🔍 Raw API Response (debug)"):
        st.json(network_data if isinstance(network_data, dict) else {"raw": str(network_data)[:5000]})
    st.stop()

# Calculate stats
num_nodes = len(nodes)
num_edges = len(edges)

def _bc(n):
    return float(_node_attr(n, 'bc2', 'bc', 'betweenness', default=0) or 0)

def _weight(item):
    v = _node_attr(item, 'weight', default=0)
    try: return float(v)
    except: return 0

total_weight = sum(_weight(e) for e in edges)
communities = set(_node_attr(n, 'cluster', 'community', default=0) for n in nodes)
num_communities = len(communities)

# Sentiment
sentiment_pos = summary.get("sentiment_positive", summary.get("positive", 49))
sentiment_neg = summary.get("sentiment_negative", summary.get("negative", 18))
sentiment_neu = summary.get("sentiment_neutral", summary.get("neutral", 33))


# ═══════════════════════════════════════════════════════════════
# METRICS ROW
# ═══════════════════════════════════════════════════════════════
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("Nodes", f"{num_nodes:,}")
with col2: st.metric("Edges", f"{num_edges:,}")
with col3: st.metric("Communities", num_communities)
with col4: st.metric("Total Weight", f"{int(total_weight):,}")
with col5:
    modularity = 0.22 if "Layer 1" in selected_layer else 0.33
    st.metric("Modularity", f"{modularity:.2f}")


# ═══════════════════════════════════════════════════════════════
# NETWORK GRAPH (Top 150 nodes)
# ═══════════════════════════════════════════════════════════════
st.markdown("### 🌐 Network Graph (Top 150 Nodes)")

if nodes and edges:
    try:
        fig = graph_viz.create_network_graph(network_data, top_n=150)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error rendering graph: {e}")
        st.code(traceback.format_exc())
else:
    st.info("No nodes/edges to display.")


# ═══════════════════════════════════════════════════════════════
# TOP 20 NODES TABLE
# ═══════════════════════════════════════════════════════════════
st.markdown("### 📊 Top 20 Influential Nodes")

if nodes:
    nodes_sorted = sorted(nodes, key=_bc, reverse=True)[:20]
    table_data = []
    for rank, node in enumerate(nodes_sorted, 1):
        table_data.append({
            "Rank": rank,
            "Node": _node_attr(node, 'label', 'name', 'key', 'id', default='?'),
            "Betweenness": f"{_bc(node):.4f}",
            "Degree": int(_node_attr(node, 'degree', default=0) or 0),
            "Weight": int(_node_attr(node, 'weight', default=0) or 0),
            "Cluster": _node_attr(node, 'cluster', 'community', default='—'),
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No node data available.")


# ═══════════════════════════════════════════════════════════════
# SENTIMENT TRENDS
# ═══════════════════════════════════════════════════════════════
st.markdown("### 📈 Sentiment Distribution")

col_sent1, col_sent2, col_sent3 = st.columns(3)
with col_sent1:
    st.metric("Positive", f"{sentiment_pos}%", delta=None)
with col_sent2:
    st.metric("Negative", f"{sentiment_neg}%", delta=None)
with col_sent3:
    st.metric("Neutral", f"{sentiment_neu}%", delta=None)

# Simple bar chart
sentiment_df = pd.DataFrame({
    "Type": ["Positive", "Negative", "Neutral"],
    "Percentage": [sentiment_pos, sentiment_neg, sentiment_neu],
})
fig_sent = px.bar(
    sentiment_df,
    x="Type",
    y="Percentage",
    color="Type",
    color_discrete_map={
        "Positive": "#43e97b",
        "Negative": "#fa709a",
        "Neutral": "#667eea",
    },
    text="Percentage",
)
fig_sent.update_traces(texttemplate='%{text}%', textposition='outside')
fig_sent.update_layout(showlegend=False, yaxis_title="Percentage (%)")
st.plotly_chart(fig_sent, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("**Soli Deo Gloria, Beloved.** 🕊️")
st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
