"""
PROPHETIC NETWORK DASHBOARD
Interactive knowledge graph visualization with GraphRAG semantic search

Features:
1. Live network graph (top 150 nodes, all edges)
2. Top 20 nodes table with trending arrows
3. Community evolution timeline
4. Sentiment trend analysis
5. Gap alerts + bridge suggestions
6. GraphRAG natural language queries
7. Semantic search

Author: IntelliWeave Cognitive Synthesis Engine
For: Seth Tillotson, MD - Prophetic Journey Network Analysis
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Import utility modules
from utils.infranodus_api import InfraNodusAPI
from utils.mcp_client import MCPClient
from utils.graph_visualizer import GraphVisualizer
from utils.data_cache import DataCache

# Page configuration
st.set_page_config(
    page_title="Prophetic Network Dashboard",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .gap-alert {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .search-result {
        background: #f8f9fa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        border-left: 3px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    """Password authentication gate"""
    
    def password_entered():
        """Check if password is correct"""
        if st.session_state["password"] == st.secrets["ACCESS_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show password input
        st.markdown('<h1 class="main-header">🕊️ Prophetic Network Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("### 🔐 Authentication Required")
        st.text_input(
            "Enter Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.info("**For Remnant Access Only** — Enter the password to continue")
        return False
    
    elif not st.session_state["password_correct"]:
        # Password incorrect
        st.markdown('<h1 class="main-header">🕊️ Prophetic Network Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("### 🔐 Authentication Required")
        st.text_input(
            "Enter Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("❌ Incorrect password. Try again.")
        return False
    
    else:
        # Password correct
        return True

# Check authentication first
if not check_password():
    st.stop()

# ============================================================================
# INITIALIZE SERVICES
# ============================================================================

@st.cache_resource
def init_services():
    """Initialize API clients and cache"""
    api_key = st.secrets["INFRANODUS_API_KEY"]
    
    infranodus = InfraNodusAPI(api_key)
    mcp = MCPClient(api_key)
    cache = DataCache()
    visualizer = GraphVisualizer()
    
    return infranodus, mcp, cache, visualizer

infranodus_api, mcp_client, data_cache, graph_viz = init_services()

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_network_data(layer_name):
    """Load network data from cache or API"""
    
    # Try to load from cache first
    cached = data_cache.get(f"network_{layer_name}")
    if cached:
        return cached
    
    # If not in cache, fetch from API
    with st.spinner("Loading network data from InfraNodus..."):
        try:
            response = infranodus_api.get_graph_and_statements(
                graph_name="prophetic_meditations",
                add_stats=True,
                include_graph=True,
                include_graph_summary=True,
                gap_depth=2
            )
            
            # Cache the response
            data_cache.set(f"network_{layer_name}", response)
            return response
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None

# Load data based on selected layer
network_data = load_network_data(layer)

if not network_data:
    st.error("⚠️ Could not load network data. Please check API connection.")
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
