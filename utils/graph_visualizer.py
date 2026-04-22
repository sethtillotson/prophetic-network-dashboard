"""
Network Graph Visualizer
Handles InfraNodus Graphology JSON format (nested attributes)
"""

import plotly.graph_objects as go
import networkx as nx
from typing import Dict, List, Optional, Any


class GraphVisualizer:
    def __init__(self):
        self.color_scale = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe',
            '#00f2fe', '#43e97b', '#38f9d7', '#fa709a',
            '#fee140', '#30cfd0', '#a8edea',
        ]

    # ─── Field extractors (handle flat OR attributes-nested) ───
    @staticmethod
    def _get_attr(node_or_edge: Dict, *keys, default=None):
        """Try top-level then inside .attributes for any of the given keys."""
        attrs = node_or_edge.get('attributes', {}) or {}
        for k in keys:
            if k in node_or_edge and node_or_edge[k] is not None:
                return node_or_edge[k]
            if k in attrs and attrs[k] is not None:
                return attrs[k]
        return default

    @classmethod
    def _node_id(cls, node: Dict) -> str:
        """Graphology uses 'key'; InfraNodus may also use 'name' or 'id'."""
        return str(cls._get_attr(node, 'key', 'id', 'name', 'uid', default=''))

    @classmethod
    def _node_label(cls, node: Dict) -> str:
        return str(cls._get_attr(node, 'label', 'name', 'key', 'id', default='?'))

    @classmethod
    def _node_bc(cls, node: Dict) -> float:
        v = cls._get_attr(node, 'bc2', 'bc', 'betweenness', 'betweenness_centrality', default=0)
        try: return float(v)
        except (TypeError, ValueError): return 0.0

    @classmethod
    def _node_cluster(cls, node: Dict) -> int:
        v = cls._get_attr(node, 'cluster', 'community', 'group', 'clusterID', default=0)
        try: return int(v)
        except (TypeError, ValueError): return 0

    @classmethod
    def _node_degree(cls, node: Dict) -> int:
        v = cls._get_attr(node, 'degree', default=0)
        try: return int(v)
        except (TypeError, ValueError): return 0

    @classmethod
    def _node_weight(cls, node: Dict) -> int:
        v = cls._get_attr(node, 'weight', 'nodeWeight', default=0)
        try: return int(v)
        except (TypeError, ValueError): return 0

    @classmethod
    def _edge_endpoints(cls, edge: Dict):
        src = edge.get('source') or edge.get('from') or edge.get('src')
        tgt = edge.get('target') or edge.get('to') or edge.get('dst')
        return src, tgt

    @classmethod
    def _edge_weight(cls, edge: Dict) -> float:
        v = cls._get_attr(edge, 'weight', default=1)
        try: return float(v)
        except (TypeError, ValueError): return 1.0

    # ─── Main unwrap: find nodes/edges ANYWHERE in response ───
    @staticmethod
    def _unwrap_graph(data: Dict) -> Dict:
        """
        Find the level that contains nodes & edges.
        Handles:  {graph:{graphologyGraph:{nodes,edges}}}
                  {graph:{nodes,edges}}
                  {nodes,edges}
                  {graphologyGraph:{nodes,edges}}
        """
        if not isinstance(data, dict):
            return {}
        # Direct hit
        if 'nodes' in data and ('edges' in data or 'relations' in data or 'links' in data):
            return data
        # One level deep
        for key in ('graphologyGraph', 'graph'):
            inner = data.get(key)
            if isinstance(inner, dict):
                unwrapped = GraphVisualizer._unwrap_graph(inner)
                if unwrapped.get('nodes') is not None:
                    return unwrapped
        return {}

    def create_network_graph(
        self,
        network_data: Dict[str, Any],
        top_n: int = 150,
        highlight_node: Optional[str] = None,
    ) -> go.Figure:
        """Create interactive network graph. Accepts any InfraNodus response shape."""
        unwrapped = self._unwrap_graph(network_data)
        all_nodes = unwrapped.get('nodes') or []
        all_edges = (
            unwrapped.get('edges')
            or unwrapped.get('relations')
            or unwrapped.get('links')
            or []
        )

        # Sort by BC DESC, take top_n
        sorted_nodes = sorted(all_nodes, key=self._node_bc, reverse=True)[:top_n]
        top_ids = {self._node_id(n) for n in sorted_nodes if self._node_id(n)}

        G = nx.Graph()
        for node in sorted_nodes:
            nid = self._node_id(node)
            if not nid:
                continue
            G.add_node(
                nid,
                label=self._node_label(node),
                bc=self._node_bc(node),
                degree=self._node_degree(node),
                weight=self._node_weight(node),
                cluster=self._node_cluster(node),
            )

        for edge in all_edges:
            src, tgt = self._edge_endpoints(edge)
            if src in top_ids and tgt in top_ids:
                G.add_edge(src, tgt, weight=self._edge_weight(edge))

        # Empty graph fallback
        if G.number_of_nodes() == 0:
            fig = go.Figure()
            fig.add_annotation(
                text=("No nodes found in response.<br>"
                      "Check browser console or use the Raw JSON dump below."),
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="#fa709a"),
            )
            fig.update_layout(
                height=500, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
                font=dict(color='#fafafa'),
            )
            return fig

        # Layout
        try:
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        except Exception:
            pos = nx.circular_layout(G)

        # Edge trace
        edge_x, edge_y = [], []
        for u, v, _ in G.edges(data=True):
            x0, y0 = pos[u]; x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y, mode='lines',
            line=dict(width=0.8, color='rgba(150,150,150,0.35)'),
            hoverinfo='none', showlegend=False,
        )

        # Node trace
        node_x, node_y, node_text, node_size, node_color, node_hover = [], [], [], [], [], []
        for nid, d in G.nodes(data=True):
            x, y = pos[nid]
            node_x.append(x); node_y.append(y)
            label, bc, deg, wt, cl = d['label'], d['bc'], d['degree'], d['weight'], d['cluster']
            node_text.append(label)
            node_size.append(8 + bc * 80)
            node_color.append(self.color_scale[cl % len(self.color_scale)])
            node_hover.append(
                f"<b>{label}</b><br>BC: {bc:.4f}<br>Degree: {deg}<br>"
                f"Weight: {wt:,}<br>Cluster: {cl}"
            )

        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers+text',
            text=node_text, textposition='top center',
            textfont=dict(size=9, color='#ffffff'),
            hovertext=node_hover, hoverinfo='text',
            marker=dict(
                size=node_size, color=node_color,
                line=dict(width=1.2, color='white'), opacity=0.92,
            ),
            showlegend=False,
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title=dict(text=f"Knowledge Graph (Top {G.number_of_nodes()} Nodes)",
                       font=dict(size=18, color='#fafafa')),
            showlegend=False, hovermode='closest',
            margin=dict(b=10, l=10, r=10, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
            font=dict(color='#fafafa'), height=700,
        )
        return fig

    # ─── Unchanged helpers ───
    def create_community_timeline(self, timeline_data):
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
        dates = [d['date'] for d in sentiment_data]
        fig = go.Figure()
        for key, color in [('positive','#28a745'), ('negative','#dc3545'), ('neutral','#6c757d')]:
            fig.add_trace(go.Scatter(
                x=dates, y=[d[key] for d in sentiment_data],
                name=key.capitalize(),
                line=dict(color=color, width=3), mode='lines+markers',
            ))
        fig.update_layout(title="Sentiment Trend Analysis",
                          xaxis_title="Date", yaxis_title="Percentage",
                          hovermode='x unified', height=400)
        return fig
