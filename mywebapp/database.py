from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _load_pymysql():
    try:
        import pymysql  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyMySQL is not installed. Install dependencies from requirements.txt first."
        ) from exc
    return pymysql


@dataclass(slots=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    connect_timeout: int = 5


class MariaDBInventoryRepository:
    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config

    def _connect(self):
        pymysql = _load_pymysql()
        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.name,
            connect_timeout=self.config.connect_timeout,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def check_ready(self) -> tuple[bool, str]:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return True, "OK"
        except Exception as exc:
            return False, f"database unavailable: {exc}"

    def migrate(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INT PRIMARY KEY,
                        applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        quantity INT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute("SHOW INDEX FROM items WHERE Key_name = %s", ("idx_items_created_at",))
                has_created_at_index = cursor.fetchone() is not None
                if not has_created_at_index:
                    cursor.execute("CREATE INDEX idx_items_created_at ON items (created_at)")
                cursor.execute(
                    """
                    INSERT IGNORE INTO schema_migrations (version)
                    VALUES (1)
                    """
                )
            connection.commit()

    def list_items(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, name
            FROM items
            ORDER BY id ASC
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return list(cursor.fetchall())

    def get_item(self, item_id: int) -> dict[str, Any] | None:
        query = """
            SELECT id, name, quantity, created_at
            FROM items
            WHERE id = %s
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (item_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def create_item(self, name: str, quantity: int) -> dict[str, Any]:
        insert_query = """
            INSERT INTO items (name, quantity)
            VALUES (%s, %s)
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_query, (name, quantity))
                item_id = cursor.lastrowid
            connection.commit()
        item = self.get_item(int(item_id))
        if item is None:
            raise RuntimeError("created item could not be reloaded from the database")
        return item
