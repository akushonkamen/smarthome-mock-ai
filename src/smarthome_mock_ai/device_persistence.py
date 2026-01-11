"""Device State Persistence - Save and load device states to/from JSON."""

import json
from pathlib import Path
from typing import Any

from smarthome_mock_ai.devices import (
    Curtain,
    DeviceType,
    Door,
    Fan,
    Light,
    SmartDevice,
    Thermostat,
)


class DeviceStateManager:
    """Manages device state persistence to/from JSON files."""

    def __init__(self, state_file: str | None = None) -> None:
        """Initialize the device state manager.

        Args:
            state_file: Path to JSON file for storing device states.
                        Defaults to data/devices.json
        """
        if state_file is None:
            # Create data directory if it doesn't exist
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            state_file = str(data_dir / "devices.json")

        self.state_file = state_file

    def save_states(self, devices: dict[str, SmartDevice]) -> bool:
        """Save device states to JSON file.

        Args:
            devices: Dictionary of device_id to SmartDevice instances

        Returns:
            True if save was successful, False otherwise
        """
        try:
            states = {}
            for device_id, device in devices.items():
                status = device.get_status()
                # Store the state dict with device type info
                states[device_id] = {
                    "device_type": status.device_type.value,
                    "state": status.state,
                }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(states, f, ensure_ascii=False, indent=2)

            return True
        except (IOError, OSError) as e:
            print(f"Warning: Failed to save device states: {e}")
            return False

    def load_states(self) -> dict[str, Any] | None:
        """Load device states from JSON file.

        Returns:
            Dictionary of device_id to state data, or None if file doesn't exist
        """
        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load device states: {e}")
            return None

    def apply_states_to_devices(
        self, devices: dict[str, SmartDevice], states: dict[str, Any]
    ) -> int:
        """Apply loaded states to device instances.

        Args:
            devices: Dictionary of device_id to SmartDevice instances
            states: Dictionary of device_id to state data from load_states()

        Returns:
            Number of devices successfully updated
        """
        updated_count = 0

        for device_id, device in devices.items():
            if device_id not in states:
                continue

            state_data = states[device_id]
            state = state_data.get("state", {})

            try:
                # Apply state based on device type
                if isinstance(device, Light):
                    self._apply_light_state(device, state)
                elif isinstance(device, Thermostat):
                    self._apply_thermostat_state(device, state)
                elif isinstance(device, Fan):
                    self._apply_fan_state(device, state)
                elif isinstance(device, Curtain):
                    self._apply_curtain_state(device, state)
                elif isinstance(device, Door):
                    self._apply_door_state(device, state)

                updated_count += 1
            except (ValueError, KeyError) as e:
                print(f"Warning: Failed to apply state to {device_id}: {e}")

        return updated_count

    def _apply_light_state(self, device: Light, state: dict[str, Any]) -> None:
        """Apply state to a Light device."""
        if "brightness" in state:
            device.set_brightness(state["brightness"])
        if "color" in state:
            device.set_color(state["color"])
        if state.get("is_on", False):
            device.turn_on()
        else:
            device.turn_off()

    def _apply_thermostat_state(self, device: Thermostat, state: dict[str, Any]) -> None:
        """Apply state to a Thermostat device."""
        if "target_temp" in state:
            device.set_temperature(state["target_temp"])
        if "mode" in state:
            device.set_mode(state["mode"])

    def _apply_fan_state(self, device: Fan, state: dict[str, Any]) -> None:
        """Apply state to a Fan device."""
        if "speed" in state:
            device.set_speed(state["speed"])
        if state.get("is_on", False):
            device.turn_on()
        else:
            device.turn_off()

    def _apply_curtain_state(self, device: Curtain, state: dict[str, Any]) -> None:
        """Apply state to a Curtain device."""
        if "position" in state:
            device.set_position(state["position"])

    def _apply_door_state(self, device: Door, state: dict[str, Any]) -> None:
        """Apply state to a Door device."""
        if state.get("is_locked", True):
            device.lock()
        else:
            device.unlock()
        # Note: door open/close is not persisted as it requires unlock first

    def backup_states(self) -> str | None:
        """Create a backup of current states file.

        Returns:
            Path to backup file, or None if backup failed
        """
        try:
            backup_path = f"{self.state_file}.backup"
            with open(self.state_file, encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            return backup_path
        except (IOError, OSError):
            return None


# Global instance for easy access
_default_manager: DeviceStateManager | None = None


def get_device_state_manager(state_file: str | None = None) -> DeviceStateManager:
    """Get or create the default device state manager instance.

    Args:
        state_file: Optional path to state file

    Returns:
        DeviceStateManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = DeviceStateManager(state_file)
    return _default_manager
