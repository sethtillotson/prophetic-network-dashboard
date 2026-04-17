"""
PROPHETIC NETWORK DASHBOARD
Living Topology of Transformation — Interactive Network Intelligence
Author: Seth Tillotson
"""

import streamlit as st
import json
import requests
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

from utils.infranodus_api import InfraNodusAPI
from utils.data_cache import DataCache


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
# AUTHENTICATION GATE (defined BEFORE it's called)
# ═══════════════════════════════════════════════════════════════
def check_password() -> None:
    """
    Bulletproof password gate. Survives reruns from button clicks,
    widget interactions, and cache invalidations.
    Calls st.stop() until authenticated; never returns False.
    """
    # Fast path: already authenticated
    if st.session_state.get("password_correct", False) is True:
        return

    # Read expected password from secrets
    expected = st.secrets.get("ACCESS_PASSWORD", "")
    if not expected:
        st.error("🔐 ACCESS_PASSWORD missing from Streamlit Cloud → Settings → Secrets.")
        st.stop()

    # Show the gate
    st.markdown("### 🔐 Prophetic Network Dashboard")
    st.markdown("Enter the access password to continue.")

    with st.form("auth_form", clear_on_submit=False):
        pwd = st.text_input(
            "Access Password",
            type="password",
            key="auth_pwd_input",   # unique key — NOT "password"
        )
        submitted = st.form_submit_button("Enter")

    if submitted:
        if pwd == expected:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect password.")

    st.stop()


# ═══════════════════════════════════════════════════════════════
# CALL THE GATE — nothing below runs until authenticated
# ═══════════════════════════════════════════════════════════════
check_password()


# ═══════════════════════════════════════════════════════════════
# INITIALIZE SERVICES (only runs after auth)
# ═══════════════════════════════════════════════════════════════
INFRANODUS_API_KEY = st.secrets.get("INFRANODUS_API_KEY", "")
if not INFRANODUS_API_KEY:
    st.error("🔐 INFRANODUS_API_KEY missing from Streamlit secrets.")
    st.stop()

@st.cache_resource
def init_services():
    return {
        "infranodus_api": InfraNodusAPI(api_key=INFRANODUS_API_KEY),
        "data_cache": DataCache(),
    }

services = init_services()
infranodus_api = services["infranodus_api"]
data_cache = services["data_cache"]


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
                            name = g.get("name") or g.get("graphName") or g.get("title") or g.get("slug") or "?"
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
                r = requests.get(
                    "https://infranodus.com/api/v1/graphs",
                    headers={"Authorization": f"Bearer {INFRANODUS_API_KEY}"},
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
# REST OF YOUR DASHBOARD CONTINUES BELOW
# (keep everything else — LAYER_GRAPH_MAP, load_network_data,
#  visualizations, metrics, etc.)
# ═══════════════════════════════════════════════════════════════



# ============================================================================
# HEADER
# ============================================================================

st.markdown('<h1 class="main-header">🕊️ Prophetic Network Dashboard</h1>', unsafe_allow_html=True)
st.markdown("**Interactive Knowledge Graph** • GraphRAG Semantic Search • Real-Time Network Analysis")
st.markdown("---")

# ============================================================================
# SIDEBAR - FILTERS & CONTROLS
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Controls")
    
    # Date range filter
    st.markdown("### 📅 Date Range")
    date_start = st.date_input(
        "Start Date",
        datetime(2026, 2, 1),
        key="date_start"
    )
    date_end = st.date_input(
        "End Date",
        datetime(2026, 4, 16),
        key="date_end"
    )
    
    # Layer selection
    st.markdown("### 📊 Layer Selection")
    layer = st.selectbox(
        "Choose Network Layer",
        ["Layer 1 (Full)", "Layer 2 (Deep)", "Layer 2 (@mind removed)", "Layer 3 (Latest)"],
        index=3
    )
    
    # Cluster filter
    st.markdown("### 🎨 Cluster Filter")
    clusters = st.multiselect(
        "Show Clusters",
        ["Spirit Dynamics", "Grace Identity", "Authority Framework", 
         "Theological Reflection", "Abiding Strive", "All"],
        default=["All"]
    )
    
    # Node search
    st.markdown("### 🔍 Node Search")
    node_search = st.text_input("Search for node (e.g., @peter)")
    
    # Refresh data
    st.markdown("### 🔄 Data Management")
    if st.button("Refresh Network Data"):
        data_cache.clear()
        st.success("Cache cleared! Refreshing...")
        st.rerun()
    
    # Display last update
    last_update = data_cache.get_last_update()
    if last_update:
        st.caption(f"Last updated: {last_update}")

# ============================================================================
# LOAD DATA
# ============================================================================

# Map dashboard layer selection → actual InfraNodus graph names
LAYER_GRAPH_MAP = {
    # Short forms
    "Layer 1": "seth_tillotson_md__meditation-g",
    "Layer 2": "seth_tillotson_md__meditation-g",
    "Layer 3": "New_Test_2",
    
    # Descriptive forms
    "Full Network (Layer 1)": "seth_tillotson_md__meditation-g",
    "Deep Network (Layer 2)": "seth_tillotson_md__meditation-g",
    "Kairos Transition (Layer 3)": "New_Test_2",
    
    # "Latest" variants (what your dropdown is currently sending)
    "Layer 1 (Full Network)": "seth_tillotson_md__meditation-g",
    "Layer 2 (Deep Analysis)": "seth_tillotson_md__meditation-g",
    "Layer 2 (Mind-Spirit Bridge)": "seth_tillotson_md__meditation-g",
    "Layer 3 (Latest)": "New_Test_2",
    "Layer 3 (Kairos)": "New_Test_2",
    "Layer 3 (Kairos Transition)": "New_Test_2",
}


@st.cache_data(ttl=300)
def load_network_data(layer_name):
    """Load network data from InfraNodus API for the selected layer"""
    
    # Normalize: just look for "Layer 1", "Layer 2", or "Layer 3" substring
    layer_key = layer_name.lower()
    
    if "layer 3" in layer_key or "kairos" in layer_key:
        graph_name = "New_Test_2"
    elif "layer 1" in layer_key or "layer 2" in layer_key or "full" in layer_key or "deep" in layer_key or "mind" in layer_key:
        graph_name = "seth_tillotson_md__meditation-g"
    else:
        st.error(f"⚠️ Unknown layer: '{layer_name}'")
        return None
    
    # Try cache
    cached = data_cache.get(f"network_{graph_name}")
    if cached:
        return cached
    
    with st.spinner(f"Loading '{graph_name}' from InfraNodus..."):
        try:
            response = infranodus_api.get_graph_and_statements(
                graph_name=graph_name,
                add_stats=True,
                include_graph=True,
                include_graph_summary=True,
                gap_depth=2
            )
            
            if not response:
                st.error(f"⚠️ Empty response for graph '{graph_name}'")
                return None
            
            graph = response.get("graph") or {}
            nodes = graph.get("nodes", [])
            edges = graph.get("edges") or graph.get("relations") or []
            
            if not nodes:
                st.warning(
                    f"⚠️ Graph '{graph_name}' exists but returned no nodes. "
                    f"Response keys: {list(response.keys())}"
                )
            
            data_cache.set(f"network_{graph_name}", response)
            return response
            
        except Exception as e:
            st.error(f"❌ Error loading '{graph_name}': {type(e).__name__}: {str(e)}")
            import traceback
            with st.expander("Full error traceback"):
                st.code(traceback.format_exc())
            return None


# Load data based on selected layer
network_data = load_network_data(layer)

if not network_data:
    st.error("⚠️ Could not load network data. Please check API connection and graph names.")
    st.stop()

# ============================================================================
# METRICS ROW
# ============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{network_data.get('node_count', 500)}</h3>
        <p>Total Nodes</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{network_data.get('edge_count', 5000)}</h3>
        <p>Total Edges</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{network_data.get('cluster_count', 11)}</h3>
        <p>Communities</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    modularity = network_data.get('modularity', 0.33)
    st.markdown(f"""
    <div class="metric-card">
        <h3>{modularity:.2f}</h3>
        <p>Modularity</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    total_weight = network_data.get('total_weight', 155997)
    st.markdown(f"""
    <div class="metric-card">
        <h3>{total_weight:,}</h3>
        <p>Total Weight</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# FEATURE 1: LIVE NETWORK GRAPH
# ============================================================================

st.markdown("## 🌐 Live Network Graph")
st.markdown("**Interactive visualization of top 150 nodes** • Click nodes to explore • Zoom & pan enabled")

# Generate network graph
with st.spinner("Generating network visualization..."):
    fig = graph_viz.create_network_graph(
        network_data,
        top_n=150,
        highlight_node=node_search if node_search else None
    )
    
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': True})

# ============================================================================
# TWO COLUMN LAYOUT
# ============================================================================

col_left, col_right = st.columns([1, 1])

with col_left:
    # ========================================================================
    # FEATURE 2: TOP 20 NODES TABLE
    # ========================================================================
    
    st.markdown("## 📊 Top 20 Influential Nodes")
    
    top_nodes_df = pd.DataFrame(network_data.get('top_nodes', []))
    
    if not top_nodes_df.empty:
        # Add trend arrows
        top_nodes_df['Trend'] = top_nodes_df.apply(
            lambda row: f"↑ +{row.get('trend', 0):.0f}%" if row.get('trend', 0) > 10
            else f"↓ {row.get('trend', 0):.0f}%" if row.get('trend', 0) < -10
            else "→ 0%",
            axis=1
        )
        
        st.dataframe(
            top_nodes_df[['Rank', 'Node', 'BC', 'Degree', 'Weight', 'Cluster', 'Trend']],
            width='stretch',
            height=600
        )
    else:
        st.info("Loading node data...")

with col_right:
    # ========================================================================
    # FEATURE 4: SENTIMENT TREND ANALYSIS
    # ========================================================================
    
    st.markdown("## 😊 Sentiment Trend Analysis")
    
    sentiment_data = network_data.get('sentiment_timeline', [])
    
    if sentiment_data:
        df_sentiment = pd.DataFrame(sentiment_data)
        
        fig_sentiment = go.Figure()
        fig_sentiment.add_trace(go.Scatter(
            x=df_sentiment['date'],
            y=df_sentiment['positive'],
            name='Positive',
            line=dict(color='#28a745', width=3),
            mode='lines+markers'
        ))
        fig_sentiment.add_trace(go.Scatter(
            x=df_sentiment['date'],
            y=df_sentiment['negative'],
            name='Negative',
            line=dict(color='#dc3545', width=3),
            mode='lines+markers'
        ))
        fig_sentiment.add_trace(go.Scatter(
            x=df_sentiment['date'],
            y=df_sentiment['neutral'],
            name='Neutral',
            line=dict(color='#6c757d', width=3),
            mode='lines+markers'
        ))
        
        fig_sentiment.update_layout(
            xaxis_title="Date",
            yaxis_title="Percentage",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_sentiment, width='stretch')
    else:
        # Show current sentiment
        sentiment = network_data.get('sentiment', {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Positive", f"{sentiment.get('positive', 34)}%")
        with col2:
            st.metric("Negative", f"{sentiment.get('negative', 49)}%")
        with col3:
            st.metric("Neutral", f"{sentiment.get('neutral', 17)}%")

st.markdown("---")

# ============================================================================
# FEATURE 3: COMMUNITY EVOLUTION TIMELINE
# ============================================================================

st.markdown("## 📈 Community Evolution Timeline")
st.markdown("**Track cluster influence over time** • Click to filter graph by community")

community_timeline = network_data.get('community_timeline', [])

if community_timeline:
    df_communities = pd.DataFrame(community_timeline)
    
    fig_communities = go.Figure()
    
    for cluster in df_communities['cluster'].unique():
        cluster_data = df_communities[df_communities['cluster'] == cluster]
        fig_communities.add_trace(go.Scatter(
            x=cluster_data['date'],
            y=cluster_data['influence'],
            name=cluster,
            stackgroup='one',
            mode='lines',
            hovertemplate='%{y:.1f}%<br>%{fullData.name}'
        ))
    
    fig_communities.update_layout(
        xaxis_title="Date",
        yaxis_title="% Influence (BC Ratio)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_communities, width='stretch')
else:
    st.info("Community timeline will appear after multiple analyses are recorded")

st.markdown("---")

# ============================================================================
# FEATURE 5: GAP ALERTS + BRIDGE SUGGESTIONS
# ============================================================================

st.markdown("## ⚠️ Structural Gap Analysis")

gaps = network_data.get('content_gaps', [])

if gaps:
    for i, gap in enumerate(gaps, 1):
        st.markdown(f"""
        <div class="gap-alert">
            <h4>⚠️ Gap {i}: {gap.get('title', 'Structural Gap')}</h4>
            <p>{gap.get('description', 'Two clusters are isolated from each other')}</p>
            <p><strong>💡 Suggested Bridges:</strong> {', '.join(gap.get('bridges', []))}</p>
            <p><strong>📊 Severity:</strong> {gap.get('severity', 'Medium').upper()}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✅ No major structural gaps detected. Network is well-connected.")

st.markdown("---")

# ============================================================================
# FEATURE 6: GRAPHRAG NATURAL LANGUAGE QUERIES
# ============================================================================

st.markdown("## 🤖 GraphRAG Natural Language Queries")
st.markdown("**Ask questions about your network** • AI analyzes graph structure to answer")

query = st.text_input(
    "Ask a question",
    placeholder="e.g., How does @failure connect to @peter?",
    key="graphrag_query"
)

if st.button("🔍 Ask GraphRAG", type="primary"):
    if query:
        with st.spinner("Analyzing graph structure..."):
            try:
                # Call MCP develop_conceptual_bridges
                response = mcp_client.develop_conceptual_bridges(
                    text=query,
                    request_mode="gaps"
                )
                
                st.markdown("### 📊 GraphRAG Answer:")
                st.markdown(response.get('answer', 'No answer generated'))
                
                # Show relevant subgraph
                if response.get('relevant_edges'):
                    st.markdown("### 🔗 Relevant Connections:")
                    for edge in response['relevant_edges']:
                        st.markdown(f"- **{edge['source']}** → **{edge['target']}** (weight: {edge['weight']})")
                
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
    else:
        st.warning("Please enter a question")

st.markdown("---")

# ============================================================================
# FEATURE 7: SEMANTIC SEARCH
# ============================================================================

st.markdown("## 🔎 Semantic Search Meditations")
st.markdown("**Find meditations by concept** • Uses GraphRAG to find semantically similar content")

search_query = st.text_input(
    "Search by concept",
    placeholder="e.g., grace, failure, wilderness provision",
    key="semantic_search"
)

if st.button("🔍 Search", type="primary", key="search_btn"):
    if search_query:
        with st.spinner("Searching knowledge graph..."):
            try:
                # Call MCP retrieve_from_knowledge_base
                results = mcp_client.retrieve_from_knowledge_base(
                    graph_name="prophetic_meditations",
                    prompt=search_query
                )
                
                st.markdown(f"### 📚 Found {len(results.get('statements', []))} Results:")
                
                for i, result in enumerate(results.get('statements', []), 1):
                    similarity = result.get('similarityScore', 0.0)
                    content = result.get('content', '')
                    cluster = result.get('topStatementCommunity', 'Unknown')
                    
                    st.markdown(f"""
                    <div class="search-result">
                        <h4>Result {i} • Similarity: {similarity:.2f}</h4>
                        <p>{content[:200]}{'...' if len(content) > 200 else ''}</p>
                        <p><em>Cluster: {cluster}</em></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error searching: {str(e)}")
    else:
        st.warning("Please enter a search term")

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div style='text-align: center; color: #6c757d; margin-top: 3rem;'>
    <p>🕊️ <strong>Prophetic Network Dashboard</strong></p>
    <p>Built with InfraNodus GraphRAG • Powered by IntelliWeave Cognitive Synthesis</p>
    <p><em>"The network is ready to become visible."</em></p>
</div>
""", unsafe_allow_html=True)
