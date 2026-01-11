"""Preference Learning Module - Learn user habits from interaction history."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any

import sqlite3


class PreferenceModel:
    """Learn and predict user preferences based on context."""

    # Define context periods
    TIME_PERIODS = {
        "early_morning": (5, 8),   # 5AM - 8AM
        "morning": (8, 12),         # 8AM - 12PM
        "afternoon": (12, 17),      # 12PM - 5PM
        "evening": (17, 21),        # 5PM - 9PM
        "night": (21, 24),          # 9PM - 12AM
        "late_night": (0, 5),       # 12AM - 5AM
    }

    # Parameters that can be learned
    LEARNABLE_PARAMS = {
        "set_temperature": "temp",
        "set_light_brightness": "level",
        "set_fan_speed": "speed",
    }

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the preference model.

        Args:
            db_path: Path to SQLite database. If None, uses default.
        """
        if db_path is None:
            from smarthome_mock_ai.interaction_logger import get_interaction_logger
            logger = get_interaction_logger()
            self.db_path = logger.db_path
        else:
            self.db_path = db_path

        # Preference weights: {tool: {context_key: {value: weight}}}
        self.preferences: dict[str, dict[str, dict[float | int, float]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(float))
        )

        # Confidence scores: {tool: {context_key: {value: count}}}
        self.confidence: dict[str, dict[str, dict[float | int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

        # Minimum confidence threshold for overriding
        self.min_confidence = 2

    def _get_time_period(self, hour: int | None = None) -> str:
        """Get the time period for a given hour.

        Args:
            hour: Hour (0-23). If None, uses current hour.

        Returns:
            Time period key
        """
        if hour is None:
            hour = datetime.now().hour

        for period, (start, end) in self.TIME_PERIODS.items():
            if start <= hour < end:
                return period
        return "night"  # fallback

    def _get_context_key(self, context: dict[str, Any]) -> str:
        """Generate a context key from context dictionary.

        Args:
            context: Context dictionary with time_of_day, day_of_week, etc.

        Returns:
            Context key string
        """
        time_period = self._get_time_period(context.get("time_of_day"))
        day_of_week = context.get("day_of_week", 0)  # 0=Monday, 6=Sunday

        # Simple context: time period + weekday/weekend
        is_weekend = day_of_week >= 5
        weekend_suffix = "_weekend" if is_weekend else "_weekday"

        return f"{time_period}{weekend_suffix}"

    def train(self) -> dict[str, Any]:
        """Train the preference model from interaction history.

        Returns:
            Dictionary with training statistics
        """
        # Reset weights
        self.preferences.clear()
        self.confidence.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get all interactions with feedback
                cursor.execute(
                    """
                    SELECT user_command, agent_action, context, user_feedback, corrected_command
                    FROM interaction_logs
                    WHERE user_feedback IS NOT NULL
                    ORDER BY timestamp DESC
                    """
                )

                corrections = cursor.fetchall()
                stats = {
                    "total_interactions": len(corrections),
                    "preferences_learned": 0,
                    "tools_updated": set(),
                }

                for row in corrections:
                    self._learn_from_interaction(row, stats)

                stats["tools_updated"] = list(stats["tools_updated"])
                return stats

        except sqlite3.Error as e:
            return {"error": f"Database error during training: {e}"}

    def _learn_from_interaction(self, interaction: dict[str, Any], stats: dict[str, Any]) -> None:
        """Learn from a single interaction with feedback.

        Args:
            interaction: Interaction row from database
            stats: Statistics dictionary to update
        """
        try:
            agent_action = json.loads(interaction["agent_action"])
            context = json.loads(interaction["context"])

            # Extract corrections from feedback
            feedback = interaction["user_feedback"]

            # If feedback is negative (-1), check for corrected command
            if feedback == -1 and interaction["corrected_command"]:
                self._learn_from_correction(agent_action, interaction["corrected_command"], context, stats)
            elif feedback == 1:
                # Positive feedback - reinforce the action
                self._reinforce_action(agent_action, context, stats)

        except (json.JSONDecodeError, KeyError):
            pass  # Skip malformed interactions

    def _learn_from_correction(
        self, agent_action: dict[str, Any], correction: str, context: dict[str, Any], stats: dict[str, Any]
    ) -> None:
        """Learn from a user correction.

        Args:
            agent_action: The action that was taken
            correction: User's corrected command
            context: Context at time of interaction
            stats: Statistics dictionary to update
        """
        # Try to extract parameter values from the correction
        import re

        # Look for temperature corrections (e.g., "24度", "24°C")
        temp_match = re.search(r"(\d+\.?\d*)\s*[度°C]", correction)
        if temp_match:
            corrected_temp = float(temp_match.group(1))
            context_key = self._get_context_key(context)

            # Increase weight for corrected temperature
            self.preferences["set_temperature"][context_key][corrected_temp] += 2.0
            self.confidence["set_temperature"][context_key][corrected_temp] += 1
            stats["preferences_learned"] += 1
            stats["tools_updated"].add("set_temperature")

        # Look for brightness corrections (e.g., "50%", "50percent")
        brightness_match = re.search(r"(\d+)\s*[%%]", correction)
        if brightness_match:
            corrected_brightness = int(brightness_match.group(1))
            context_key = self._get_context_key(context)

            self.preferences["set_light_brightness"][context_key][corrected_brightness] += 2.0
            self.confidence["set_light_brightness"][context_key][corrected_brightness] += 1
            stats["preferences_learned"] += 1
            stats["tools_updated"].add("set_light_brightness")

        # Look for fan speed corrections (e.g., "1档", "2档")
        speed_match = re.search(r"(\d+)\s*档", correction)
        if speed_match:
            corrected_speed = int(speed_match.group(1))
            context_key = self._get_context_key(context)

            self.preferences["set_fan_speed"][context_key][corrected_speed] += 2.0
            self.confidence["set_fan_speed"][context_key][corrected_speed] += 1
            stats["preferences_learned"] += 1
            stats["tools_updated"].add("set_fan_speed")

    def _reinforce_action(self, agent_action: dict[str, Any], context: dict[str, Any], stats: dict[str, Any]) -> None:
        """Reinforce an action that received positive feedback.

        Args:
            agent_action: The action that was taken
            context: Context at time of interaction
            stats: Statistics dictionary to update
        """
        if "actions" not in agent_action:
            return

        for action in agent_action["actions"]:
            tool_name = action.get("tool")
            arguments = action.get("arguments", {})

            if tool_name in self.LEARNABLE_PARAMS:
                param_name = self.LEARNABLE_PARAMS[tool_name]
                if param_name in arguments:
                    value = arguments[param_name]
                    context_key = self._get_context_key(context)

                    # Increase weight for the successful action
                    self.preferences[tool_name][context_key][value] += 1.0
                    self.confidence[tool_name][context_key][value] += 1
                    stats["preferences_learned"] += 1
                    stats["tools_updated"].add(tool_name)

    def predict(self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
        """Predict the preferred parameter value for a given context.

        Args:
            tool_name: The tool being called
            arguments: The proposed arguments from the LLM
            context: Current context

        Returns:
            Dictionary with suggested adjustments or None if no preference
        """
        if tool_name not in self.LEARNABLE_PARAMS:
            return None

        param_name = self.LEARNABLE_PARAMS[tool_name]
        if param_name not in arguments:
            return None

        context_key = self._get_context_key(context)
        current_value = arguments[param_name]

        # Get learned preferences for this context
        prefs = self.preferences.get(tool_name, {}).get(context_key, {})
        confs = self.confidence.get(tool_name, {}).get(context_key, {})

        if not prefs or not confs:
            return None

        # Find the value with highest confidence
        best_value = None
        best_confidence = 0

        for value, conf in confs.items():
            if conf > best_confidence:
                best_confidence = conf
                best_value = value

        # Only override if we have enough confidence and the value differs
        if best_confidence >= self.min_confidence and best_value != current_value:
            return {
                "parameter": param_name,
                "original_value": current_value,
                "suggested_value": best_value,
                "confidence": best_confidence,
                "context": context_key,
            }

        return None

    def adjust_arguments(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> tuple[dict[str, Any], str | None]:
        """Adjust arguments based on learned preferences.

        Args:
            tool_name: The tool being called
            arguments: The proposed arguments from the LLM
            context: Current context

        Returns:
            Tuple of (adjusted_arguments, explanation_message)
        """
        prediction = self.predict(tool_name, arguments, context)

        if prediction is None:
            return arguments, None

        # Create adjusted arguments
        adjusted = arguments.copy()
        param_name = prediction["parameter"]
        adjusted[param_name] = prediction["suggested_value"]

        # Generate explanation message
        tool_display_names = {
            "set_temperature": "温度",
            "set_light_brightness": "亮度",
            "set_fan_speed": "风速",
        }

        param_display = tool_display_names.get(tool_name, param_name)

        explanation = (
            f"🤖 根据您的习惯 ({prediction['context']}),"
            f"我已将{param_display}调整为 {prediction['suggested_value']}"
            f" (置信度: {prediction['confidence']})"
        )

        return adjusted, explanation

    def get_preference_summary(self) -> dict[str, Any]:
        """Get a summary of learned preferences.

        Returns:
            Dictionary with preference statistics
        """
        summary = {
            "tools": {},
            "total_preferences": 0,
        }

        for tool_name in self.LEARNABLE_PARAMS:
            tool_prefs = self.preferences.get(tool_name, {})
            tool_confs = self.confidence.get(tool_name, {})

            contexts = {}
            for context_key in tool_prefs:
                # Get top preferences for this context
                prefs = tool_prefs[context_key]
                confs = tool_confs[context_key]

                sorted_prefs = sorted(prefs.items(), key=lambda x: x[1], reverse=True)[:3]

                top_values = []
                for value, weight in sorted_prefs:
                    top_values.append({
                        "value": value,
                        "weight": weight,
                        "confidence": confs[value],
                    })

                contexts[context_key] = top_values
                summary["total_preferences"] += len(top_values)

            if contexts:
                summary["tools"][tool_name] = contexts

        return summary

    def save_preferences(self, filepath: str | None = None) -> str:
        """Save learned preferences to JSON file.

        Args:
            filepath: Path to save preferences. Defaults to data/preferences.json

        Returns:
            Path to saved file
        """
        if filepath is None:
            from pathlib import Path

            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(data_dir / "preferences.json")

        data = {
            "preferences": dict(self.preferences),
            "confidence": dict(self.confidence),
            "trained_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def load_preferences(self, filepath: str | None = None) -> bool:
        """Load learned preferences from JSON file.

        Args:
            filepath: Path to preferences file. Defaults to data/preferences.json

        Returns:
            True if loaded successfully, False otherwise
        """
        if filepath is None:
            from pathlib import Path

            data_dir = Path(__file__).parent.parent.parent / "data"
            filepath = str(data_dir / "preferences.json")

        try:
            with open(filepath) as f:
                data = json.load(f)

            self.preferences = defaultdict(
                lambda: defaultdict(lambda: defaultdict(float)),
                data.get("preferences", {})
            )
            self.confidence = defaultdict(
                lambda: defaultdict(lambda: defaultdict(int)),
                data.get("confidence", {})
            )

            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False


# Global instance for easy access
_default_model: PreferenceModel | None = None


def get_preference_model(db_path: str | None = None) -> PreferenceModel:
    """Get or create the default preference model instance.

    Args:
        db_path: Optional path to database file

    Returns:
        PreferenceModel instance
    """
    global _default_model
    if _default_model is None:
        _default_model = PreferenceModel(db_path)
    return _default_model
