"""智能家居模拟器 - 动态设备注册和管理系统."""

from typing import Any

from smarthome_mock_ai.device_persistence import DeviceStateManager, get_device_state_manager
from smarthome_mock_ai.devices import (
    Curtain,
    DeviceMetadata,
    Door,
    Fan,
    Light,
    SmartDevice,
    Thermostat,
)


class HomeSimulator:
    """家庭设备模拟器 - 支持动态设备注册."""

    def __init__(self, persist_state: bool = True, state_file: str | None = None) -> None:
        """初始化模拟器.

        Args:
            persist_state: Whether to save/load device states from file
            state_file: Optional path to state file (defaults to data/devices.json)
        """
        self.devices: dict[str, SmartDevice] = {}
        self.persist_state = persist_state
        self.state_manager = get_device_state_manager(state_file) if persist_state else None
        # Note: No longer calling _setup_default_devices here
        # Devices must be registered via register_device() method
        self._load_states()

    # ========== 设备注册管理 ==========

    def register_device(self, device: SmartDevice) -> str:
        """注册一个新设备到系统中.

        Args:
            device: 设备实例

        Returns:
            注册的设备ID

        Raises:
            ValueError: 如果设备ID已存在
        """
        if device.device_id in self.devices:
            msg = f"设备ID '{device.device_id}' 已存在"
            raise ValueError(msg)

        self.devices[device.device_id] = device
        self._save_after_action()
        return device.device_id

    def unregister_device(self, device_id: str) -> bool:
        """从系统中注销一个设备.

        Args:
            device_id: 要注销的设备ID

        Returns:
            True if device was unregistered, False if device not found
        """
        if device_id not in self.devices:
            return False

        del self.devices[device_id]
        self._save_after_action()
        return True

    def get_device_details(self, device_id: str) -> dict[str, Any] | None:
        """获取设备的完整元数据和当前状态.

        Args:
            device_id: 设备ID

        Returns:
            包含 metadata 和 current_state 的字典,如果设备不存在返回 None
        """
        if device_id not in self.devices:
            return None

        device = self.devices[device_id]
        metadata = device.get_metadata()
        status = device.get_status()

        return {
            "metadata": metadata.to_dict(),
            "current_state": status.state,
        }

    # ========== 设备查询方法 ==========

    def get_device(self, device_id: str) -> SmartDevice:
        """获取设备.

        Args:
            device_id: 设备ID

        Returns:
            设备实例

        Raises:
            KeyError: 设备不存在
        """
        if device_id not in self.devices:
            msg = f"设备 '{device_id}' 不存在"
            raise KeyError(msg)
        return self.devices[device_id]

    def list_all_devices(self) -> list[str]:
        """列出所有设备ID."""
        return list(self.devices.keys())

    def list_devices_by_type(self, device_type: str) -> list[str]:
        """按类型列出设备ID.

        Args:
            device_type: 设备类型 (light, thermostat, door, fan, curtain)

        Returns:
            匹配类型的设备ID列表
        """
        result = []
        for device_id, device in self.devices.items():
            if device.device_type.value == device_type:
                result.append(device_id)
        return result

    def list_devices_by_location(self, location: str) -> list[str]:
        """按位置列出设备ID.

        Args:
            location: 位置/房间名称

        Returns:
            匹配位置的设备ID列表
        """
        result = []
        for device_id, device in self.devices.items():
            if device.location == location:
                result.append(device_id)
        return result

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        """获取所有设备的元数据.

        Returns:
            设备ID到元数据字典的映射
        """
        return {device_id: device.get_metadata().to_dict() for device_id, device in self.devices.items()}

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """获取所有设备状态."""
        return {device_id: device.get_status().state for device_id, device in self.devices.items()}

    def reset_all(self) -> None:
        """重置所有设备."""
        for device in self.devices.values():
            device.reset()

    # ========== 状态持久化方法 ==========

    def _load_states(self) -> None:
        """Load device states from file if persistence is enabled."""
        if not self.persist_state or self.state_manager is None:
            return

        states = self.state_manager.load_states()
        if states:
            updated = self.state_manager.apply_states_to_devices(self.devices, states)
            if updated > 0:
                print(f"✓ 已从文件加载 {updated} 个设备的状态")

    def save_states(self) -> bool:
        """Save current device states to file.

        Returns:
            True if save was successful, False otherwise
        """
        if not self.persist_state or self.state_manager is None:
            return False

        return self.state_manager.save_states(self.devices)

    def _save_after_action(self) -> None:
        """Save states after an action (internal method)."""
        if self.persist_state:
            self.save_states()

    # ========== 便捷操作方法 ==========

    def turn_on_light(self, device_id: str) -> str:
        """打开灯光.

        Args:
            device_id: 灯光设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Light):
            return f"错误: 设备 '{device_id}' 不是灯光设备"
        device.turn_on()
        self._save_after_action()
        return f"✓ 已打开 {device.name}"

    def turn_off_light(self, device_id: str) -> str:
        """关闭灯光.

        Args:
            device_id: 灯光设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Light):
            return f"错误: 设备 '{device_id}' 不是灯光设备"
        device.turn_off()
        self._save_after_action()
        return f"✓ 已关闭 {device.name}"

    def set_light_brightness(self, device_id: str, level: int) -> str:
        """设置灯光亮度.

        Args:
            device_id: 灯光设备ID
            level: 亮度级别 (0-100)

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Light):
            return f"错误: 设备 '{device_id}' 不是灯光设备"
        device.set_brightness(level)
        self._save_after_action()
        return f"✓ {device.name} 亮度已设置为 {level}%"

    def set_light_color(self, device_id: str, color: str) -> str:
        """设置灯光颜色.

        Args:
            device_id: 灯光设备ID
            color: 颜色

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Light):
            return f"错误: 设备 '{device_id}' 不是灯光设备"
        device.set_color(color)
        self._save_after_action()
        return f"✓ {device.name} 颜色已设置为 {color}"

    def set_temperature(self, device_id: str, temp: float) -> str:
        """设置温度.

        Args:
            device_id: 温控器设备ID
            temp: 目标温度

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Thermostat):
            return f"错误: 设备 '{device_id}' 不是温控器"
        device.set_temperature(temp)
        self._save_after_action()
        return f"✓ {device.name} 温度已设置为 {temp}°C"

    def turn_on_fan(self, device_id: str) -> str:
        """打开风扇.

        Args:
            device_id: 风扇设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Fan):
            return f"错误: 设备 '{device_id}' 不是风扇设备"
        device.turn_on()
        self._save_after_action()
        return f"✓ 已打开 {device.name}"

    def turn_off_fan(self, device_id: str) -> str:
        """关闭风扇.

        Args:
            device_id: 风扇设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Fan):
            return f"错误: 设备 '{device_id}' 不是风扇设备"
        device.turn_off()
        self._save_after_action()
        return f"✓ 已关闭 {device.name}"

    def set_fan_speed(self, device_id: str, speed: int) -> str:
        """设置风扇速度.

        Args:
            device_id: 风扇设备ID
            speed: 速度等级 (1-3)

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Fan):
            return f"错误: 设备 '{device_id}' 不是风扇设备"
        device.set_speed(speed)
        self._save_after_action()
        return f"✓ {device.name} 速度已设置为 {speed}"

    def open_curtain(self, device_id: str) -> str:
        """打开窗帘.

        Args:
            device_id: 窗帘设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Curtain):
            return f"错误: 设备 '{device_id}' 不是窗帘"
        device.open()
        self._save_after_action()
        return f"✓ 已打开 {device.name}"

    def close_curtain(self, device_id: str) -> str:
        """关闭窗帘.

        Args:
            device_id: 窗帘设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Curtain):
            return f"错误: 设备 '{device_id}' 不是窗帘"
        device.close()
        self._save_after_action()
        return f"✓ 已关闭 {device.name}"

    def lock_door(self, device_id: str) -> str:
        """锁门.

        Args:
            device_id: 门锁设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Door):
            return f"错误: 设备 '{device_id}' 不是门锁"
        device.lock()
        self._save_after_action()
        return f"✓ 已锁定 {device.name}"

    def unlock_door(self, device_id: str) -> str:
        """解锁门.

        Args:
            device_id: 门锁设备ID

        Returns:
            操作结果消息
        """
        device = self.get_device(device_id)
        if not isinstance(device, Door):
            return f"错误: 设备 '{device_id}' 不是门锁"
        device.unlock()
        self._save_after_action()
        return f"✓ 已解锁 {device.name}"

    # ========== 批量操作 ==========

    def turn_off_all_lights(self) -> list[str]:
        """关闭所有灯光."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Light):
                results.append(self.turn_off_light(device_id))
        return results

    def turn_on_all_lights(self) -> list[str]:
        """打开所有灯光."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Light):
                results.append(self.turn_on_light(device_id))
        return results

    def lock_all_doors(self) -> list[str]:
        """锁定所有门."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Door):
                results.append(self.lock_door(device_id))
        return results

    def unlock_all_doors(self) -> list[str]:
        """解锁所有门."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Door):
                results.append(self.unlock_door(device_id))
        return results

    def close_all_curtains(self) -> list[str]:
        """关闭所有窗帘."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Curtain):
                results.append(self.close_curtain(device_id))
        return results

    def open_all_curtains(self) -> list[str]:
        """打开所有窗帘."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Curtain):
                results.append(self.open_curtain(device_id))
        return results

    def turn_off_all_fans(self) -> list[str]:
        """关闭所有风扇."""
        results = []
        for device_id in self.devices:
            device = self.devices[device_id]
            if isinstance(device, Fan):
                results.append(self.turn_off_fan(device_id))
        return results
