"""
InfraNodus MCP Client
Handles communication with InfraNodus MCP Server for GraphRAG queries
"""

import requests
import json
from typing import Dict, List, Optional, Any

class MCPClient:
    """MCP client for InfraNodus GraphRAG operations"""
    
    MCP_ENDPOINT = "https://mcp.infranodus.com"
    
    def __init__(self, api_key: str):
        """
        Initialize MCP client
        
        Args:
            api_key: InfraNodus API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to call MCP tool
        
        Args:
            tool_name: Name of the MCP tool
            params: Tool parameters
            
        Returns:
            Tool response
        """
        request_body = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        try:
            response = requests.post(
                self.MCP_ENDPOINT,
                headers=self.headers,
                json=request_body,
                timeout=60  # MCP calls can take longer
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP call error: {str(e)}")
    
    def generate_knowledge_graph(
        self,
        text: str,
        include_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Generate knowledge graph from text
        
        Args:
            text: Text to analyze
            include_graph: Include full graph structure
            
        Returns:
            Graph data and statistics
        """
        return self._call_tool("generate_knowledge_graph", {
            "text": text,
            "includeGraph": include_graph
        })
    
    def analyze_existing_graph_by_name(
        self,
        graph_name: str,
        include_graph: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze an existing graph by name
        
        Args:
            graph_name: Name of the graph
            include_graph: Include full graph structure
            
        Returns:
            Graph analysis
        """
        return self._call_tool("analyze_existing_graph_by_name", {
            "graphName": graph_name,
            "includeGraph": include_graph
        })
    
    def retrieve_from_knowledge_base(
        self,
        graph_name: str,
        prompt: str,
        include_graph_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Semantic search using GraphRAG
        
        Args:
            graph_name: Name of the graph to search
            prompt: Search query/concept
            include_graph_summary: Include graph summary
            
        Returns:
            Retrieved statements with similarity scores
        """
        return self._call_tool("retrieve_from_knowledge_base", {
            "graphName": graph_name,
            "prompt": prompt,
            "includeGraphSummary": include_graph_summary
        })
    
    def generate_topical_clusters(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Generate topical clusters from text
        
        Args:
            text: Text to cluster
            
        Returns:
            Topical clusters
        """
        return self._call_tool("generate_topical_clusters", {
            "text": text
        })
    
    def generate_content_gaps(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Identify content gaps in knowledge graph
        
        Args:
            text: Text to analyze
            
        Returns:
            List of content gaps
        """
        return self._call_tool("generate_content_gaps", {
            "text": text
        })
    
    def develop_conceptual_bridges(
        self,
        text: str,
        request_mode: str = "gaps"
    ) -> Dict[str, Any]:
        """
        Develop conceptual bridges between isolated clusters
        
        Args:
            text: Text or query to analyze
            request_mode: Mode (gaps, transcend, develop)
            
        Returns:
            Bridge suggestions and latent concepts
        """
        return self._call_tool("develop_conceptual_bridges", {
            "text": text,
            "requestMode": request_mode
        })
    
    def generate_research_questions(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Generate research questions from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of research questions
        """
        return self._call_tool("generate_research_questions", {
            "text": text
        })
    
    def develop_latent_topics(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Develop latent (under-represented) topics
        
        Args:
            text: Text to analyze
            
        Returns:
            Latent topics to develop
        """
        return self._call_tool("develop_latent_topics", {
            "text": text
        })
    
    def search(
        self,
        graph_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Search statements in graph
        
        Args:
            graph_name: Name of graph to search
            query: Search query
            
        Returns:
            Matching statements
        """
        return self._call_tool("search", {
            "graphName": graph_name,
            "query": query
        })
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """
        List all available graphs
        
        Returns:
            List of graphs
        """
        return self._call_tool("list_graphs", {})
    
    def overlap_between_texts(
        self,
        text1: str,
        text2: str
    ) -> Dict[str, Any]:
        """
        Find overlap between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Overlap analysis
        """
        return self._call_tool("overlap_between_texts", {
            "text1": text1,
            "text2": text2
        })
    
    def difference_between_texts(
        self,
        text1: str,
        text2: str
    ) -> Dict[str, Any]:
        """
        Find differences between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Difference analysis
        """
        return self._call_tool("difference_between_texts", {
            "text1": text1,
            "text2": text2
        })
