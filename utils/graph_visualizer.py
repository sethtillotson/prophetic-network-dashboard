"""
Network Graph Visualizer
Creates interactive Plotly visualizations of knowledge graphs
Hardened for InfraNodus field-name variations
"""

import plotly.graph_objects as go
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any


class GraphVisualizer:
    """Interactive network graph visualization with Plotly"""

    def __init__(self):
        self.color_scale = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe',
            '#00f2fe', '#43e97b', '#38f9d7', '#fa709a',
            '#fee140', '#30cfd0', '#a8edea',
        ]

    @staticmethod
    def _node_id(node: Dict) -> str:
        """Extract a stable node identifier (InfraNodus uses 'name' primarily)."""
        return (
            node.get('name') or node.get('id') or node.get('label')
            or node.get('uid') or ''
        )

    @staticmethod
    def _node_label(node: Dict) -> str:
        """Extract a display label."""
        return (
            node.get('label') or node.get('name') or node.get('id') or '?'
        )

    @staticmethod
    def _node_bc(node: Dict) -> float:
        """Extract betweenness centrality — InfraNodus uses 'bc' or 'bc2'."""
        for key in ('bc2', 'bc', 'betweenness', 'betweenness_centrality'):
            v = node.get(key)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
        return 0.0

    @staticmethod
    def _node_cluster(node: Dict) -> int:
        """Extract cluster/community id."""
        for key in ('cluster', 'community', 'group', 'clusterID'):
            v = node.get(key)
            if v is not None:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    continue
        return 0

    @staticmethod
    def _edge_endpoints(edge: Dict) -> tuple:
        """Extract source/target — InfraNodus may use 'source'/'target' or 'from'/'to'."""
        src = edge.get('source') or edge.get('from') or edge.get('src') or edge.get('start')
        tgt = edge.get('target') or edge.get('to') or edge.get('dst') or edge.get('end')
        return src, tgt

    def create_network_graph(
        self,
        network_data: Dict[str, Any],
        top_n: int = 150,
        highlight_node: Optional[str] = None,
    ) -> go.Figure:
        """
        Create interactive network graph.
        Accepts either flat {nodes,edges} or wrapped {graph:{nodes,edges}}.
        """
        # Defensive unwrap: accept both flat and wrapped shapes
        if 'graph' in network_data and isinstance(network_data['graph'], dict):
            network_data = network_data['graph']

        all_nodes = network_data.get('nodes') or []
        all_edges = (
            network_data.get('edges')
            or network_data.get('relations')
            or network_data.get('links')
            or []
        )

        # Sort by betweenness DESC and take top_n
        sorted_nodes = sorted(all_nodes, key=self._node_bc, reverse=True)[:top_n]
        top_ids = {self._node_id(n) for n in sorted_nodes if self._node_id(n)}

        # Build NetworkX graph
        G = nx.Graph()
        for node in sorted_nodes:
            nid = self._node_id(node)
            if not nid:
                continue
            G.add_node(
                nid,
                label=self._node_label(node),
                bc=self._node_bc(node),
                degree=int(node.get('degree', 0) or 0),
                weight=int(node.get('weight', 0) or 0),
                cluster=self._node_cluster(node),
            )

        # Add edges (only between top_n nodes)
        for edge in all_edges:
            src, tgt = self._edge_endpoints(edge)
            if src in top_ids and tgt in top_ids:
                try:
                    w = float(edge.get('weight', 1) or 1)
                except (TypeError, ValueError):
                    w = 1.0
                G.add_edge(src, tgt, weight=w)

        if G.number_of_nodes() == 0:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No graph data to display.<br>Check that nodes and edges are loaded.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray"),
            )
            fig.update_layout(height=600, plot_bgcolor='rgba(240,242,246,0.5)')
            return fig

        # Layout
        try:
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        except Exception:
            pos = nx.circular_layout(G)

        # Edge traces
        edge_x, edge_y, edge_widths = [], [], []
        for u, v, d in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_widths.append(d.get('weight', 1))

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(width=1, color='rgba(125,125,125,0.35)'),
            hoverinfo='none',
            showlegend=False,
        )

        # Node trace
        node_x, node_y = [], []
        node_text, node_size, node_color, node_hover = [], [], [], []

        for nid, data in G.nodes(data=True):
            x, y = pos[nid]
            node_x.append(x)
            node_y.append(y)
            label = data.get('label', nid)
            bc = data.get('bc', 0.0)
            degree = data.get('degree', 0)
            weight = data.get('weight', 0)
            cluster = data.get('cluster', 0)

            node_text.append(label)
            node_size.append(10 + bc * 100)  # Scale BC to visible size
            node_color.append(self.color_scale[cluster % len(self.color_scale)])
            node_hover.append(
                f"<b>{label}</b><br>"
                f"BC: {bc:.4f}<br>"
                f"Degree: {degree}<br>"
                f"Weight: {weight:,}<br>"
                f"Cluster: {cluster}"
            )

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            textfont=dict(size=9, color='#ffffff'),
            hovertext=node_hover,
            hoverinfo='text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=1.5, color='white'),
                opacity=0.92,
            ),
            showlegend=False,
        )

        fig = go.Figure(data=[edge_trace, node_trace])

        # Optional highlight
        if highlight_node:
            for nid, data in G.nodes(data=True):
                if data.get('label', '').lower() == highlight_node.lower():
                    x, y = pos[nid]
                    fig.add_trace(go.Scatter(
                        x=[x], y=[y], mode='markers',
                        marker=dict(size=40, color='rgba(255,0,0,0)',
                                    line=dict(width=4, color='red')),
                        hoverinfo='skip', showlegend=False,
                    ))
                    break

        fig.update_layout(
            title=dict(text=f"Knowledge Graph Network (Top {top_n} Nodes)",
                       font=dict(size=18)),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=10, l=10, r=10, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='#fafafa'),
            height=700,
        )
        return fig

    def create_community_timeline(self, timeline_data):
        """Stacked area chart — unchanged logic."""
        fig = go.Figure()
        clusters = {}
        for r in timeline_data:
            c = r.get('cluster', 'Unknown')
            clusters.setdefault(c, {'dates': [], 'influence': []})
            clusters[c]['dates'].append(r['date'])
            clusters[c]['influence'].append(r['influence'])
        for i, (c, d) in enumerate(clusters.items()):
            fig.add_trace(go.Scatter(
                x=d['dates'], y=d['influence'], name=str(c),
                stackgroup='one', mode='lines', line=dict(width=0),
                fillcolor=self.color_scale[i % len(self.color_scale)],
            ))
        fig.update_layout(title="Community Evolution Over Time",
                          xaxis_title="Date", yaxis_title="% Influence",
                          hovermode='x unified', height=400)
        return fig

    def create_sentiment_chart(self, sentiment_data):
        """Sentiment trend lines — unchanged logic."""
        dates = [d['date'] for d in sentiment_data]
        fig = go.Figure()
        for key, color in [('positive', '#28a745'),
                            ('negative', '#dc3545'),
                            ('neutral', '#6c757d')]:
            fig.add_trace(go.Scatter(
                x=dates, y=[d[key] for d in sentiment_data],
                name=key.capitalize(),
                line=dict(color=color, width=3),
                mode='lines+markers',
            ))
        fig.update_layout(title="Sentiment Trend Analysis",
                          xaxis_title="Date", yaxis_title="Percentage",
                          hovermode='x unified', height=400)
        return fig
