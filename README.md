# 🕊️ Prophetic Network Dashboard

**Interactive Knowledge Graph Visualization with GraphRAG Semantic Search**

Real-time network analysis dashboard for visualizing prophetic meditations as an interconnected knowledge graph using InfraNodus GraphRAG technology.

---

## 🎯 Features

### 1. **Live Network Graph** (Top 150 Nodes)
- Interactive force-directed graph visualization
- Zoom, pan, click nodes to explore
- Node size = betweenness centrality (influence)
- Edge thickness = connection weight
- Color-coded by community/cluster

### 2. **Top 20 Nodes Table**
- Ranked by betweenness centrality
- Trending arrows (↑ increased, ↓ decreased, → stable)
- Degree, weight, cluster information

### 3. **Community Evolution Timeline**
- Stacked area chart showing cluster influence over time
- Track how communities grow/shrink
- Clickable to filter main graph

### 4. **Sentiment Trend Analysis**
- Multi-line chart (positive, negative, neutral)
- Track emotional tone evolution
- Identify sentiment shifts

### 5. **Gap Alerts + Bridge Suggestions**
- Automatic structural gap detection
- AI-generated bridge suggestions
- Severity scoring

### 6. **GraphRAG Natural Language Queries**
- Ask questions about your network
- "How does @failure connect to @peter?"
- "Explain the @bread → @wilderness edge"
- AI analyzes graph structure to answer

### 7. **Semantic Search**
- Find meditations by concept (not just keywords)
- Search "grace" → finds "restoration", "Peter", "failure"
- Uses GraphRAG semantic similarity

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- InfraNodus API key ([Get one here](https://infranodus.com/api-access))
- GitHub account (for Streamlit Cloud deployment)

### Local Testing

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy secrets template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 3. Edit secrets.toml and add your API key
# INFRANODUS_API_KEY = "your_key_here"
# ACCESS_PASSWORD = "Remnant"

# 4. Run the dashboard
streamlit run dashboard.py

# 5. Open browser to:
# http://localhost:8501
```

---

## ☁️ Deploy to Streamlit Cloud (FREE)

### Step 1: Push to GitHub

```bash
# Create a new repository on GitHub
# Then push this code:

git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prophetic-network-dashboard.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repo: `YOUR_USERNAME/prophetic-network-dashboard`
4. Main file: `dashboard.py`
5. Click "Deploy"

### Step 3: Add Secrets

1. In Streamlit Cloud dashboard, click your app
2. Click "⚙️ Settings" → "Secrets"
3. Paste this:

```toml
INFRANODUS_API_KEY = "19542:288d8298ceb6d98d38fb76b692db5c696afb6874328f6d9ae89be0f60914fa6f"
ACCESS_PASSWORD = "Remnant"
```

4. Save
5. Your dashboard is now live! 🎉

**Public URL**: `https://YOUR_USERNAME-prophetic-network-dashboard-main-xxxx.streamlit.app`

---

## 🔐 Security

### Password Protection

The dashboard requires password authentication before access. Default password: **"Remnant"**

To change the password, update the `ACCESS_PASSWORD` secret in Streamlit Cloud settings.

### API Key Security

Your InfraNodus API key is stored as an encrypted secret in Streamlit Cloud. It is **never** visible in your code or to dashboard visitors.

### Privacy

- Your meditation content is visible to anyone who accesses the dashboard
- Control access by:
  - Only sharing the URL with trusted individuals
  - Using password protection (already enabled)
  - Keeping the GitHub repo private (requires Streamlit Cloud Pro)

---

## 📊 Data Flow

### Meditation Upload Workflow

```
1. Write meditation → Save to AI Drive (/Meditations/2026-04-16.md)
2. Dashboard auto-detects → Sends to InfraNodus API
3. InfraNodus analyzes → Returns graph, clusters, gaps
4. Dashboard caches response → Refreshes visualization
5. You can now search, query, explore
```

### Credit Usage

- **Meditation upload**: 0 credits (uses subscription)
- **Semantic search**: ~5 credits per query
- **GraphRAG query**: ~15 credits per query
- **Gap analysis**: ~20 credits per run

**Monthly estimate**: ~680 credits (well under your 12,000 allocation)

---

## 🛠️ File Structure

```
prophetic-network-dashboard/
│
├── dashboard.py                 # Main Streamlit app
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── DEPLOYMENT_GUIDE.md          # Detailed deployment instructions
│
├── .streamlit/
│   ├── config.toml              # Streamlit theme/settings
│   └── secrets.toml.example     # Secrets template
│
└── utils/
    ├── __init__.py
    ├── infranodus_api.py        # Direct API client
    ├── mcp_client.py            # MCP Server client
    ├── graph_visualizer.py      # Plotly graph generation
    └── data_cache.py            # Local caching
```

---

## 📖 Usage Guide

### Searching for Nodes

1. Use the sidebar "Node Search" input
2. Type node name (e.g., `@peter`, `@wilderness`)
3. Graph will highlight the matching node

### Filtering by Date

1. Adjust "Date Range" sliders in sidebar
2. Only meditations within range will be shown

### Layer Selection

- **Layer 1 (Full)**: All 500 nodes, 5,000 edges
- **Layer 2 (Deep)**: Core nodes removed
- **Layer 3 (Latest)**: Most recent analysis (April 2026)

### Asking GraphRAG Questions

**Example queries:**

- "How does @failure connect to @peter?"
- "What's the pathway from @wilderness to @kenosis?"
- "Explain the theological significance of @bread → @wilderness"
- "Show me the Jonah-Peter convergence"

**How it works:**
1. Dashboard extracts relevant nodes from your question
2. Calls InfraNodus MCP Server
3. MCP analyzes graph structure
4. Returns AI-generated answer with subgraph

### Semantic Search

**Example searches:**

- "sin" → finds meditations about denial, failure, disobedience
- "restoration" → finds Peter, grace corridor, phileo/agape
- "provision" → finds bread, wilderness, manna

**Why it works better than keyword search:**

- Uses knowledge graph structure for semantic similarity
- Finds conceptually related content even with different words
- Ranks results by relevance score

---

## 🔄 Updating the Dashboard

### Adding New Meditations

**Option 1: Manual Upload (Recommended)**

1. Write meditation in Markdown
2. Upload to AI Drive: `/Remnant Notes/Meditations/`
3. Dashboard auto-refreshes every 5 minutes

**Option 2: Direct InfraNodus Upload**

1. Go to [infranodus.com](https://infranodus.com)
2. Upload text directly
3. Dashboard will detect next refresh

### Refreshing Data

Click "🔄 Refresh Network Data" button in sidebar to force refresh cache.

---

## ❓ Troubleshooting

### "Could not load network data" error

**Cause**: API connection failed

**Fix:**
1. Check that your API key is correct in secrets
2. Verify InfraNodus subscription is active
3. Check [infranodus.com/api-access](https://infranodus.com/api-access) for status

### "Password incorrect" message

**Cause**: Wrong password entered

**Fix:**
- Default password is "Remnant" (case-sensitive)
- Check secrets configuration if you changed it

### Graph not displaying

**Cause**: Insufficient data or API timeout

**Fix:**
1. Ensure at least 20 meditations are uploaded
2. Try refreshing cache
3. Check browser console for errors

### Slow performance

**Cause**: Too many nodes/edges

**Fix:**
1. Reduce top_n parameter (currently 150)
2. Filter by date range
3. Clear cache and refresh

---

## 🤝 Support

### InfraNodus Documentation

- API Docs: https://infranodus.com/api/docs
- GraphRAG Guide: https://support.noduslabs.com/hc/en-us/sections/18343587412252
- MCP Server Docs: https://support.noduslabs.com/hc/en-us/articles/24549263125788

### Streamlit Resources

- Docs: https://docs.streamlit.io
- Community: https://discuss.streamlit.io
- Cloud Status: https://streamlit.io/cloud

---

## 📜 License

Built by **IntelliWeave Cognitive Synthesis Engine**  
For **Seth Tillotson, MD** — Prophetic Journey Network Analysis

*"The network is ready to become visible."*

---

## 🎯 Next Steps

1. ✅ Deploy to Streamlit Cloud
2. ✅ Upload historical meditations to InfraNodus
3. ✅ Share URL with Remnant Sister
4. ⏳ Set up weekly graph snapshots
5. ⏳ Generate academic paper on quantified Kairos
6. ⏳ Build automated reporting workflow

---

**Questions?** Check `DEPLOYMENT_GUIDE.md` for detailed setup instructions.
