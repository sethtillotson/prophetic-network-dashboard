"""
Network Graph Visualizer
Creates interactive Plotly visualizations of knowledge graphs
"""

import plotly.graph_objects as go
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple

class GraphVisualizer:
    """Interactive network graph visualization with Plotly"""
    
    def __init__(self):
        """Initialize visualizer"""
        self.color_scale = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe',
            '#00f2fe', '#43e97b', '#38f9d7', '#fa709a',
            '#fee140', '#30cfd0', '#a8edea'
        ]
    
    def create_network_graph(
        self,
        network_data: Dict[str, Any],
        top_n: int = 150,
        highlight_node: Optional[str] = None
    ) -> go.Figure:
        """
        Create interactive network graph
        
        Args:
            network_data: Network data from InfraNodus API
            top_n: Number of top nodes to display
            highlight_node: Node to highlight (optional)
            
        Returns:
            Plotly figure
        """
        # Extract graph data
        nodes = network_data.get('nodes', [])[:top_n]
        edges = network_data.get('edges', [])
        
        # Build NetworkX graph for layout
        G = nx.Graph()
        
        # Add nodes with attributes
        for node in nodes:
            G.add_node(
                node.get('id'),
                label=node.get('label', ''),
                bc=node.get('betweenness', 0.0),
                degree=node.get('degree', 0),
                weight=node.get('weight', 0),
                cluster=node.get('cluster', 0)
            )
        
        # Add edges
        edge_list = []
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            weight = edge.get('weight', 1)
            
            # Only add if both nodes are in top_n
            if source in G.nodes and target in G.nodes:
                G.add_edge(source, target, weight=weight)
                edge_list.append((source, target, weight))
        
        # Compute spring layout
        try:
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        except:
            # Fallback to circular layout if spring fails
            pos = nx.circular_layout(G)
        
        # Create edge traces
        edge_traces = []
        for source, target, weight in edge_list:
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            
            # Edge thickness based on weight
            width = min(weight / 50, 5)  # Cap at 5px
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color='rgba(125, 125, 125, 0.3)'),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        node_hover = []
        
        for node in G.nodes(data=True):
            node_id = node[0]
            node_data = node[1]
            
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            label = node_data.get('label', node_id)
            bc = node_data.get('bc', 0.0)
            degree = node_data.get('degree', 0)
            weight = node_data.get('weight', 0)
            cluster = node_data.get('cluster', 0)
            
            # Node size based on betweenness centrality
            size = 10 + (bc * 50)  # Scale BC to visible size
            node_size.append(size)
            
            # Node color based on cluster
            color_idx = cluster % len(self.color_scale)
            node_color.append(self.color_scale[color_idx])
            
            # Node label (show @ prefix if exists)
            node_text.append(label)
            
            # Hover text
            hover_text = (
                f"<b>{label}</b><br>"
                f"BC: {bc:.4f}<br>"
                f"Degree: {degree}<br>"
                f"Weight: {weight:,}<br>"
                f"Cluster: {cluster}"
            )
            node_hover.append(hover_text)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            textfont=dict(size=8),
            hovertext=node_hover,
            hoverinfo='text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white'),
                opacity=0.9
            ),
            showlegend=False
        )
        
        # Highlight specific node if requested
        if highlight_node:
            highlight_trace = None
            for node in G.nodes(data=True):
                node_id = node[0]
                node_data = node[1]
                label = node_data.get('label', '')
                
                if label.lower() == highlight_node.lower():
                    x, y = pos[node_id]
                    highlight_trace = go.Scatter(
                        x=[x],
                        y=[y],
                        mode='markers',
                        marker=dict(
                            size=40,
                            color='rgba(255, 0, 0, 0)',
                            line=dict(width=4, color='red')
                        ),
                        hoverinfo='skip',
                        showlegend=False
                    )
                    break
        
        # Create figure
        fig = go.Figure()
        
        # Add all edge traces
        for edge_trace in edge_traces:
            fig.add_trace(edge_trace)
        
        # Add node trace
        fig.add_trace(node_trace)
        
        # Add highlight if exists
        if highlight_node and highlight_trace:
            fig.add_trace(highlight_trace)
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Knowledge Graph Network (Top {top_n} Nodes)",
                font=dict(size=20)
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(240, 242, 246, 0.5)',
            height=700
        )
        
        return fig
    
    def create_community_timeline(
        self,
        timeline_data: List[Dict[str, Any]]
    ) -> go.Figure:
        """
        Create stacked area chart for community evolution
        
        Args:
            timeline_data: List of {date, cluster, influence} dicts
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Group by cluster
        clusters = {}
        for record in timeline_data:
            cluster = record.get('cluster', 'Unknown')
            if cluster not in clusters:
                clusters[cluster] = {'dates': [], 'influence': []}
            clusters[cluster]['dates'].append(record['date'])
            clusters[cluster]['influence'].append(record['influence'])
        
        # Add trace for each cluster
        for i, (cluster, data) in enumerate(clusters.items()):
            color_idx = i % len(self.color_scale)
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['influence'],
                name=cluster,
                stackgroup='one',
                mode='lines',
                line=dict(width=0),
                fillcolor=self.color_scale[color_idx],
                hovertemplate='%{y:.1f}%<br>%{fullData.name}'
            ))
        
        fig.update_layout(
            title="Community Evolution Over Time",
            xaxis_title="Date",
            yaxis_title="% Influence (BC Ratio)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_sentiment_chart(
        self,
        sentiment_data: List[Dict[str, Any]]
    ) -> go.Figure:
        """
        Create multi-line sentiment trend chart
        
        Args:
            sentiment_data: List of {date, positive, negative, neutral} dicts
            
        Returns:
            Plotly figure
        """
        dates = [d['date'] for d in sentiment_data]
        positive = [d['positive'] for d in sentiment_data]
        negative = [d['negative'] for d in sentiment_data]
        neutral = [d['neutral'] for d in sentiment_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=positive,
            name='Positive',
            line=dict(color='#28a745', width=3),
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=negative,
            name='Negative',
            line=dict(color='#dc3545', width=3),
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=neutral,
            name='Neutral',
            line=dict(color='#6c757d', width=3),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title="Sentiment Trend Analysis",
            xaxis_title="Date",
            yaxis_title="Percentage",
            hovermode='x unified',
            height=400
        )
        
        return fig
