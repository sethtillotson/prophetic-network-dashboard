"""
InfraNodus Direct API Client
Handles all direct HTTP requests to InfraNodus API endpoints
"""

import requests
import json
from typing import Dict, List, Optional, Any

class InfraNodusAPI:
    """Direct API client for InfraNodus knowledge graph service"""
    
    BASE_URL = "https://infranodus.com/api/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize API client
        
        Args:
            api_key: InfraNodus API key from https://infranodus.com/api-access
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_graph_and_statements(
        self,
        text: Optional[str] = None,
        graph_name: Optional[str] = None,
        do_not_save: bool = False,
        add_stats: bool = True,
        include_graph: bool = True,
        include_graph_summary: bool = True,
        gap_depth: int = 2,
        ai_topics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate knowledge graph from text or retrieve existing graph
        
        Args:
            text: Text to analyze (optional if graph_name provided)
            graph_name: Name of existing graph to retrieve/update
            do_not_save: If True, don't save to InfraNodus account
            add_stats: Include graph statistics
            include_graph: Include full graph structure
            include_graph_summary: Include AI-generated summary
            gap_depth: Depth for gap analysis (1-3)
            ai_topics: Generate AI topic names for clusters
            
        Returns:
            Dict containing graph, statements, and statistics
        """
        endpoint = f"{self.BASE_URL}/graphAndStatements"
        
        params = {
            "doNotSave": str(do_not_save).lower(),
            "addStats": str(add_stats).lower(),
            "includeGraph": str(include_graph).lower(),
            "includeGraphSummary": str(include_graph_summary).lower(),
            "gapDepth": gap_depth
        }
        
        body = {}
        if text:
            body["text"] = text
        if graph_name:
            body["name"] = graph_name
        if ai_topics:
            body["aiTopics"] = True
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                params=params,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"InfraNodus API error: {str(e)}")
    
    def get_graph_and_advice(
        self,
        text: str,
        request_mode: str = "questions",
        optimize: str = "develop",
        transcend: bool = False
    ) -> Dict[str, Any]:
        """
        Get AI-generated advice, questions, or ideas based on text
        
        Args:
            text: Text to analyze
            request_mode: Type of output (questions, ideas, facts, summary, etc.)
            optimize: Optimization mode (develop, reinforce, gaps, latent)
            transcend: If True, broaden discourse scope
            
        Returns:
            Dict containing AI-generated advice
        """
        endpoint = f"{self.BASE_URL}/graphAndAdvice"
        
        params = {
            "optimize": optimize,
            "transcend": str(transcend).lower()
        }
        
        body = {
            "text": text,
            "requestMode": request_mode
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                params=params,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"InfraNodus API error: {str(e)}")
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """
        List all graphs in user's account
        
        Returns:
            List of graph metadata
        """
        endpoint = f"{self.BASE_URL}/listGraphs"
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"InfraNodus API error: {str(e)}")
    
    def compare_graphs(
        self,
        graph_names: List[str],
        compare_mode: str = "overlap"
    ) -> Dict[str, Any]:
        """
        Compare multiple graphs
        
        Args:
            graph_names: List of graph names to compare
            compare_mode: Comparison mode (overlap, difference, merge)
            
        Returns:
            Dict containing comparison results
        """
        endpoint = f"{self.BASE_URL}/compareGraphs"
        
        body = {
            "graphNames": graph_names,
            "compareMode": compare_mode
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"InfraNodus API error: {str(e)}")
    
    def search(
        self,
        query: str,
        graph_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search statements in graph
        
        Args:
            query: Search query
            graph_name: Specific graph to search (optional)
            
        Returns:
            Dict containing matching statements and subgraph
        """
        endpoint = f"{self.BASE_URL}/search"
        
        body = {
            "query": query
        }
        if graph_name:
            body["graphName"] = graph_name
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"InfraNodus API error: {str(e)}")
