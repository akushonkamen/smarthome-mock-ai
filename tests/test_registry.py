"""Tests for dynamic device registry functionality."""

import pytest

from smarthome_mock_ai.devices import DeviceType, Light, Thermostat
from smarthome_mock_ai.simulator import HomeSimulator


class TestDeviceRegistry:
    """Test dynamic device registration and management."""

    @pytest.fixture
    def empty_simulator(self):
        """Create a simulator without default devices."""
        return HomeSimulator(persist_state=False)

    def test_register_single_device(self, empty_simulator):
        """Test registering a single device."""
        device = Light(device_id="test_light", name="Test Light", room="test_room")
        device_id = empty_simulator.register_device(device)

        assert device_id == "test_light"
        assert "test_light" in empty_simulator.list_all_devices()
        assert empty_simulator.get_device("test_light") is device

    def test_register_multiple_devices(self, empty_simulator):
        """Test registering multiple devices."""
        devices = [
            Light(device_id="light1", name="Light 1", room="room1"),
            Light(device_id="light2", name="Light 2", room="room2"),
            Thermostat(device_id="therm1", name="Thermo 1", room="room1"),
        ]

        for device in devices:
            empty_simulator.register_device(device)

        assert len(empty_simulator.list_all_devices()) == 3
        assert "light1" in empty_simulator.list_all_devices()
        assert "light2" in empty_simulator.list_all_devices()
        assert "therm1" in empty_simulator.list_all_devices()

    def test_register_duplicate_device_id_raises_error(self, empty_simulator):
        """Test that registering a device with duplicate ID raises ValueError."""
        device1 = Light(device_id="dup_light", name="Light 1", room="room1")
        device2 = Light(device_id="dup_light", name="Light 2", room="room2")

        empty_simulator.register_device(device1)

        with pytest.raises(ValueError, match="设备ID 'dup_light' 已存在"):
            empty_simulator.register_device(device2)

    def test_unregister_existing_device(self, empty_simulator):
        """Test unregistering an existing device."""
        device = Light(device_id="test_light", name="Test Light", room="test_room")
        empty_simulator.register_device(device)

        assert empty_simulator.unregister_device("test_light") is True
        assert "test_light" not in empty_simulator.list_all_devices()

    def test_unregister_nonexistent_device(self, empty_simulator):
        """Test unregistering a non-existent device."""
        assert empty_simulator.unregister_device("nonexistent") is False

    def test_get_device_details_existing(self, empty_simulator):
        """Test getting details for an existing device."""
        device = Light(device_id="test_light", name="Test Light", room="test_room")
        empty_simulator.register_device(device)
        device.turn_on()

        details = empty_simulator.get_device_details("test_light")

        assert details is not None
        assert "metadata" in details
        assert "current_state" in details
        assert details["metadata"]["device_id"] == "test_light"
        assert details["metadata"]["name"] == "Test Light"
        assert details["metadata"]["device_type"] == "light"
        assert details["metadata"]["capabilities"] == ["turn_on", "turn_off", "set_brightness", "set_color"]
        assert details["metadata"]["location"] == "test_room"
        assert details["current_state"]["is_on"] is True

    def test_get_device_details_nonexistent(self, empty_simulator):
        """Test getting details for a non-existent device."""
        assert empty_simulator.get_device_details("nonexistent") is None

    def test_list_devices_by_type(self, empty_simulator):
        """Test listing devices by type."""
        empty_simulator.register_device(Light(device_id="light1", name="L1", room="r1"))
        empty_simulator.register_device(Light(device_id="light2", name="L2", room="r2"))
        empty_simulator.register_device(Thermostat(device_id="therm1", name="T1", room="r1"))

        lights = empty_simulator.list_devices_by_type("light")
        therms = empty_simulator.list_devices_by_type("thermostat")
        fans = empty_simulator.list_devices_by_type("fan")

        assert len(lights) == 2
        assert "light1" in lights
        assert "light2" in lights
        assert len(therms) == 1
        assert "therm1" in therms
        assert len(fans) == 0

    def test_list_devices_by_location(self, empty_simulator):
        """Test listing devices by location."""
        empty_simulator.register_device(Light(device_id="light1", name="L1", room="living_room"))
        empty_simulator.register_device(Light(device_id="light2", name="L2", room="bedroom"))
        empty_simulator.register_device(Thermostat(device_id="therm1", name="T1", room="living_room"))

        living_room = empty_simulator.list_devices_by_location("living_room")
        bedroom = empty_simulator.list_devices_by_location("bedroom")

        assert len(living_room) == 2
        assert "light1" in living_room
        assert "therm1" in living_room
        assert len(bedroom) == 1
        assert "light2" in bedroom

    def test_get_all_metadata(self, empty_simulator):
        """Test getting metadata for all devices."""
        empty_simulator.register_device(Light(device_id="light1", name="L1", room="r1"))
        empty_simulator.register_device(Thermostat(device_id="therm1", name="T1", room="r1"))

        metadata = empty_simulator.get_all_metadata()

        assert len(metadata) == 2
        assert "light1" in metadata
        assert "therm1" in metadata
        assert metadata["light1"]["device_type"] == "light"
        assert metadata["therm1"]["device_type"] == "thermostat"
        assert "turn_on" in metadata["light1"]["capabilities"]
        assert "set_temperature" in metadata["therm1"]["capabilities"]

    def test_device_capabilities_property(self, empty_simulator):
        """Test that devices expose their capabilities."""
        light = Light(device_id="light1", name="L1", room="r1")
        thermostat = Thermostat(device_id="therm1", name="T1", room="r1")

        empty_simulator.register_device(light)
        empty_simulator.register_device(thermostat)

        light_details = empty_simulator.get_device_details("light1")
        therm_details = empty_simulator.get_device_details("therm1")

        assert "turn_on" in light_details["metadata"]["capabilities"]
        assert "turn_off" in light_details["metadata"]["capabilities"]
        assert "set_brightness" in light_details["metadata"]["capabilities"]
        assert "set_color" in light_details["metadata"]["capabilities"]

        assert "set_temperature" in therm_details["metadata"]["capabilities"]
        assert "set_mode" in therm_details["metadata"]["capabilities"]

    def test_device_metadata_to_dict(self, empty_simulator):
        """Test DeviceMetadata.to_dict() method."""
        device = Light(device_id="test_light", name="Test Light", room="test_room")
        empty_simulator.register_device(device)

        details = empty_simulator.get_device_details("test_light")
        metadata_dict = details["metadata"]

        # Verify all metadata fields are present
        assert metadata_dict["device_id"] == "test_light"
        assert metadata_dict["name"] == "Test Light"
        assert metadata_dict["device_type"] == "light"
        assert metadata_dict["location"] == "test_room"
        assert metadata_dict["model"] == "Light"
        assert metadata_dict["manufacturer"] == "SmartHome AI"
        assert isinstance(metadata_dict["capabilities"], list)

    def test_get_device_raises_keyerror_for_nonexistent(self, empty_simulator):
        """Test that get_device raises KeyError for non-existent device."""
        with pytest.raises(KeyError, match="设备 'nonexistent' 不存在"):
            empty_simulator.get_device("nonexistent")


class TestDeviceRegistryIntegration:
    """Integration tests for device registry with existing functionality."""

    @pytest.fixture
    def empty_simulator(self):
        """Create a simulator without default devices."""
        return HomeSimulator(persist_state=False)

    @pytest.fixture
    def simulator_with_devices(self):
        """Create a simulator with some devices registered."""
        sim = HomeSimulator(persist_state=False)
        sim.register_device(Light(device_id="l1", name="Light 1", room="r1"))
        sim.register_device(Light(device_id="l2", name="Light 2", room="r2"))
        sim.register_device(Thermostat(device_id="t1", name="Thermo 1", room="r1"))
        return sim

    def test_device_operations_work_after_registration(self, simulator_with_devices):
        """Test that device operations work correctly on registered devices."""
        # Turn on a light
        result = simulator_with_devices.turn_on_light("l1")
        assert "已打开" in result

        # Set temperature
        result = simulator_with_devices.set_temperature("t1", 25.0)
        assert "25" in result

        # Verify states are correct
        device = simulator_with_devices.get_device("l1")
        assert device.get_status().state["is_on"] is True

    def test_batch_operations_with_registered_devices(self, simulator_with_devices):
        """Test batch operations work with dynamically registered devices."""
        results = simulator_with_devices.turn_off_all_lights()
        assert len(results) == 2
        for result in results:
            assert "已关闭" in result

    def test_get_all_statuses_with_registered_devices(self, simulator_with_devices):
        """Test get_all_statuses works with registered devices."""
        statuses = simulator_with_devices.get_all_statuses()

        assert len(statuses) == 3
        assert "l1" in statuses
        assert "l2" in statuses
        assert "t1" in statuses

    def test_reset_all_with_registered_devices(self, simulator_with_devices):
        """Test reset_all works with registered devices."""
        # Modify some states
        simulator_with_devices.turn_on_light("l1")
        simulator_with_devices.set_temperature("t1", 26.0)

        # Reset all
        simulator_with_devices.reset_all()

        # Verify reset
        l1_status = simulator_with_devices.get_device("l1").get_status().state
        t1_status = simulator_with_devices.get_device("t1").get_status().state
        assert l1_status["is_on"] is False
        assert t1_status["target_temp"] == 22.0

    def test_register_and_unregister_sequence(self, empty_simulator):
        """Test a sequence of register and unregister operations."""
        # Register devices
        devices = [
            Light(device_id=f"light{i}", name=f"Light {i}", room=f"room{i}")
            for i in range(5)
        ]
        for device in devices:
            empty_simulator.register_device(device)

        assert len(empty_simulator.list_all_devices()) == 5

        # Unregister some devices
        empty_simulator.unregister_device("light1")
        empty_simulator.unregister_device("light3")

        assert len(empty_simulator.list_all_devices()) == 3
        assert "light1" not in empty_simulator.list_all_devices()
        assert "light3" not in empty_simulator.list_all_devices()
        assert "light0" in empty_simulator.list_all_devices()
        assert "light2" in empty_simulator.list_all_devices()
        assert "light4" in empty_simulator.list_all_devices()

        # Register new device
        new_light = Light(device_id="new_light", name="New", room="new_room")
        empty_simulator.register_device(new_light)

        assert len(empty_simulator.list_all_devices()) == 4
        assert "new_light" in empty_simulator.list_all_devices()
