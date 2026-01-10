"""智能家居模拟器 - 管理所有虚拟设备."""

from typing import Any

from smarthome_mock_ai.devices import (
    Curtain,
    Door,
    Fan,
    Light,
    SmartDevice,
    Thermostat,
)


class HomeSimulator:
    """家庭设备模拟器."""

    def __init__(self) -> None:
        """初始化模拟器和所有设备."""
        self.devices: dict[str, SmartDevice] = {}
        self._setup_default_devices()

    def _setup_default_devices(self) -> None:
        """设置默认设备配置."""
        # 灯光设备
        self.devices["living_room_light"] = Light(
            device_id="living_room_light",
            name="客厅灯",
            room="living_room",
        )
        self.devices["bedroom_light"] = Light(
            device_id="bedroom_light",
            name="卧室灯",
            room="bedroom",
        )
        self.devices["kitchen_light"] = Light(
            device_id="kitchen_light",
            name="厨房灯",
            room="kitchen",
        )
        self.devices["bathroom_light"] = Light(
            device_id="bathroom_light",
            name="浴室灯",
            room="bathroom",
        )

        # 温控器
        self.devices["thermostat"] = Thermostat(
            device_id="thermostat",
            name="主温控器",
            room="living_room",
        )

        # 门锁
        self.devices["front_door"] = Door(
            device_id="front_door",
            name="前门",
            location="entrance",
        )
        self.devices["back_door"] = Door(
            device_id="back_door",
            name="后门",
            location="backyard",
        )

        # 风扇
        self.devices["living_room_fan"] = Fan(
            device_id="living_room_fan",
            name="客厅风扇",
            room="living_room",
        )
        self.devices["bedroom_fan"] = Fan(
            device_id="bedroom_fan",
            name="卧室风扇",
            room="bedroom",
        )

        # 窗帘
        self.devices["living_room_curtain"] = Curtain(
            device_id="living_room_curtain",
            name="客厅窗帘",
            room="living_room",
        )
        self.devices["bedroom_curtain"] = Curtain(
            device_id="bedroom_curtain",
            name="卧室窗帘",
            room="bedroom",
        )

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

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """获取所有设备状态."""
        return {device_id: device.get_status().state for device_id, device in self.devices.items()}

    def reset_all(self) -> None:
        """重置所有设备."""
        for device in self.devices.values():
            device.reset()

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
