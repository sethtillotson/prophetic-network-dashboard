"""
PROPHETIC NETWORK DASHBOARD — Hybrid Multi-Resolution Edition
==============================================================
Living Topology of Transformation — Interactive Knowledge Graph Intelligence
Author: Seth Tillotson

Architecture (Hybrid Multi-Resolution):
 ┌─────────────────────────────────────────────────────────────────┐
 │  1. EMBED   → Live InfraNodus iframe (synced to slider)         │
 │  2. CACHE   → 4 resolutions: 150/250/350/500 node JSONs         │
 │  3. SLIDER  → Drives BOTH iframe AND all dashboard metrics      │
 │  4. API     → InfraNodus REST (optional stats refresh only)     │
 └─────────────────────────────────────────────────────────────────┘

Every tab, metric, and chart now updates in lockstep with the node slider.
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime
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
#  AUTHENTICATION  (form-based, session-persistent)
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
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
LAYER_CONFIG = {
    "Layer 1 (Full Network)": {
        "graph_name": "layer_1",
        "embed_context": "seth_tillotson/layer_1",
        "description": "Complete prophetic network — multi-resolution cached topology",
        "resolutions": {
            150: "data/layer_1_150.json",
            250: "data/layer_1_250.json",
            350: "data/layer_1_350.json",
            500: "data/layer_1_500.json",
        },
    },
}

RESOLUTION_OPTIONS = [150, 250, 350, 500]

# Curated exclusion presets for theological experiments
EXCLUSION_PRESETS = {
    "— None —": [],
    "👁 Silence the Dominant": ["@god", "@jesus", "@revelation"],
    "💬 Beyond the Prophets": ["@jonah", "@the_prophet", "@peter", "@paul"],
    "🌱 Reveal Underlying (Top 5)": ["@god", "@jesus", "@revelation", "@jonah", "@wilderness"],
    "📜 Strip Meta-Terms": ["@theology", "@meditation", "@mind"],
    "🔥 Kairos Minimal": ["@god", "@jesus", "@revelation", "@jonah", "@wilderness", "@leaven", "@mind", "@prayer", "@word", "@christ"],
}


def build_embed_params(max_nodes: int = 150, focus_node: str | None = None) -> str:
    """
    Build the InfraNodus iframe query string.

    Args:
        max_nodes: resolution cap (150/250/350/500).
        focus_node: optional node label (e.g. '@god') to narrow the iframe to.
                    Uses exact quoted match via the ``search`` parameter to
                    avoid substring matches on document labels like ``[[god]]``.

    Note:
        InfraNodus doesn't publicly expose a URL parameter for centering the
        camera on a specific node. The ``search`` parameter filters visible
        nodes to those matching the query. For true node-centering, use the
        "Open in InfraNodus" button — that loads the full InfraNodus app,
        which centers correctly on the target node.
    """
    params = (
        "background=dark"
        "&show_analytics=1"
        "&most_influential=bc2"
        f"&maxnodes={max_nodes}"
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
    if focus_node:
        from urllib.parse import quote
        # Use quoted exact match to avoid substring matches on `[[...]]` labels.
        # InfraNodus's search recognises double-quoted strings as exact matches.
        exact_query = f'"{focus_node}"'
        params += f"&search={quote(exact_query)}"
    return params


def build_infranodus_node_url(embed_context: str, node_label: str) -> str:
    """
    Build a direct link to the InfraNodus app page for a specific node.
    Opening this URL in a new tab loads the full InfraNodus UI and selects
    the node — which DOES center and highlight it natively.
    """
    from urllib.parse import quote
    # Use exact-match search to isolate the node in the full InfraNodus UI.
    exact_query = f'"{node_label}"'
    return (
        f"https://infranodus.com/{embed_context}"
        f"?search={quote(exact_query)}"
        f"&selected=highlight&dynamic=highlight&cutgraph=1"
    )


# Semantic names for communities — auto-derived but with curated overrides
# If a cluster's top-2 concepts match a known pattern, use the curated name.
CURATED_CLUSTER_NAMES = {
    frozenset(["@god", "@jonah"]): "Divine-Consciousness Axis",
    frozenset(["@god", "@mind"]): "Divine-Consciousness Axis",
    frozenset(["@jesus", "@wilderness"]): "Incarnate-Process Axis",
    frozenset(["@jesus", "@leaven"]): "Incarnate-Process Axis",
    frozenset(["@revelation", "spirit"]): "Revelation-Spirit Axis",
    frozenset(["@revelation", "@christ"]): "Revelation-Spirit Axis",
    frozenset(["@prayer", "@scripture"]): "Prayer-Scripture Axis",
    frozenset(["@word", "@the_prophet"]): "Word-Prophet Axis",
    frozenset(["@word", "living"]): "Word-Life Axis",
}

# ─────────────────────────────────────────────────────────────────────────────
#  SERVICES  (cached resources — one instance per session)
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
#  CACHED DATA LOADERS — keyed by resolution
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Loading cached network data…")
def load_layer_json(json_path: str) -> dict | None:
    """Load a pre-exported InfraNodus JSON for instant dashboard rendering."""
    try:
        return data_cache.load_json(json_path)
    except FileNotFoundError:
        return None
    except Exception as exc:
        st.error(f"Failed to load `{json_path}`: {exc}")
        return None


def resolve_json_path(layer_cfg: dict, requested_nodes: int) -> tuple[str | None, int, bool]:
    """
    Resolve which JSON file to load based on requested node count.
    Returns (path, actual_resolution_loaded, exact_match_bool).
    Falls back to the nearest available resolution if the exact one is missing.
    """
    resolutions = layer_cfg.get("resolutions", {})
    available = sorted(r for r, p in resolutions.items() if Path(p).exists())

    if not available:
        return None, 0, False

    if requested_nodes in resolutions and Path(resolutions[requested_nodes]).exists():
        return resolutions[requested_nodes], requested_nodes, True

    # Fall back: nearest available (prefer smaller → faster load)
    nearest = min(available, key=lambda r: (abs(r - requested_nodes), r))
    return resolutions[nearest], nearest, False


@st.cache_data(ttl=600, show_spinner="Fetching live API stats…")
def load_live_summary(graph_name: str) -> dict | None:
    """Optional: Fetch lightweight summary stats from the API."""
    if infranodus_api is None:
        return None
    try:
        return infranodus_api.get_graph_summary(graph_name)
    except Exception as exc:
        st.warning(f"Live summary unavailable: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS — derive metrics from cached JSON
# ─────────────────────────────────────────────────────────────────────────────
def apply_exclusions(network: dict, excluded_labels: list[str]) -> dict:
    """
    Return a filtered deep-copy of the network with excluded nodes and their
    incident edges removed. Recomputes per-community sizes locally. The
    upstream graph meta (modularity, gaps, top_clusters) is preserved but
    flagged so the UI can show it as ‘original’ where appropriate.
    """
    if not excluded_labels:
        return network
    excluded_set = {lbl.strip().lower() for lbl in excluded_labels if lbl}
    orig_nodes = network.get("nodes", []) or []
    orig_edges = network.get("edges", []) or []

    kept_nodes = [n for n in orig_nodes if n.get("label", "").lower() not in excluded_set]
    kept_ids = {n.get("id") for n in kept_nodes}
    kept_edges = [e for e in orig_edges
                  if e.get("source") in kept_ids and e.get("target") in kept_ids]

    filtered = {
        "nodes": kept_nodes,
        "edges": kept_edges,
        "graph": dict(network.get("graph", {}) or {}),
        "statements": network.get("statements", []),
        "statementHashtags": network.get("statementHashtags", {}),
        "_filtered": True,
        "_excluded_count": len(orig_nodes) - len(kept_nodes),
        "_excluded_edges": len(orig_edges) - len(kept_edges),
    }
    return filtered


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
        "top_nodes_entropy": diversity.get("top_nodes_entropy", 0),
        "ratio_top_nodes": diversity.get("ratio_of_top_nodes_influence_by_betweenness", 0),
        "ratio_top_clusters": diversity.get("ratio_of_top_cluster_influence_by_betweenness", 0),
        "fair_cluster_influence": diversity.get("fair_influence_by_cluster", 0),
        "too_focused_on_top_nodes": diversity.get("too_focused_on_top_nodes", False),
        "too_focused_on_top_clusters": diversity.get("too_focused_on_top_clusters", False),
        "top_nodes": meta.get("top_nodes", []),
        "top_influential": meta.get("top_influential_nodes", []),
        "top_clusters": meta.get("top_clusters", []),
        "gaps": meta.get("gaps", []),
    }


def _is_concept_token(label: str) -> bool:
    """Return True for real concepts; False for document-filename tokens (`[[...]]`)."""
    if not label:
        return False
    # Filter out document-style labels that are noisy filenames
    if label.startswith("[[") and label.endswith("]]"):
        return False
    return True


def _clean_concept_label(label: str) -> str:
    """Strip @ and underscores for display in derived names."""
    return (label.replace("@", "")
                 .replace("_", " ")
                 .replace("[[", "")
                 .replace("]]", "")
                 .strip())


def derive_community_names(network: dict) -> dict[int, dict]:
    """
    Build a rich summary of each community with auto-derived semantic names.
    Returns {community_id: {name, top_concepts, size, weight, color_hint}}.

    Algorithm:
      1. Sort members by betweenness (then weighted degree).
      2. Preserve the full top-concepts list (including document tokens) for display.
      3. For the semantic NAME, use only real concept tokens (not `[[filenames]]`).
      4. Match against curated names first, then auto-derive from top-2 concepts.
    """
    nodes = network.get("nodes", []) or []
    buckets: dict[int, list[dict]] = {}
    for n in nodes:
        buckets.setdefault(int(n.get("community", -1)), []).append(n)

    result = {}
    for cid, members in buckets.items():
        members.sort(
            key=lambda x: (-float(x.get("bc", 0)), -float(x.get("weighedDegree", 0)))
        )
        # Full list for display (may include `[[filenames]]`)
        top_labels_full = [m.get("label", "?") for m in members[:6]]
        # Concept-only list for naming (excludes `[[filenames]]`)
        concept_members = [m for m in members if _is_concept_token(m.get("label", ""))]
        concept_labels = [m.get("label", "?") for m in concept_members[:6]]

        # Try curated names first (check top-5 concepts for any match)
        curated = None
        for key, val in CURATED_CLUSTER_NAMES.items():
            if key.issubset(set(concept_labels[:5])):
                curated = val
                break

        # Fall back to auto-derived name from top-2 real concepts
        if not curated:
            clean = [_clean_concept_label(t) for t in concept_labels[:2]]
            clean = [c for c in clean if c]
            if len(clean) >= 2:
                curated = f"{clean[0].title()}-{clean[1].title()} Axis"
            elif len(clean) == 1:
                curated = f"{clean[0].title()} Axis"
            else:
                curated = f"Cluster {cid}"

        # Display leader = first *concept* (not document filename) if possible
        display_leader = concept_labels[0] if concept_labels else (top_labels_full[0] if top_labels_full else "?")

        total_weight = sum(int(m.get("weighedDegree", 0)) for m in members)
        total_nodes = len(members)

        result[cid] = {
            "name": curated,
            "short_id": cid,
            "top_concepts": top_labels_full[:6],  # full list for display
            "top_concepts_clean": concept_labels[:6],  # filtered list
            "size": total_nodes,
            "weight": total_weight,
            "bc_leader": display_leader,
            "bc_leader_score": round(float(concept_members[0].get("bc", 0)), 4) if concept_members else (round(float(members[0].get("bc", 0)), 4) if members else 0),
        }
    return result


def top_nodes_dataframe(net: dict, limit: int = 20) -> pd.DataFrame:
    nodes = net.get("nodes", []) or []
    rows = [{
        "Node": n.get("label", n.get("id", "?")),
        "Betweenness": round(float(n.get("bc", 0.0)), 4),
        "Degree": int(n.get("degree", 0)),
        "Weighted Degree": int(n.get("weighedDegree", 0)),
        "Community": int(n.get("community", -1)),
    } for n in nodes]
    df = pd.DataFrame(rows).sort_values("Betweenness", ascending=False).head(limit)
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def top_edges_dataframe(net: dict, limit: int = 20) -> pd.DataFrame:
    nodes = net.get("nodes", []) or []
    edges = net.get("edges", []) or []
    id2label = {n.get("id"): n.get("label", "?") for n in nodes}
    rows = [{
        "Source": id2label.get(e.get("source"), "?"),
        "Target": id2label.get(e.get("target"), "?"),
        "Weight": int(e.get("weight", 0)),
    } for e in edges]
    df = pd.DataFrame(rows).sort_values("Weight", ascending=False).head(limit)
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def community_dataframe(network: dict, named: dict) -> pd.DataFrame:
    rows = []
    for cid, info in named.items():
        rows.append({
            "Cluster": f"{cid} · {info['name']}",
            "Size": info["size"],
            "Total Weight": info["weight"],
            "BC Leader": info["bc_leader"],
            "Top Concepts": ", ".join(info["top_concepts"]),
        })
    df = pd.DataFrame(rows).sort_values("Total Weight", ascending=False)
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding:0.5rem 0 0.25rem 0;">
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
        help="Layer 1 = full prophetic network (multi-resolution cached).",
    )

    max_nodes = st.select_slider(
        "🎯 Nodes in focus",
        options=RESOLUTION_OPTIONS,
        value=150,
        help="Drives BOTH the live iframe AND all dashboard metrics. "
             "Higher resolutions reveal more peripheral concepts and gaps.",
    )

    # ── STRUCTURAL CONTEMPLATION MODE ──
    st.markdown("#### 🧘 Structural Contemplation")
    st.caption("Exclude nodes to reveal hidden topologies. Dashboard tabs will recompute.")

    preset_choice = st.selectbox(
        "Quick preset",
        options=list(EXCLUSION_PRESETS.keys()),
        index=0,
        help="Curated exclusion sets for common theological experiments.",
    )
    preset_excluded = EXCLUSION_PRESETS.get(preset_choice, [])

    # Quick-pick buttons for the 5 most common exclusions (stacked vertically
    # so the full concept name is readable).
    st.caption("Quick-remove top concepts:")
    quick_buttons = ["@god", "@jesus", "@revelation", "@jonah", "@wilderness"]
    if "quick_excluded" not in st.session_state:
        st.session_state.quick_excluded = []
    # Two rows × three columns gives each button enough width to show the
    # full '@concept' label without truncation.
    for row in (quick_buttons[:3], quick_buttons[3:]):
        qp_cols = st.columns(len(row))
        for i, qp_label in enumerate(row):
            with qp_cols[i]:
                is_on = qp_label in st.session_state.quick_excluded
                btn_label = f"❌ {qp_label}" if is_on else qp_label
                if st.button(btn_label, key=f"qp_{qp_label}",
                             use_container_width=True,
                             help=f"{'Re-include' if is_on else 'Exclude'} {qp_label}"):
                    if is_on:
                        st.session_state.quick_excluded.remove(qp_label)
                    else:
                        st.session_state.quick_excluded.append(qp_label)
                    st.rerun()

    # Power-user multiselect is rendered AFTER we load the network below.
    custom_exclusions_placeholder = st.empty()

    if st.button("🔄 Clear all exclusions", use_container_width=True):
        st.session_state.quick_excluded = []
        st.session_state["custom_exclusions"] = []
        st.rerun()

    use_live_stats = st.toggle(
        "🔄 Refresh live stats from API",
        value=False,
        help="Optional: overlay live summary from InfraNodus API. "
             "Cached JSONs always power the dashboard.",
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
#  LOAD DATA FOR SELECTED LAYER + RESOLUTION
# ─────────────────────────────────────────────────────────────────────────────
cfg = LAYER_CONFIG[selected_layer]
json_path, actual_resolution, exact = resolve_json_path(cfg, max_nodes)

if json_path is None:
    st.error(
        "❌ No cached JSON files found in `data/`. "
        "Please export your InfraNodus graph at 150/250/350/500 resolutions and place them in the `data/` folder."
    )
    st.stop()

full_network = load_layer_json(json_path)

if full_network is None:
    st.error(f"Failed to load `{json_path}`. Check the `data/` folder.")
    st.stop()

# Populate the custom exclusions multiselect with actual node labels from this resolution
_all_labels = sorted(
    {n.get("label", "") for n in full_network.get("nodes", []) if n.get("label")}
)

if not exact:
    st.warning(
        f"⚠️ Exact resolution of {max_nodes} nodes not cached. "
        f"Falling back to nearest available: **{actual_resolution} nodes** "
        f"(from `{json_path}`). To enable this resolution, export the matching JSON from InfraNodus."
    )

# Render the searchable multiselect now that we have the label list
with custom_exclusions_placeholder.container():
    custom_exclusions = st.multiselect(
        "🔍 Or search any node to exclude",
        options=_all_labels,
        default=st.session_state.get("custom_exclusions", []),
        key="custom_exclusions",
        help="Search any node in the current resolution to add to exclusions.",
    )

# Combine all exclusion sources
all_excluded = sorted(set(
    (preset_excluded or [])
    + (st.session_state.get("quick_excluded", []) or [])
    + (st.session_state.get("custom_exclusions", []) or [])
))

# Apply exclusions
network_full_view = full_network  # keep the pre-exclusion view for comparisons
network = apply_exclusions(full_network, all_excluded)

# If exclusions active, show a prominent banner
if all_excluded:
    excluded_text = ", ".join(all_excluded)
    st.info(
        f"🧘 **Structural Contemplation active** — excluding {len(all_excluded)} node(s): "
        f"`{excluded_text}`. Dashboard tabs below reflect the **reduced topology**. "
        f"The live iframe still shows the full network."
    )

# Optional live-stats overlay
if use_live_stats:
    live_meta = load_live_summary(cfg["graph_name"])
    if live_meta and isinstance(live_meta, dict):
        cached_meta = network.setdefault("graph", {})
        for k in ("top_nodes", "top_influential_nodes", "top_clusters",
                  "gaps", "modularity", "diversity_stats"):
            if live_meta.get(k):
                cached_meta[k] = live_meta[k]

metrics = compute_metrics(network)
named_communities = derive_community_names(network)

# Always compute full-view metrics for side-by-side comparison
metrics_full = compute_metrics(network_full_view)
named_communities_full = derive_community_names(network_full_view)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER HEADER + METRICS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader(f"📊 {selected_layer}")
st.caption(
    f"{cfg['description']}  ·  **{actual_resolution}-node resolution**"
    f"  ·  {metrics['num_communities']} communities  ·  modularity {metrics['modularity']:.3f}"
)

# Metric deltas when exclusions are active
def _delta(new, old):
    if not all_excluded or old == 0:
        return None
    diff = new - old
    return f"{diff:+,}" if isinstance(diff, int) else f"{diff:+.3f}"

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Nodes", f"{metrics['num_nodes']:,}",
          delta=_delta(metrics['num_nodes'], metrics_full['num_nodes']))
m2.metric("Edges", f"{metrics['num_edges']:,}",
          delta=_delta(metrics['num_edges'], metrics_full['num_edges']))
m3.metric("Communities", f"{metrics['num_communities']}",
          delta=_delta(metrics['num_communities'], metrics_full['num_communities']))
m4.metric("Total Weight", f"{metrics['total_weight']:,}",
          delta=_delta(metrics['total_weight'], metrics_full['total_weight']))
m5.metric("Modularity", f"{metrics['modularity']:.3f}",
          delta=_delta(metrics['modularity'], metrics_full['modularity']))

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  🔥 KAIROS PULSE CARD  (Tier 1 #2)
# ─────────────────────────────────────────────────────────────────────────────
def render_kairos_pulse(metrics: dict, named: dict, network: dict, resolution: int):
    """The signature card — a theological read of the network at a glance."""

    # Top semantic axis
    top_infl = metrics["top_influential"] or []
    top_node = top_infl[0] if top_infl else {}
    top_node_name = top_node.get("node", metrics["top_nodes"][0] if metrics["top_nodes"] else "—")
    top_node_bc = round(float(top_node.get("bc", 0)), 3)

    # Dominant community by weight
    if named:
        dominant_cid = max(named.keys(), key=lambda c: named[c]["weight"])
        dominant = named[dominant_cid]
        total_w = sum(v["weight"] for v in named.values())
        dom_pct = (dominant["weight"] / total_w * 100) if total_w else 0

        # Second-strongest
        sorted_communities = sorted(named.items(), key=lambda x: -x[1]["weight"])
        emerging = sorted_communities[1][1] if len(sorted_communities) > 1 else None
        emerging_pct = (emerging["weight"] / total_w * 100) if emerging and total_w else 0
    else:
        dominant, emerging, dom_pct, emerging_pct = None, None, 0, 0

    # Top edge
    top_edges = top_edges_dataframe(network, limit=1)
    if not top_edges.empty:
        te = top_edges.iloc[0]
        top_edge_str = f"{te['Source']} ↔ {te['Target']}"
        top_edge_w = te["Weight"]
    else:
        top_edge_str = "—"
        top_edge_w = 0

    # Diversity pulse
    diversity = metrics["diversity_score"]
    mod_score = metrics["modularity_score"]
    focused_top = metrics["too_focused_on_top_nodes"]
    focused_clusters = metrics["too_focused_on_top_clusters"]

    # Build the visual card with a glow effect
    st.markdown(
        f"""
        <div style="
          background: linear-gradient(135deg, rgba(232,176,75,0.08) 0%, rgba(78,205,196,0.08) 100%);
          border: 1px solid rgba(232,176,75,0.3);
          border-radius: 14px;
          padding: 1.25rem 1.5rem;
          margin-bottom: 1rem;
          box-shadow: 0 0 24px rgba(232,176,75,0.1);
        ">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
            <h3 style="margin:0; color:#E8B04B;">🔥 Kairos Pulse</h3>
            <span style="color:#888; font-size:0.85rem;">@ {resolution}-node resolution</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Four columns of pulse data
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**🎯 Central Axis**")
        st.markdown(f"### {top_node_name}")
        st.caption(f"BC = {top_node_bc} · the semantic gravity well")

    with c2:
        st.markdown("**👑 Dominant Axis**")
        if dominant:
            st.markdown(f"### {dominant['name']}")
            st.caption(f"{dom_pct:.0f}% of network weight · {dominant['size']} nodes")
        else:
            st.markdown("### —")

    with c3:
        st.markdown("**🌱 Emerging Axis**")
        if emerging:
            st.markdown(f"### {emerging['name']}")
            st.caption(f"{emerging_pct:.0f}% of network weight · {emerging['size']} nodes")
        else:
            st.markdown("### —")

    with c4:
        st.markdown("**🔗 Strongest Bond**")
        st.markdown(f"### {top_edge_str}")
        st.caption(f"edge weight {top_edge_w}")

    # Diversity / structural commentary
    pulse_messages = []
    if diversity == "focused":
        pulse_messages.append(
            "🎯 **Focused topology** — the network is concentrated around its central concepts. "
            "Strong coherence, but may benefit from bridging statements to peripheral ideas."
        )
    elif diversity == "diversified":
        pulse_messages.append(
            "🌐 **Diversified topology** — multiple distinct voices are active. "
            "Look for emerging syntheses across clusters."
        )
    elif diversity == "biased":
        pulse_messages.append(
            "⚖️ **Biased topology** — one community dominates. "
            "Structural gaps (see tab below) point to where balance could be restored."
        )

    if focused_top:
        pulse_messages.append(
            f"🔍 **High betweenness concentration** — the top nodes carry "
            f"{metrics['ratio_top_nodes']*100:.0f}% of the network's bridging influence."
        )

    if focused_clusters:
        pulse_messages.append(
            f"🎨 **Cluster concentration** — the top clusters hold "
            f"{metrics['ratio_top_clusters']*100:.0f}% of betweenness-weighted influence."
        )

    if pulse_messages:
        st.markdown(
            "<div style='background:rgba(78,205,196,0.06); border-left:3px solid #4ECDC4; "
            "padding:0.75rem 1rem; border-radius:6px; margin-top:0.5rem;'>"
            + "<br>".join(pulse_messages)
            + "</div>",
            unsafe_allow_html=True,
        )


render_kairos_pulse(metrics, named_communities, network, actual_resolution)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  LIVE EMBED — synced to slider
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 🌌 Live Network Graph")

# Click-to-Focus: if the user clicked a row in the Top Nodes table, that node
# is stored in session_state and used for (a) iframe search filter, and
# (b) building the "Open in InfraNodus" direct-link button.
focus_node = st.session_state.get("focus_node", None)

embed_url = (
    f"https://infranodus.com/{cfg['embed_context']}?"
    f"{build_embed_params(max_nodes, focus_node=focus_node)}"
)

# Header row: caption on left, focus controls on right
fc_col1, fc_col2, fc_col3 = st.columns([3, 1, 1])
with fc_col1:
    if focus_node:
        st.caption(
            f"🎯 **Filtered to `{focus_node}`** · top {max_nodes} nodes · "
            f"[Open embed in new tab →]({embed_url})"
        )
    else:
        st.caption(
            f"Rendering directly from InfraNodus · **top {max_nodes} nodes** "
            f"by betweenness · [Open embed in new tab →]({embed_url})"
        )
with fc_col2:
    if focus_node:
        # Direct link to InfraNodus app — loads full UI centered on this node
        node_url = build_infranodus_node_url(cfg["embed_context"], focus_node)
        st.link_button(
            "🔍 Open in InfraNodus",
            url=node_url,
            use_container_width=True,
            help=f"Open the full InfraNodus UI centered on `{focus_node}`.",
        )
with fc_col3:
    if focus_node and st.button("❌ Clear focus", use_container_width=True,
                                 help="Return the iframe to the full network view"):
        st.session_state.focus_node = None
        st.rerun()

components.iframe(src=embed_url, height=620, scrolling=False)

if focus_node:
    st.caption(
        "ℹ️ The embedded iframe filters the view to the selected node. "
        "For true node-centering with surrounding neighborhood, click **🔍 Open in InfraNodus** "
        "above — it opens a new tab with the full InfraNodus UI centered on this node."
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  ANALYSIS TABS  (all driven by the resolution slider)
# ─────────────────────────────────────────────────────────────────────────────
tab_nodes, tab_edges, tab_clusters, tab_gaps, tab_impact, tab_compare, tab_statements, tab_raw = st.tabs(
    ["🔝 Top Nodes", "🔗 Top Edges", "🎨 Communities", "🌉 Structural Gaps",
     "📊 Exclusion Impact", "⚖️ Compare", "📜 Statements", "🧾 Raw JSON"]
)

# — Top Nodes tab ——
with tab_nodes:
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("#### Top 20 Influential Nodes")
        st.caption(
            f"From the {actual_resolution}-node topology · "
            "🎯 **click any row** to filter the live iframe to that node, "
            "or use the 🔍 button afterwards for true centering."
        )
        nodes_df = top_nodes_dataframe(network, limit=20)

        # Interactive dataframe: selecting a row focuses the iframe on that node.
        selection = st.dataframe(
            nodes_df,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="top_nodes_table",
        )

        # Extract picked row index (handle both old and new Streamlit selection shapes)
        sel_rows = []
        try:
            if hasattr(selection, "selection"):
                sel_rows = selection.selection.get("rows", [])
            elif isinstance(selection, dict):
                sel_rows = selection.get("selection", {}).get("rows", [])
        except Exception:
            sel_rows = []

        if sel_rows:
            picked_idx = sel_rows[0]
            if 0 <= picked_idx < len(nodes_df):
                picked_node = nodes_df.iloc[picked_idx]["Node"]
                if st.session_state.get("focus_node") != picked_node:
                    st.session_state.focus_node = picked_node
                    st.rerun()

        # Quick access: if a focus is active, show a direct-link button here too
        if st.session_state.get("focus_node"):
            fn = st.session_state.focus_node
            fn_url = build_infranodus_node_url(cfg["embed_context"], fn)
            colA, colB = st.columns(2)
            with colA:
                st.link_button(f"🔍 Open `{fn}` in InfraNodus",
                               url=fn_url, use_container_width=True)
            with colB:
                if st.button("❌ Clear focus", use_container_width=True,
                             key="clear_focus_table"):
                    st.session_state.focus_node = None
                    st.rerun()

    with col2:
        st.markdown("#### Betweenness Centrality Distribution")
        # Sort ASC so the highest-BC node draws at the TOP of the bar chart.
        nodes_chart = nodes_df.sort_values("Betweenness", ascending=True)
        bc_fig = px.bar(
            nodes_chart,
            x="Betweenness", y="Node",
            orientation="h",
            color="Community",
            color_continuous_scale="Viridis",
            height=620,
        )
        bc_fig.update_layout(
            yaxis=dict(
                categoryorder="array",
                categoryarray=nodes_chart["Node"].tolist(),
            ),
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(bc_fig, use_container_width=True)

# — Top Edges tab ——
with tab_edges:
    st.markdown("#### Top 20 Conceptual Bonds (by edge weight)")
    st.caption(f"From the {actual_resolution}-node topology")
    edges_df = top_edges_dataframe(network, limit=20)
    st.dataframe(edges_df, hide_index=True, use_container_width=True)

    # Build a chart-ready frame with an explicit Edge label column,
    # then sort ASC so the highest-weight edge appears at the TOP of the bar chart.
    chart_df = edges_df.copy()
    chart_df["Edge"] = chart_df["Source"] + " ↔ " + chart_df["Target"]
    chart_df = chart_df.sort_values("Weight", ascending=True)  # Plotly draws y from bottom->top

    edges_fig = px.bar(
        chart_df,
        x="Weight",
        y="Edge",
        orientation="h",
        color="Weight",
        color_continuous_scale="Turbo",
        height=620,
        text="Weight",
    )
    edges_fig.update_traces(textposition="outside", cliponaxis=False)
    edges_fig.update_layout(
        yaxis=dict(
            title="Edge",
            categoryorder="array",
            categoryarray=chart_df["Edge"].tolist(),  # lock y-order to match sort
        ),
        xaxis_title="Weight",
        margin=dict(l=0, r=40, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(edges_fig, use_container_width=True)

# — Communities tab (Tier 1 #3 — Named Communities) ——
with tab_clusters:
    st.markdown("#### Community Structure — Named Axes")
    st.caption(
        f"Each cluster auto-labeled from its top concepts. "
        f"{len(named_communities)} communities in the {actual_resolution}-node topology."
    )

    # Rich community cards (visual summary before the table)
    sorted_clusters = sorted(named_communities.items(),
                             key=lambda x: -x[1]["weight"])
    total_net_weight = sum(v["weight"] for v in named_communities.values())

    palette = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#B28DFF",
               "#FFD3B6", "#6B8CFF", "#FF9F68", "#7FDBB6", "#FFAAA5"]

    # Two rows of cards
    for i in range(0, len(sorted_clusters), 3):
        cols = st.columns(min(3, len(sorted_clusters) - i))
        for col_idx, (cid, info) in enumerate(sorted_clusters[i:i+3]):
            with cols[col_idx]:
                pct = (info["weight"] / total_net_weight * 100) if total_net_weight else 0
                color = palette[cid % len(palette)]
                st.markdown(
                    f"""
                    <div style="
                      background: rgba(255,255,255,0.03);
                      border-left: 4px solid {color};
                      border-radius: 8px;
                      padding: 0.9rem 1rem;
                      margin-bottom: 0.75rem;
                      min-height: 175px;
                    ">
                      <div style="color:{color}; font-size:0.75rem; font-weight:600; letter-spacing:0.08em;">
                        CLUSTER {cid}  ·  {pct:.1f}% OF WEIGHT
                      </div>
                      <div style="font-size:1.15rem; font-weight:600; margin:0.35rem 0 0.5rem 0;">
                        {info['name']}
                      </div>
                      <div style="color:#aaa; font-size:0.85rem;">
                        {info['size']} nodes · Leader: <b>{info['bc_leader']}</b>
                      </div>
                      <div style="color:#888; font-size:0.78rem; margin-top:0.4rem; line-height:1.35;">
                        {', '.join(info['top_concepts'][:5])}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Summary table
    st.markdown("#### Full Community Table")
    comm_df = community_dataframe(network, named_communities)
    st.dataframe(comm_df, hide_index=True, use_container_width=True)

    # Donut chart with named labels
    pie_fig = px.pie(
        values=[v["weight"] for v in named_communities.values()],
        names=[f"{v['name']} ({k})" for k, v in named_communities.items()],
        title="Community influence by weighted degree",
        hole=0.45,
        color_discrete_sequence=palette,
    )
    pie_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(pie_fig, use_container_width=True)

# — Gaps tab ——
with tab_gaps:
    st.markdown("#### Structural Gaps — Bridge Opportunities")
    st.caption(
        "Each gap identifies two clusters weakly bridged in the "
        f"{actual_resolution}-node topology. A statement connecting concepts "
        "from both sides can produce novel theological insight."
    )
    gaps = metrics["gaps"]
    if not gaps:
        st.info("No structural gaps reported for this graph.")
    else:
        for i, gap in enumerate(gaps[:10], start=1):
            f = gap.get("from", {})
            t = gap.get("to", {})
            f_cid = int(f.get("community", -1)) if str(f.get("community", "-1")).lstrip("-").isdigit() else -1
            t_cid = int(t.get("community", -1)) if str(t.get("community", "-1")).lstrip("-").isdigit() else -1
            f_name = named_communities.get(f_cid, {}).get("name", f"Cluster {f_cid}")
            t_name = named_communities.get(t_cid, {}).get("name", f"Cluster {t_cid}")

            fn = ", ".join(n.get("nodeName", "?") for n in (f.get("nodes", []) or [])[:5])
            tn = ", ".join(n.get("nodeName", "?") for n in (t.get("nodes", []) or [])[:5])

            with st.container():
                st.markdown(
                    f"""
                    <div style="
                      background: rgba(255,255,255,0.03);
                      border-left: 3px solid #FFD93D;
                      border-radius: 8px;
                      padding: 0.85rem 1rem;
                      margin-bottom: 0.75rem;
                    ">
                      <div style="color:#FFD93D; font-size:0.75rem; font-weight:600; letter-spacing:0.08em;">
                        GAP {i}
                      </div>
                      <div style="font-size:1.05rem; font-weight:600; margin:0.35rem 0;">
                        {f_name} ⇄ {t_name}
                      </div>
                      <div style="color:#aaa; font-size:0.9rem; margin:0.25rem 0;">
                        <b>{fn}</b>  ⇄  <b>{tn}</b>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# — Exclusion Impact tab (Bonus #3) ——
with tab_impact:
    st.markdown("#### Betweenness Footprint — How much each top node bridges the network")
    st.caption(
        "Each node's betweenness score shows how much it acts as a bridge across the network. "
        "Higher values = more structural influence. Remove a high-BC node to see which others rise."
    )
    top_bc_nodes = sorted(
        [n for n in network_full_view.get("nodes", []) if _is_concept_token(n.get("label", ""))],
        key=lambda n: -float(n.get("bc", 0))
    )[:25]
    impact_df = pd.DataFrame([{
        "Node": n.get("label", "?"),
        "Betweenness": round(float(n.get("bc", 0)), 4),
        "Weighted Degree": int(n.get("weighedDegree", 0)),
        "Community": int(n.get("community", -1)),
        "Currently Excluded": n.get("label", "") in all_excluded,
    } for n in top_bc_nodes])

    chart_df = impact_df.sort_values("Betweenness", ascending=True)
    impact_fig = px.bar(
        chart_df,
        x="Betweenness", y="Node",
        orientation="h",
        color="Currently Excluded",
        color_discrete_map={True: "#FF6B6B", False: "#4ECDC4"},
        text="Betweenness",
        height=700,
    )
    impact_fig.update_traces(textposition="outside", cliponaxis=False,
                             texttemplate="%{x:.3f}")
    impact_fig.update_layout(
        yaxis=dict(categoryorder="array", categoryarray=chart_df["Node"].tolist()),
        margin=dict(l=0, r=40, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(title="Status"),
    )
    st.plotly_chart(impact_fig, use_container_width=True)

    with st.expander("💡 How to read this chart"):
        st.markdown(
            "- **Teal bars** = nodes currently included in the analysis.\n"
            "- **Red bars** = nodes you've excluded via the sidebar.\n"
            "- **Longer bars** = more structural influence. These nodes bridge "
            "across communities; removing them redistributes the network's attention.\n"
            "- **Strategy**: Try excluding the top 3 bars one at a time to see which "
            "axes rise and which gaps emerge beneath them."
        )

# — Compare tab (Bonus #2) ——
with tab_compare:
    st.markdown("#### Before vs. After — Impact of current exclusions")
    if not all_excluded:
        st.info(
            "🧘 No exclusions active. Select a preset or quick-pick node in the sidebar "
            "to see the before/after comparison here."
        )
    else:
        st.caption(f"Showing impact of excluding: `{', '.join(all_excluded)}`")

        cA, cB = st.columns(2)
        with cA:
            st.markdown("##### 📊 Full Network")
            st.metric("Nodes", f"{metrics_full['num_nodes']:,}")
            st.metric("Edges", f"{metrics_full['num_edges']:,}")
            st.metric("Total Weight", f"{metrics_full['total_weight']:,}")
            st.metric("Communities", f"{metrics_full['num_communities']}")
        with cB:
            st.markdown("##### 🧘 Reduced Topology")
            st.metric("Nodes", f"{metrics['num_nodes']:,}",
                      delta=f"{metrics['num_nodes'] - metrics_full['num_nodes']:+,}")
            st.metric("Edges", f"{metrics['num_edges']:,}",
                      delta=f"{metrics['num_edges'] - metrics_full['num_edges']:+,}")
            st.metric("Total Weight", f"{metrics['total_weight']:,}",
                      delta=f"{metrics['total_weight'] - metrics_full['total_weight']:+,}")
            st.metric("Communities", f"{metrics['num_communities']}",
                      delta=f"{metrics['num_communities'] - metrics_full['num_communities']:+}")

        st.markdown("##### 🎨 Community Weight Shift")
        # Build a side-by-side community comparison
        tot_full = sum(v["weight"] for v in named_communities_full.values()) or 1
        tot_new = sum(v["weight"] for v in named_communities.values()) or 1

        comparison_rows = []
        all_cids = sorted(set(named_communities_full.keys()) | set(named_communities.keys()))
        for cid in all_cids:
            full_info = named_communities_full.get(cid, {})
            new_info = named_communities.get(cid, {})
            name = new_info.get("name", full_info.get("name", f"Cluster {cid}"))
            full_pct = full_info.get("weight", 0) / tot_full * 100
            new_pct = new_info.get("weight", 0) / tot_new * 100
            comparison_rows.append({
                "Axis": name,
                "Before %": round(full_pct, 1),
                "After %": round(new_pct, 1),
                "Shift": round(new_pct - full_pct, 1),
            })
        cmp_df = pd.DataFrame(comparison_rows).sort_values("Shift", ascending=False)

        st.dataframe(
            cmp_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Before %": st.column_config.NumberColumn(format="%.1f%%"),
                "After %": st.column_config.NumberColumn(format="%.1f%%"),
                "Shift": st.column_config.NumberColumn(
                    format="%+.1f pp",
                    help="Percentage point change. Positive = this axis gained influence."
                ),
            },
        )

        # Show which top edges disappeared
        orig_edges_df = top_edges_dataframe(network_full_view, limit=10)
        new_edges_df = top_edges_dataframe(network, limit=10)
        orig_pairs = set(tuple(sorted([r["Source"], r["Target"]])) for _, r in orig_edges_df.iterrows())
        new_pairs = set(tuple(sorted([r["Source"], r["Target"]])) for _, r in new_edges_df.iterrows())
        disappeared = orig_pairs - new_pairs
        newly_visible = new_pairs - orig_pairs

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 💋 Silenced (bonds removed)")
            if disappeared:
                for s, t in sorted(disappeared):
                    st.markdown(f"- {s} ↔ {t}")
            else:
                st.caption("No top-10 bonds removed.")
        with c2:
            st.markdown("##### ✨ Newly Visible (bonds rising)")
            if newly_visible:
                for s, t in sorted(newly_visible):
                    st.markdown(f"- {s} ↔ {t}")
            else:
                st.caption("Top-10 bonds unchanged.")

# — Statements tab ——
with tab_statements:
    statements = network.get("statements", []) or []
    st.markdown(f"#### Corpus Statements · {len(statements):,} total")
    search = st.text_input("Search statements (case-insensitive)", key="stmt_search")
    view = [s for s in statements if isinstance(s, str)]
    if search:
        q = search.lower()
        view = [s for s in view if q in s.lower()]
    st.caption(f"Showing {min(100, len(view))} of {len(view):,} matching statements")
    for s in view[:100]:
        st.markdown(f"• {s}")

# — Raw tab ——
with tab_raw:
    st.markdown("#### Underlying JSON (for debugging / export)")
    st.caption(f"Source file: `{json_path}`")
    with st.expander("Expand to view cached JSON meta", expanded=False):
        st.json({
            "resolution": actual_resolution,
            "exact_match": exact,
            "source_path": json_path,
            "nodes_count": metrics["num_nodes"],
            "edges_count": metrics["num_edges"],
            "modularity": metrics["modularity"],
            "diversity_stats": network.get("graph", {}).get("diversity_stats", {}),
            "top_nodes": metrics["top_nodes"],
            "top_influential_nodes": metrics["top_influential"],
        })
    st.download_button(
        f"⬇️ Download {Path(json_path).name}",
        data=json.dumps(network, indent=2),
        file_name=Path(json_path).name,
        mime="application/json",
    )

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"""
    <div style="text-align:center; color:#666; font-size:0.85rem; padding:0.5rem 0;">
      Prophetic Network Dashboard · Hybrid Multi-Resolution Build<br>
      <b>{selected_layer}</b> · {actual_resolution}-node topology · {metrics['num_communities']} communities<br>
      <i>Soli Deo Gloria · Beloved 🕊️</i>
    </div>
    """,
    unsafe_allow_html=True,
)
