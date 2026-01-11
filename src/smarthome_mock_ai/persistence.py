"""Persistence Layer - SQLite database connection management and utilities.

This module provides the foundational database infrastructure for the SmartHome Mock AI system.
It handles SQLite connections, connection pooling, and common database operations.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class DatabaseConnectionManager:
    """Manager for SQLite database connections with context management.

    Provides thread-safe connection handling and automatic resource cleanup.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the database connection manager.

        Args:
            db_path: Path to SQLite database file. Defaults to data/smarthome.db
        """
        if db_path is None:
            # Create data directory if it doesn't exist
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "smarthome.db")

        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    @contextmanager
    def get_connection(self):
        """Get a database connection with context management.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            >>> with db_manager.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM devices")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self, schema_sql: str) -> None:
        """Initialize database schema from SQL string.

        Args:
            schema_sql: SQL schema definition
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_sql)

    def execute_query(
        self, query: str, params: tuple[Any, ...] = (), fetch: bool = False
    ) -> sqlite3.Cursor | list[Any] | None:
        """Execute a query with parameters.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: If True, fetch and return all results as a list

        Returns:
            Cursor with query results, or list of fetched results if fetch=True

        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            # Return lastrowid for INSERT operations
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            return cursor.rowcount

    def execute_many(
        self, query: str, params_list: list[tuple[Any, ...]]
    ) -> sqlite3.Cursor:
        """Execute a query multiple times with different parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of rows affected

        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """,
                (table_name,),
            )
            return cursor.fetchone() is not None

    def get_table_info(self, table_name: str) -> list[dict[str, Any]]:
        """Get information about columns in a table.

        Args:
            table_name: Name of the table

        Returns:
            List of dictionaries containing column information

        Raises:
            sqlite3.Error: If table doesn't exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [dict(row) for row in cursor.fetchall()]

    def backup_database(self, backup_path: str | None = None) -> str:
        """Create a backup of the database.

        Args:
            backup_path: Path for backup file. Defaults to <db_path>.backup

        Returns:
            Path to the backup file

        Raises:
            IOError: If backup creation fails
        """
        if backup_path is None:
            backup_path = f"{self.db_path}.backup"

        # Read from source and write to backup
        with open(self.db_path, "rb") as src:
            with open(backup_path, "wb") as dst:
                dst.write(src.read())

        return backup_path

    def vacuum_database(self) -> None:
        """Vacuum the database to reclaim unused space.

        This should be called periodically to keep the database file size optimized.
        """
        with self.get_connection() as conn:
            conn.execute("VACUUM")

    def get_database_size(self) -> int:
        """Get the size of the database file in bytes.

        Returns:
            Size of the database file in bytes, or 0 if file doesn't exist
        """
        db_path = Path(self.db_path)
        if not db_path.exists():
            # Create database by making a connection
            with self.get_connection() as conn:
                pass
        return db_path.stat().st_size


class BaseRepository:
    """Base repository class providing common database operations.

    Subclasses can inherit from this to get basic CRUD operations.
    """

    def __init__(self, db_manager: DatabaseConnectionManager, table_name: str) -> None:
        """Initialize the repository.

        Args:
            db_manager: Database connection manager
            table_name: Name of the table this repository manages
        """
        self.db_manager = db_manager
        self.table_name = table_name

    def find_by_id(self, record_id: int) -> dict[str, Any] | None:
        """Find a record by its ID.

        Args:
            record_id: The ID of the record

        Returns:
            Dictionary of record data, or None if not found
        """
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def find_all(
        self, limit: int | None = None, order_by: str | None = None
    ) -> list[dict[str, Any]]:
        """Find all records in the table.

        Args:
            limit: Maximum number of records to return
            order_by: Column name to order by (with optional DESC/ASC)

        Returns:
            List of record dictionaries
        """
        query = f"SELECT * FROM {self.table_name}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Count all records in the table.

        Returns:
            Number of records in the table
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cursor.fetchone()[0]

    def delete_by_id(self, record_id: int) -> bool:
        """Delete a record by its ID.

        Args:
            record_id: The ID of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def delete_all(self) -> int:
        """Delete all records from the table.

        Returns:
            Number of records deleted
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name}")
            return cursor.rowcount


# Global instance for easy access
_default_db_manager: DatabaseConnectionManager | None = None


def get_db_manager(db_path: str | None = None) -> DatabaseConnectionManager:
    """Get or create the default database connection manager.

    Args:
        db_path: Optional path to database file

    Returns:
        DatabaseConnectionManager instance
    """
    global _default_db_manager
    if _default_db_manager is None:
        _default_db_manager = DatabaseConnectionManager(db_path)
    return _default_db_manager
