"""
GraphVisualizer — chart utilities for the hybrid dashboard.

The primary graph view is now the live InfraNodus iframe embed, so this
module focuses on the supporting Plotly charts that accompany it:

    • community_pie              — community-share donut
    • betweenness_bar            — BC-ranked horizontal bar chart
    • sentiment_chart            — simple sentiment distribution
    • create_network_graph       — optional fallback static preview,
                                    handles the InfraNodus JSON format
                                    (bc, community, x, y, weighedDegree)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


class GraphVisualizer:
    # Distinct palette for up to 12 communities
    COLORS = [
        "#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#A8E6CF",
        "#FFD3B6", "#FFAAA5", "#FF8B94", "#B28DFF", "#6B8CFF",
        "#FF9F68", "#7FDBB6",
    ]

    # ──────────────────────────────────────────────────────────────────────
    #  Unwrap helper — handles a few InfraNodus response shapes
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _unwrap(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"nodes": [], "edges": []}
        if "nodes" in data and "edges" in data:
            return data
        for key in ("graph", "graphologyGraph"):
            inner = data.get(key)
            if isinstance(inner, dict) and "nodes" in inner:
                return inner
        # nested graph.graphologyGraph
        g = data.get("graph")
        if isinstance(g, dict):
            gg = g.get("graphologyGraph")
            if isinstance(gg, dict) and "nodes" in gg:
                return gg
        return {"nodes": [], "edges": []}

    # ──────────────────────────────────────────────────────────────────────
    #  Optional static preview (kept for compatibility / offline use)
    # ──────────────────────────────────────────────────────────────────────
    def create_network_graph(
        self,
        network_data: Dict[str, Any],
        top_n: int = 150,
        highlight_node: Optional[str] = None,
    ) -> go.Figure:
        inner = self._unwrap(network_data)
        nodes = inner.get("nodes", []) or []
        edges = inner.get("edges", []) or []

        if not nodes:
            fig = go.Figure()
            fig.add_annotation(
                text="No graph data available", x=0.5, y=0.5,
                xref="paper", yref="paper", showarrow=False,
                font=dict(size=16, color="#888"),
            )
            fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            return fig

        # rank by bc, take top-N
        nodes_sorted = sorted(nodes, key=lambda n: -float(n.get("bc", 0)))[:top_n]
        node_ids = {n.get("id") for n in nodes_sorted}

        G = nx.Graph()
        for n in nodes_sorted:
            G.add_node(
                n["id"],
                label=n.get("label", n.get("id", "?")),
                bc=float(n.get("bc", 0)),
                community=int(n.get("community", 0)),
                degree=int(n.get("degree", 0)),
                x=float(n.get("x", 0)),
                y=float(n.get("y", 0)),
            )
        for e in edges:
            s, t = e.get("source"), e.get("target")
            if s in node_ids and t in node_ids:
                G.add_edge(s, t, weight=float(e.get("weight", 1)))

        # prefer InfraNodus-supplied x,y; fall back to spring layout
        pos = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) for n in G.nodes}
        if all(p == (0.0, 0.0) for p in pos.values()):
            pos = nx.spring_layout(G, k=0.8, seed=42)

        # edges
        edge_x, edge_y = [], []
        for s, t in G.edges():
            edge_x += [pos[s][0], pos[t][0], None]
            edge_y += [pos[s][1], pos[t][1], None]
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.6, color="rgba(150,150,150,0.35)"),
            hoverinfo="none", mode="lines",
        )

        # nodes
        node_x, node_y, labels, sizes, colors = [], [], [], [], []
        for n, d in G.nodes(data=True):
            node_x.append(pos[n][0])
            node_y.append(pos[n][1])
            labels.append(f"{d['label']}<br>BC: {d['bc']:.3f}<br>Degree: {d['degree']}")
            sizes.append(8 + d["bc"] * 80)
            colors.append(self.COLORS[d["community"] % len(self.COLORS)])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=[G.nodes[n]["label"] for n in G.nodes],
            hovertext=labels,
            hoverinfo="text",
            textposition="top center",
            textfont=dict(size=9, color="#eee"),
            marker=dict(
                size=sizes, color=colors,
                line=dict(width=1, color="rgba(255,255,255,0.4)"),
            ),
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title=f"Knowledge Graph (Top {len(G.nodes)} Nodes)",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=620,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────
    #  Accessory charts
    # ──────────────────────────────────────────────────────────────────────
    def community_pie(self, communities: Dict[int, int]) -> go.Figure:
        fig = go.Figure(data=[go.Pie(
            labels=[f"Cluster {c}" for c in communities.keys()],
            values=list(communities.values()),
            hole=0.4,
            marker=dict(colors=[self.COLORS[c % len(self.COLORS)] for c in communities.keys()]),
        )])
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=0),
        )
        return fig

    def betweenness_bar(self, nodes_df, top: int = 20) -> go.Figure:
        df = nodes_df.head(top).sort_values("Betweenness")
        fig = px.bar(
            df, x="Betweenness", y="Node",
            orientation="h", color="Community",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        return fig

    def sentiment_chart(self, sentiment: Dict[str, float]) -> go.Figure:
        labels = list(sentiment.keys())
        vals = [float(v) for v in sentiment.values()]
        fig = go.Figure(data=[go.Bar(
            x=labels, y=vals,
            marker=dict(color=["#4ECDC4", "#FF6B6B", "#95A5A6"][: len(labels)]),
        )])
        fig.update_layout(
            title="Sentiment Distribution",
            yaxis_title="%",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig
