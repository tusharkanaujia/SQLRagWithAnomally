"""Cache Service for Query Results and Anomaly Detection"""
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import os


class CacheService:
    """
    Intelligent caching service with Redis fallback to in-memory

    Features:
    - Automatic Redis connection with graceful fallback
    - Configurable TTL per cache type
    - Cache invalidation support
    - Hit/miss statistics
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self.redis_client = None
        self.use_redis = False
        self.memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self.stats = {"hits": 0, "misses": 0, "sets": 0}

        # Try to connect to Redis
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        try:
            import redis
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            print(f"✓ Redis cache enabled at {redis_url}")
        except Exception as e:
            print(f"⚠ Redis unavailable: {e}")
            print("  Using in-memory cache (not persisted)")

    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        # Create hash of the data
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            if self.use_redis:
                # Get from Redis
                value = self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    return json.loads(value)
                else:
                    self.stats["misses"] += 1
                    return None
            else:
                # Get from memory cache
                if key in self.memory_cache:
                    value, expiry = self.memory_cache[key]
                    if expiry is None or datetime.now() < expiry:
                        self.stats["hits"] += 1
                        return value
                    else:
                        # Expired
                        del self.memory_cache[key]

                self.stats["misses"] += 1
                return None

        except Exception as e:
            print(f"Cache get error: {e}")
            self.stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl_seconds: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful
        """
        try:
            self.stats["sets"] += 1

            if self.use_redis:
                # Set in Redis with TTL
                self.redis_client.setex(
                    key,
                    ttl_seconds,
                    json.dumps(value)
                )
                return True
            else:
                # Set in memory cache
                expiry = datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
                self.memory_cache[key] = (value, expiry)

                # Clean up expired entries if cache is getting large
                if len(self.memory_cache) > 1000:
                    self._cleanup_memory_cache()

                return True

        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.use_redis:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
        except Exception:
            return False

    def clear(self, pattern: str = None) -> int:
        """
        Clear cache entries

        Args:
            pattern: Pattern to match (e.g., "query:*"). If None, clears all.

        Returns:
            Number of keys deleted
        """
        try:
            if self.use_redis:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        return self.redis_client.delete(*keys)
                    return 0
                else:
                    return self.redis_client.flushdb()
            else:
                if pattern:
                    # Simple pattern matching for memory cache
                    prefix = pattern.replace('*', '')
                    keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
                    for k in keys_to_delete:
                        del self.memory_cache[k]
                    return len(keys_to_delete)
                else:
                    count = len(self.memory_cache)
                    self.memory_cache.clear()
                    return count
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [
            k for k, (_, expiry) in self.memory_cache.items()
            if expiry and now >= expiry
        ]
        for k in expired_keys:
            del self.memory_cache[k]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "backend": "redis" if self.use_redis else "memory",
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "hit_rate_pct": round(hit_rate, 2)
        }

        if self.use_redis:
            try:
                info = self.redis_client.info()
                stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
                stats["redis_keys"] = self.redis_client.dbsize()
            except Exception:
                pass
        else:
            stats["memory_keys"] = len(self.memory_cache)

        return stats

    # Convenience methods for different cache types

    def get_query_cache(self, question: str, execute: bool = True) -> Optional[Dict]:
        """Get cached query result"""
        key = self._generate_key("query", {"q": question, "exec": execute})
        return self.get(key)

    def set_query_cache(self, question: str, result: Dict, execute: bool = True, ttl: int = 300) -> bool:
        """Cache query result (default: 5 minutes)"""
        key = self._generate_key("query", {"q": question, "exec": execute})
        return self.set(key, result, ttl)

    def get_anomaly_cache(self, detection_type: str, params: Dict) -> Optional[Dict]:
        """Get cached anomaly detection result"""
        key = self._generate_key(f"anomaly:{detection_type}", params)
        return self.get(key)

    def set_anomaly_cache(self, detection_type: str, params: Dict, result: Dict, ttl: int = 3600) -> bool:
        """Cache anomaly result (default: 1 hour)"""
        key = self._generate_key(f"anomaly:{detection_type}", params)
        return self.set(key, result, ttl)

    def clear_query_cache(self) -> int:
        """Clear all query caches"""
        return self.clear("query:*")

    def clear_anomaly_cache(self) -> int:
        """Clear all anomaly caches"""
        return self.clear("anomaly:*")


# Global instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get singleton cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
