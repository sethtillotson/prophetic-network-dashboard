"""
Data Cache Manager
Handles local caching of InfraNodus responses to minimize API calls
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

class DataCache:
    """Simple file-based cache for network data"""
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(minutes=5)  # Cache time-to-live
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key"""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                # Expired, remove cache file
                cache_path.unlink()
                return None
            
            return cache_data['data']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache, remove it
            cache_path.unlink()
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            # Cache write failed, not critical
            print(f"Cache write error: {e}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def get_last_update(self) -> Optional[str]:
        """
        Get timestamp of most recent cache update
        
        Returns:
            ISO timestamp string or None
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        
        if not cache_files:
            return None
        
        # Find most recent cache file
        latest_file = max(cache_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            return cache_data['timestamp']
        except:
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache size, file count, etc.
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'file_count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }
