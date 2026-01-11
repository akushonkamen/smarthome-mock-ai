"""Interaction Logger - SQLite database for storing interaction history and feedback."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import sqlite3


class InteractionLogger:
    """Logger for storing interaction history and user feedback."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the interaction logger.

        Args:
            db_path: Path to SQLite database file. Defaults to data/history.db
        """
        if db_path is None:
            # Create data directory if it doesn't exist
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "history.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL,
                    user_command TEXT NOT NULL,
                    agent_action TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    user_feedback INTEGER,
                    corrected_command TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

    def log_interaction(
        self,
        user_command: str,
        agent_action: dict[str, Any],
        context: dict[str, Any] | None = None,
        action_id: str | None = None,
    ) -> int:
        """Log an interaction to the database.

        Args:
            user_command: The user's natural language command
            agent_action: The action the agent took (tool name + parameters)
            context: Context at time of interaction (device states, time of day, etc.)
            action_id: Unique identifier for this action

        Returns:
            The ID of the inserted log entry
        """
        if action_id is None:
            action_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(user_command) % 10000:04d}"

        if context is None:
            context = {}

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    timestamp,
                    json.dumps(context, ensure_ascii=False),
                    user_command,
                    json.dumps(agent_action, ensure_ascii=False),
                    action_id,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def record_feedback(
        self,
        action_id: str,
        feedback: int,
        corrected_command: str | None = None,
    ) -> bool:
        """Record user feedback for an interaction.

        Args:
            action_id: The action ID to record feedback for
            feedback: Feedback score (+1 for good, -1 for bad)
            corrected_command: Optional corrected command if feedback was negative

        Returns:
            True if feedback was recorded successfully, False otherwise
        """
        if feedback not in (1, -1):
            raise ValueError("Feedback must be either 1 (good) or -1 (bad)")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE interaction_logs
                SET user_feedback = ?, corrected_command = ?
                WHERE action_id = ?
                """,
                (feedback, corrected_command, action_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_interaction_by_action_id(self, action_id: str) -> dict[str, Any] | None:
        """Retrieve an interaction by its action ID.

        Args:
            action_id: The action ID to look up

        Returns:
            Dictionary containing the interaction data, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM interaction_logs WHERE action_id = ?
                """,
                (action_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_recent_interactions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent interactions from the database.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM interaction_logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_feedback_stats(self) -> dict[str, Any]:
        """Get statistics about user feedback.

        Returns:
            Dictionary containing feedback statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN user_feedback = 1 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN user_feedback = -1 THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN user_feedback IS NULL THEN 1 ELSE 0 END) as no_feedback
                FROM interaction_logs
                """
            )
            row = cursor.fetchone()
            return {
                "total": row[0],
                "positive": row[1],
                "negative": row[2],
                "no_feedback": row[3],
            }

    def get_training_data(self) -> list[dict[str, Any]]:
        """Get all interactions with feedback for training purposes.

        Returns:
            List of interaction dictionaries with feedback
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM interaction_logs
                WHERE user_feedback IS NOT NULL
                ORDER BY timestamp DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_old_logs(self, days: int = 30) -> int:
        """Clear logs older than specified number of days.

        Args:
            days: Number of days to keep logs

        Returns:
            Number of logs deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Use julianday for more reliable date comparison
            cursor.execute(
                """
                DELETE FROM interaction_logs
                WHERE julianday('now') - julianday(timestamp) > ?
                """,
                (days,),
            )
            conn.commit()
            return cursor.rowcount

    def export_to_json(self, output_path: str | None = None) -> str:
        """Export all interactions to a JSON file.

        Args:
            output_path: Path to save JSON file. Defaults to data/interactions_export.json

        Returns:
            Path to the exported JSON file
        """
        if output_path is None:
            data_dir = Path(self.db_path).parent
            output_path = str(data_dir / "interactions_export.json")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interaction_logs ORDER BY timestamp DESC")
            rows = [dict(row) for row in cursor.fetchall()]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        return output_path


# Global instance for easy access
_default_logger: InteractionLogger | None = None


def get_interaction_logger(db_path: str | None = None) -> InteractionLogger:
    """Get or create the default interaction logger instance.

    Args:
        db_path: Optional path to database file

    Returns:
        InteractionLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = InteractionLogger(db_path)
    return _default_logger
