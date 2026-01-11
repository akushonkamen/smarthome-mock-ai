"""Tests for the preference learning module."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from smarthome_mock_ai.learning import PreferenceModel


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    db_path = tmp_path / "test_history.db"
    return str(db_path)


@pytest.fixture
def preference_model(temp_db_path):
    """Create a PreferenceModel instance with temp database."""
    return PreferenceModel(temp_db_path)


class TestPreferenceModelBasics:
    """Test basic PreferenceModel functionality."""

    def test_init_creates_model(self, preference_model, temp_db_path):
        """Test that PreferenceModel initializes correctly."""
        assert preference_model.db_path == temp_db_path
        assert preference_model.min_confidence == 2
        assert len(preference_model.preferences) == 0
        assert len(preference_model.confidence) == 0

    def test_get_time_period(self, preference_model):
        """Test time period classification."""
        assert preference_model._get_time_period(6) == "early_morning"
        assert preference_model._get_time_period(10) == "morning"
        assert preference_model._get_time_period(14) == "afternoon"
        assert preference_model._get_time_period(19) == "evening"
        assert preference_model._get_time_period(22) == "night"
        assert preference_model._get_time_period(2) == "late_night"

    def test_get_context_key(self, preference_model):
        """Test context key generation."""
        context = {"time_of_day": 10, "day_of_week": 0}  # Monday morning
        key = preference_model._get_context_key(context)
        assert key == "morning_weekday"

        context = {"time_of_day": 20, "day_of_week": 5}  # Friday evening
        key = preference_model._get_context_key(context)
        assert key == "evening_weekend"


class TestPreferenceModelTraining:
    """Test training functionality."""

    def test_train_with_empty_database(self, preference_model, temp_db_path):
        """Test training with an empty database."""
        # Create empty database with table
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)
        conn.commit()
        conn.close()

        stats = preference_model.train()
        assert stats["total_interactions"] == 0
        assert stats["preferences_learned"] == 0
        assert stats["tools_updated"] == []

    def test_train_from_corrections(self, temp_db_path, preference_model):
        """Test training from user corrections."""
        # Create mock interaction data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Create table and insert mock data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # Insert 3 corrections: user wants 24°C in evening (consistently)
        for i in range(3):
            context = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "time_of_day": 19,
                "day_of_week": 0,
            })
            agent_action = json.dumps({
                "actions": [{
                    "tool": "set_temperature",
                    "arguments": {"device_id": "thermostat", "temp": 26}
                }]
            })

            cursor.execute(
                """INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), context, "太热了", agent_action, f"action_{i}", -1, "不,应该是24度")
            )

        conn.commit()
        conn.close()

        # Train the model
        stats = preference_model.train()

        assert stats["total_interactions"] == 3
        assert stats["preferences_learned"] >= 3
        assert "set_temperature" in stats["tools_updated"]

    def test_train_with_positive_feedback(self, temp_db_path, preference_model):
        """Test that positive feedback reinforces actions."""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # Insert positive feedback for 22°C
        context = json.dumps({"time_of_day": 8, "day_of_week": 0})
        agent_action = json.dumps({
            "actions": [{
                "tool": "set_temperature",
                "arguments": {"device_id": "thermostat", "temp": 22}
            }]
        })

        cursor.execute(
            """INSERT INTO interaction_logs
            (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), context, "调低温度", agent_action, "action_1", 1, None)
        )

        conn.commit()
        conn.close()

        stats = preference_model.train()
        assert stats["preferences_learned"] >= 1
        assert "set_temperature" in stats["tools_updated"]


class TestPreferenceModelPrediction:
    """Test prediction and adjustment functionality."""

    def test_predict_with_no_preferences(self, preference_model):
        """Test prediction when no preferences are learned."""
        context = {"time_of_day": 19, "day_of_week": 0}
        prediction = preference_model.predict(
            "set_temperature",
            {"device_id": "thermostat", "temp": 26},
            context
        )
        assert prediction is None

    def test_predict_with_learned_preferences(self, temp_db_path, preference_model):
        """Test prediction after learning preferences."""
        # Setup: Train the model with corrections
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # 3 corrections for 24°C in evening
        for i in range(3):
            context = json.dumps({"time_of_day": 19, "day_of_week": 0})
            agent_action = json.dumps({
                "actions": [{
                    "tool": "set_temperature",
                    "arguments": {"device_id": "thermostat", "temp": 26}
                }]
            })

            cursor.execute(
                """INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), context, "太热了", agent_action, f"action_{i}", -1, "应该是24度")
            )

        conn.commit()
        conn.close()

        # Train
        preference_model.train()

        # Now predict
        context = {"time_of_day": 19, "day_of_week": 0}
        prediction = preference_model.predict(
            "set_temperature",
            {"device_id": "thermostat", "temp": 26},
            context
        )

        assert prediction is not None
        assert prediction["parameter"] == "temp"
        assert prediction["original_value"] == 26
        assert prediction["suggested_value"] == 24
        assert prediction["confidence"] >= 2

    def test_adjust_arguments(self, temp_db_path, preference_model):
        """Test adjusting arguments based on preferences."""
        # Setup training data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # 3 corrections for 50% brightness in morning
        for i in range(3):
            context = json.dumps({"time_of_day": 9, "day_of_week": 0})
            agent_action = json.dumps({
                "actions": [{
                    "tool": "set_light_brightness",
                    "arguments": {"device_id": "living_room_light", "level": 100}
                }]
            })

            cursor.execute(
                """INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), context, "太亮了", agent_action, f"action_{i}", -1, "应该是50%")
            )

        conn.commit()
        conn.close()

        # Train
        preference_model.train()

        # Adjust arguments
        context = {"time_of_day": 9, "day_of_week": 0}
        adjusted_args, message = preference_model.adjust_arguments(
            "set_light_brightness",
            {"device_id": "living_room_light", "level": 100},
            context
        )

        assert adjusted_args["level"] == 50
        assert message is not None
        assert "根据您的习惯" in message
        assert "50" in message

    def test_predict_different_context_no_match(self, temp_db_path, preference_model):
        """Test that predictions don't apply across different contexts."""
        # Train for evening preference
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # Evening correction for 24°C
        context = json.dumps({"time_of_day": 20, "day_of_week": 0})
        agent_action = json.dumps({
            "actions": [{
                "tool": "set_temperature",
                "arguments": {"device_id": "thermostat", "temp": 26}
            }]
        })

        cursor.execute(
            """INSERT INTO interaction_logs
            (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), context, "太热", agent_action, "action_1", -1, "24度")
        )

        conn.commit()
        conn.close()

        preference_model.train()

        # Try morning context - should not predict
        morning_context = {"time_of_day": 9, "day_of_week": 0}
        prediction = preference_model.predict(
            "set_temperature",
            {"device_id": "thermostat", "temp": 26},
            morning_context
        )

        # Should not predict because context doesn't match
        assert prediction is None


class TestPreferenceModelPersistence:
    """Test save/load functionality."""

    def test_save_and_load_preferences(self, temp_db_path, preference_model, tmp_path):
        """Test saving and loading preferences."""
        # Setup some preferences
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        context = json.dumps({"time_of_day": 19, "day_of_week": 0})
        agent_action = json.dumps({
            "actions": [{
                "tool": "set_temperature",
                "arguments": {"device_id": "thermostat", "temp": 26}
            }]
        })

        cursor.execute(
            """INSERT INTO interaction_logs
            (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), context, "太热", agent_action, "action_1", -1, "24度")
        )

        conn.commit()
        conn.close()

        preference_model.train()

        # Save preferences
        pref_file = str(tmp_path / "preferences.json")
        saved_path = preference_model.save_preferences(pref_file)
        assert saved_path == pref_file

        # Create new model and load
        new_model = PreferenceModel()
        loaded = new_model.load_preferences(pref_file)
        assert loaded is True

        # Verify preferences were loaded
        assert len(new_model.preferences) > 0
        assert len(new_model.confidence) > 0


class TestPreferenceModelSummary:
    """Test preference summary functionality."""

    def test_get_preference_summary(self, temp_db_path, preference_model):
        """Test getting preference summary."""
        # Setup training data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # Add some corrections
        context = json.dumps({"time_of_day": 19, "day_of_week": 0})
        agent_action = json.dumps({
            "actions": [{
                "tool": "set_temperature",
                "arguments": {"device_id": "thermostat", "temp": 26}
            }]
        })

        for i in range(3):
            cursor.execute(
                """INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), context, "太热", agent_action, f"action_{i}", -1, "24度")
            )

        conn.commit()
        conn.close()

        preference_model.train()

        summary = preference_model.get_preference_summary()

        assert summary["total_preferences"] > 0
        assert "set_temperature" in summary["tools"]
        assert "evening_weekday" in summary["tools"]["set_temperature"]


class TestHabitLearningScenario:
    """Test the complete habit learning scenario."""

    def test_habit_learning_complete_scenario(self, temp_db_path, preference_model):
        """Test that after 3 corrections, the 4th time the system gets it right.

        This is the key verification test requested in the requirements.
        """
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                user_command TEXT,
                agent_action TEXT,
                action_id TEXT,
                user_feedback INTEGER,
                corrected_command TEXT
            )
        """)

        # Simulate 3 user corrections:
        # Each time the LLM suggests 26°C, user corrects to 24°C in the evening
        for i in range(3):
            context = json.dumps({"time_of_day": 19, "day_of_week": 0})
            agent_action = json.dumps({
                "actions": [{
                    "tool": "set_temperature",
                    "arguments": {"device_id": "thermostat", "temp": 26}
                }]
            })

            cursor.execute(
                """INSERT INTO interaction_logs
                (timestamp, context, user_command, agent_action, action_id, user_feedback, corrected_command)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), context, "太热了", agent_action, f"action_{i}", -1, "应该是24度")
            )

        conn.commit()
        conn.close()

        # Train the model
        stats = preference_model.train()
        assert stats["total_interactions"] == 3
        assert stats["preferences_learned"] >= 3

        # Now the 4th time: LLM suggests 26°C again
        evening_context = {"time_of_day": 19, "day_of_week": 0}
        llm_suggestion = {"device_id": "thermostat", "temp": 26}

        # The model should predict and adjust to 24°C
        adjusted_args, message = preference_model.adjust_arguments(
            "set_temperature",
            llm_suggestion,
            evening_context
        )

        # Verify the system automatically corrected it
        assert adjusted_args["temp"] == 24, "System should automatically adjust to 24°C after learning"
        assert message is not None, "System should provide explanation for the adjustment"
        assert "24" in message, "Message should mention the corrected value"

        # Verify the confidence is high enough
        prediction = preference_model.predict("set_temperature", llm_suggestion, evening_context)
        assert prediction is not None
        assert prediction["confidence"] >= 2, "Confidence should be at least minimum threshold after 3 corrections"
