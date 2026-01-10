"""虚拟智能家居设备类定义."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class DeviceType(Enum):
    """设备类型枚举."""

    LIGHT = "light"
    THERMOSTAT = "thermostat"
    DOOR = "door"
    FAN = "fan"
    CURTAIN = "curtain"


class DeviceState(Enum):
    """设备状态枚举."""

    ON = "on"
    OFF = "off"
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class DeviceStatus:
    """设备状态数据类."""

    device_id: str
    device_type: DeviceType
    state: dict[str, Any]

    def __str__(self) -> str:
        """返回状态字符串表示."""
        state_str = ", ".join(f"{k}={v}" for k, v in self.state.items())
        return f"{self.device_type.value}[{self.device_id}]: {state_str}"


class SmartDevice(ABC):
    """智能设备抽象基类."""

    def __init__(self, device_id: str, name: str) -> None:
        """初始化设备.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
        """
        self.device_id = device_id
        self.name = name
        self._state: dict[str, Any] = {}

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """返回设备类型."""

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        """获取设备当前状态."""

    @abstractmethod
    def reset(self) -> None:
        """重置设备到初始状态."""


class Light(SmartDevice):
    """智能灯光设备."""

    def __init__(self, device_id: str, name: str, room: str) -> None:
        """初始化灯光设备.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
            room: 所在房间
        """
        super().__init__(device_id, name)
        self.room = room
        self._is_on = False
        self._brightness = 100  # 0-100
        self._color = "white"

    @property
    def device_type(self) -> DeviceType:
        """返回设备类型."""
        return DeviceType.LIGHT

    def turn_on(self) -> None:
        """打开灯光."""
        self._is_on = True

    def turn_off(self) -> None:
        """关闭灯光."""
        self._is_on = False

    def set_brightness(self, level: int) -> None:
        """设置亮度.

        Args:
            level: 亮度级别 (0-100)
        """
        if not 0 <= level <= 100:
            msg = "亮度必须在 0-100 之间"
            raise ValueError(msg)
        self._brightness = level
        if level > 0:
            self._is_on = True

    def set_color(self, color: str) -> None:
        """设置颜色.

        Args:
            color: 颜色名称或十六进制值
        """
        self._color = color

    def get_status(self) -> DeviceStatus:
        """获取设备状态."""
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state={
                "name": self.name,
                "room": self.room,
                "is_on": self._is_on,
                "brightness": self._brightness,
                "color": self._color,
            },
        )

    def reset(self) -> None:
        """重置设备状态."""
        self._is_on = False
        self._brightness = 100
        self._color = "white"


class Thermostat(SmartDevice):
    """智能温控器设备."""

    def __init__(self, device_id: str, name: str, room: str) -> None:
        """初始化温控器.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
            room: 所在房间
        """
        super().__init__(device_id, name)
        self.room = room
        self._current_temp = 22.0  # 摄氏度
        self._target_temp = 22.0
        self._mode = "auto"  # auto, heat, cool, off

    @property
    def device_type(self) -> DeviceType:
        """返回设备类型."""
        return DeviceType.THERMOSTAT

    def set_temperature(self, temp: float) -> None:
        """设置目标温度.

        Args:
            temp: 目标温度 (摄氏度)
        """
        if not 16 <= temp <= 30:
            msg = "温度必须在 16-30°C 之间"
            raise ValueError(msg)
        self._target_temp = temp
        if self._mode == "off":
            self._mode = "auto"

    def set_mode(self, mode: str) -> None:
        """设置温控模式.

        Args:
            mode: 模式 (auto, heat, cool, off)
        """
        valid_modes = ["auto", "heat", "cool", "off"]
        if mode not in valid_modes:
            msg = f"无效的模式,必须是: {', '.join(valid_modes)}"
            raise ValueError(msg)
        self._mode = mode

    def get_status(self) -> DeviceStatus:
        """获取设备状态."""
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state={
                "name": self.name,
                "room": self.room,
                "current_temp": self._current_temp,
                "target_temp": self._target_temp,
                "mode": self._mode,
            },
        )

    def reset(self) -> None:
        """重置设备状态."""
        self._current_temp = 22.0
        self._target_temp = 22.0
        self._mode = "auto"


class Door(SmartDevice):
    """智能门锁设备."""

    def __init__(self, device_id: str, name: str, location: str) -> None:
        """初始化门锁.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
            location: 位置
        """
        super().__init__(device_id, name)
        self.location = location
        self._is_locked = True
        self._is_closed = True

    @property
    def device_type(self) -> DeviceType:
        """返回设备类型."""
        return DeviceType.DOOR

    def lock(self) -> None:
        """锁门."""
        self._is_locked = True

    def unlock(self) -> None:
        """解锁."""
        self._is_locked = False

    def open(self) -> None:
        """开门."""
        if self._is_locked:
            msg = "门已锁定,无法打开"
            raise RuntimeError(msg)
        self._is_closed = False

    def close(self) -> None:
        """关门."""
        self._is_closed = True

    def get_status(self) -> DeviceStatus:
        """获取设备状态."""
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state={
                "name": self.name,
                "location": self.location,
                "is_locked": self._is_locked,
                "is_closed": self._is_closed,
            },
        )

    def reset(self) -> None:
        """重置设备状态."""
        self._is_locked = True
        self._is_closed = True


class Fan(SmartDevice):
    """智能风扇设备."""

    def __init__(self, device_id: str, name: str, room: str) -> None:
        """初始化风扇.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
            room: 所在房间
        """
        super().__init__(device_id, name)
        self.room = room
        self._is_on = False
        self._speed = 1  # 1-3

    @property
    def device_type(self) -> DeviceType:
        """返回设备类型."""
        return DeviceType.FAN

    def turn_on(self) -> None:
        """打开风扇."""
        self._is_on = True

    def turn_off(self) -> None:
        """关闭风扇."""
        self._is_on = False

    def set_speed(self, speed: int) -> None:
        """设置风速.

        Args:
            speed: 风速等级 (1-3)
        """
        if not 1 <= speed <= 3:
            msg = "风速必须在 1-3 之间"
            raise ValueError(msg)
        self._speed = speed
        self._is_on = True

    def get_status(self) -> DeviceStatus:
        """获取设备状态."""
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state={
                "name": self.name,
                "room": self.room,
                "is_on": self._is_on,
                "speed": self._speed,
            },
        )

    def reset(self) -> None:
        """重置设备状态."""
        self._is_on = False
        self._speed = 1


class Curtain(SmartDevice):
    """智能窗帘设备."""

    def __init__(self, device_id: str, name: str, room: str) -> None:
        """初始化窗帘.

        Args:
            device_id: 设备唯一标识符
            name: 设备名称
            room: 所在房间
        """
        super().__init__(device_id, name)
        self.room = room
        self._position = 0  # 0=closed, 100=open

    @property
    def device_type(self) -> DeviceType:
        """返回设备类型."""
        return DeviceType.CURTAIN

    def open(self) -> None:
        """完全打开窗帘."""
        self._position = 100

    def close(self) -> None:
        """完全关闭窗帘."""
        self._position = 0

    def set_position(self, position: int) -> None:
        """设置窗帘位置.

        Args:
            position: 位置百分比 (0-100)
        """
        if not 0 <= position <= 100:
            msg = "位置必须在 0-100 之间"
            raise ValueError(msg)
        self._position = position

    def get_status(self) -> DeviceStatus:
        """获取设备状态."""
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state={
                "name": self.name,
                "room": self.room,
                "position": self._position,
            },
        )

    def reset(self) -> None:
        """重置设备状态."""
        self._position = 0
