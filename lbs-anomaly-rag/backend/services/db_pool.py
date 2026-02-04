"""Database Connection Pool for SQL Server"""
import pyodbc
from typing import Optional
from queue import Queue, Empty
from threading import Lock
from config.settings import settings
import time


class DatabaseConnectionPool:
    """
    Connection pool for SQL Server

    Features:
    - Reuse connections instead of creating new ones
    - Thread-safe connection management
    - Automatic connection validation
    - Configurable pool size
    """

    def __init__(self, min_connections: int = 2, max_connections: int = 10):
        """
        Initialize connection pool

        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_string = settings.get_db_connection_string()

        # Connection pool (available connections)
        self.pool = Queue(maxsize=max_connections)

        # Track active connections
        self.active_connections = 0
        self.lock = Lock()

        # Statistics
        self.stats = {
            "total_created": 0,
            "total_requests": 0,
            "total_returns": 0,
            "pool_hits": 0,
            "pool_misses": 0
        }

        # Initialize minimum connections
        print(f"Initializing database connection pool (min={min_connections}, max={max_connections})")
        for _ in range(min_connections):
            try:
                conn = self._create_connection()
                self.pool.put(conn)
            except Exception as e:
                print(f"Warning: Could not create initial connection: {e}")

        print(f"✓ Connection pool initialized with {self.pool.qsize()} connections")

    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection"""
        with self.lock:
            self.stats["total_created"] += 1
            self.active_connections += 1

        conn = pyodbc.connect(
            self.connection_string,
            timeout=settings.QUERY_TIMEOUT,
            autocommit=True
        )
        return conn

    def _validate_connection(self, conn: pyodbc.Connection) -> bool:
        """Check if connection is still valid"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def get_connection(self, timeout: int = 5) -> pyodbc.Connection:
        """
        Get a connection from the pool

        Args:
            timeout: Maximum time to wait for a connection (seconds)

        Returns:
            Database connection

        Raises:
            Exception: If no connection available within timeout
        """
        with self.lock:
            self.stats["total_requests"] += 1

        start_time = time.time()

        # Try to get from pool first
        try:
            conn = self.pool.get(block=True, timeout=timeout)
            self.stats["pool_hits"] += 1

            # Validate connection
            if self._validate_connection(conn):
                return conn
            else:
                # Connection is stale, create new one
                print("Warning: Stale connection detected, creating new one")
                with self.lock:
                    self.active_connections -= 1
                return self._create_connection()

        except Empty:
            # Pool is empty, try to create new connection if under max
            with self.lock:
                if self.active_connections < self.max_connections:
                    self.stats["pool_misses"] += 1
                    return self._create_connection()

            # Can't create more connections, wait a bit and retry
            elapsed = time.time() - start_time
            if elapsed < timeout:
                time.sleep(0.1)
                return self.get_connection(timeout - elapsed)

            raise Exception(f"No database connections available after {timeout}s (max={self.max_connections})")

    def return_connection(self, conn: pyodbc.Connection):
        """
        Return a connection to the pool

        Args:
            conn: Connection to return
        """
        with self.lock:
            self.stats["total_returns"] += 1

        if conn is None:
            return

        # Validate before returning to pool
        if self._validate_connection(conn):
            try:
                self.pool.put_nowait(conn)
            except Exception:
                # Pool is full, close the connection
                try:
                    conn.close()
                except Exception:
                    pass
                with self.lock:
                    self.active_connections -= 1
        else:
            # Connection is bad, close it
            try:
                conn.close()
            except Exception:
                pass
            with self.lock:
                self.active_connections -= 1

    def close_all(self):
        """Close all connections in the pool"""
        print("Closing all database connections...")
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Exception:
                pass

        with self.lock:
            self.active_connections = 0

        print("✓ All connections closed")

    def get_stats(self) -> dict:
        """Get connection pool statistics"""
        with self.lock:
            return {
                "pool_size": self.pool.qsize(),
                "active_connections": self.active_connections,
                "max_connections": self.max_connections,
                "total_created": self.stats["total_created"],
                "total_requests": self.stats["total_requests"],
                "pool_hit_rate": round(
                    (self.stats["pool_hits"] / self.stats["total_requests"] * 100)
                    if self.stats["total_requests"] > 0 else 0,
                    2
                )
            }


class PooledConnection:
    """
    Context manager for pooled connections

    Usage:
        with PooledConnection(pool) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """

    def __init__(self, pool: DatabaseConnectionPool):
        self.pool = pool
        self.conn = None

    def __enter__(self) -> pyodbc.Connection:
        self.conn = self.pool.get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.return_connection(self.conn)


# Global connection pool
_connection_pool = None


def get_connection_pool() -> DatabaseConnectionPool:
    """Get singleton connection pool instance"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool(
            min_connections=2,
            max_connections=10
        )
    return _connection_pool


def get_pooled_connection() -> PooledConnection:
    """Get a pooled connection context manager"""
    return PooledConnection(get_connection_pool())
