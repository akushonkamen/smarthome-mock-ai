"""AI Agent - 使用 LLM 和 Function Calling 控制智能家居."""

import json
import os
from typing import Any

import httpx


class SmartHomeAgent:
    """智能家居 AI Agent."""

    # API 配置
    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    @property
    def API_KEY(self) -> str:
        """获取 API Key."""
        return os.getenv("ZHIPU_API_KEY", "")

    def __init__(self, simulator: Any) -> None:
        """初始化 Agent.

        Args:
            simulator: HomeSimulator 实例
        """
        self.simulator = simulator
        self.tools = self._define_tools()

    def _define_tools(self) -> list[dict[str, Any]]:
        """定义可用的工具/函数.

        Returns:
            工具定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "turn_on_light",
                    "description": "打开指定的灯光设备",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": [
                                    "living_room_light",
                                    "bedroom_light",
                                    "kitchen_light",
                                    "bathroom_light",
                                ],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "turn_off_light",
                    "description": "关闭指定的灯光设备",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": [
                                    "living_room_light",
                                    "bedroom_light",
                                    "kitchen_light",
                                    "bathroom_light",
                                ],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_light_brightness",
                    "description": "设置灯光的亮度级别",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": [
                                    "living_room_light",
                                    "bedroom_light",
                                    "kitchen_light",
                                    "bathroom_light",
                                ],
                            },
                            "level": {
                                "type": "integer",
                                "description": "亮度级别,范围 0-100,0为关闭,100为最亮",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["device_id", "level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_light_color",
                    "description": "设置灯光的颜色",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": [
                                    "living_room_light",
                                    "bedroom_light",
                                    "kitchen_light",
                                    "bathroom_light",
                                ],
                            },
                            "color": {
                                "type": "string",
                                "description": "颜色名称或十六进制值 (例如: red, blue, white)",
                            },
                        },
                        "required": ["device_id", "color"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_temperature",
                    "description": "设置温控器的目标温度",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "温控器设备ID",
                                "enum": ["thermostat"],
                            },
                            "temp": {
                                "type": "number",
                                "description": "目标温度 (摄氏度),范围 16-30",
                                "minimum": 16,
                                "maximum": 30,
                            },
                        },
                        "required": ["device_id", "temp"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "turn_on_fan",
                    "description": "打开指定的风扇设备",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": ["living_room_fan", "bedroom_fan"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "turn_off_fan",
                    "description": "关闭指定的风扇设备",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": ["living_room_fan", "bedroom_fan"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_fan_speed",
                    "description": "设置风扇的速度等级",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": ["living_room_fan", "bedroom_fan"],
                            },
                            "speed": {
                                "type": "integer",
                                "description": "速度等级,1为低速,2为中速,3为高速",
                                "minimum": 1,
                                "maximum": 3,
                            },
                        },
                        "required": ["device_id", "speed"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_curtain",
                    "description": "打开指定的窗帘",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "窗帘设备ID",
                                "enum": ["living_room_curtain", "bedroom_curtain"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "close_curtain",
                    "description": "关闭指定的窗帘",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "窗帘设备ID",
                                "enum": ["living_room_curtain", "bedroom_curtain"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_door",
                    "description": "锁定指定的门",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "门锁设备ID",
                                "enum": ["front_door", "back_door"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "unlock_door",
                    "description": "解锁指定的门",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "门锁设备ID",
                                "enum": ["front_door", "back_door"],
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "turn_off_all_lights",
                    "description": "关闭所有的灯光设备 (通常用于睡觉、离家等场景)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_device_statuses",
                    "description": "获取所有设备的当前状态",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]

    def _build_system_prompt(self) -> str:
        """构建系统提示词.

        Returns:
            系统提示词字符串
        """
        devices_info = "\n".join(self.simulator.list_all_devices())
        return (
            f"你是一个智能家居控制助手。用户会用自然语言描述"
            f"他们的需求,你需要理解并控制相应的设备。\n\n"
            f"可用设备列表:\n{devices_info}\n\n"
            f"设备ID说明:\n"
            f"- 灯光: living_room_light(客厅灯), bedroom_light(卧室灯), "
            f"kitchen_light(厨房灯), bathroom_light(浴室灯)\n"
            f"- 温控器: thermostat(主温控器)\n"
            f"- 风扇: living_room_fan(客厅风扇), bedroom_fan(卧室风扇)\n"
            f"- 窗帘: living_room_curtain(客厅窗帘), bedroom_curtain(卧室窗帘)\n"
            f"- 门锁: front_door(前门), back_door(后门)\n\n"
            f"理解用户意图时请注意:\n"
            f'1. "太热了" → 调低温度或打开风扇\n'
            f'2. "太冷了" → 调高温度\n'
            f'3. "睡觉了"/"睡觉"/"晚安" → 关闭所有灯光\n'
            f'4. "出门"/"离开" → 关闭所有灯光,锁定所有门\n'
            f'5. "回家" → 打开客厅灯,解锁门\n'
            f'6. "看电视" → 调暗客厅灯,关闭窗帘\n'
            f'7. "起床" → 打开窗帘,打开卧室灯\n'
            f'8. "太亮了" → 调暗灯光或关闭窗帘\n\n'
            f"只调用必要的工具,不要过度操作。如果用户询问状态,"
            f"使用 get_all_device_statuses。"
        )

    async def _call_llm(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """调用智谱AI API.

        Args:
            messages: 消息列表

        Returns:
            API 响应
        """
        api_key = self.API_KEY
        if not api_key:
            return {"error": "API Key 未设置,请在环境变量中设置 ZHIPU_API_KEY"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "glm-4-flash",
            "messages": messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.API_URL, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "No response"
            return {"error": f"API 请求失败: {e} - {error_detail}"}
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            return {"error": f"请求异常: {e}\n{error_trace}"}

    def _execute_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """执行工具调用.

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            执行结果
        """
        try:
            if tool_name == "turn_on_light":
                return self.simulator.turn_on_light(**arguments)
            if tool_name == "turn_off_light":
                return self.simulator.turn_off_light(**arguments)
            if tool_name == "set_light_brightness":
                return self.simulator.set_light_brightness(**arguments)
            if tool_name == "set_light_color":
                return self.simulator.set_light_color(**arguments)
            if tool_name == "set_temperature":
                return self.simulator.set_temperature(**arguments)
            if tool_name == "turn_on_fan":
                return self.simulator.turn_on_fan(**arguments)
            if tool_name == "turn_off_fan":
                return self.simulator.turn_off_fan(**arguments)
            if tool_name == "set_fan_speed":
                return self.simulator.set_fan_speed(**arguments)
            if tool_name == "open_curtain":
                return self.simulator.open_curtain(**arguments)
            if tool_name == "close_curtain":
                return self.simulator.close_curtain(**arguments)
            if tool_name == "lock_door":
                return self.simulator.lock_door(**arguments)
            if tool_name == "unlock_door":
                return self.simulator.unlock_door(**arguments)
            if tool_name == "turn_off_all_lights":
                results = self.simulator.turn_off_all_lights()
                return "\n".join(results)
            if tool_name == "get_all_device_statuses":
                statuses = self.simulator.get_all_statuses()
                return json.dumps(statuses, ensure_ascii=False, indent=2)
            return f"错误: 未知的工具 '{tool_name}'"
        except Exception as e:
            return f"执行失败: {e}"

    async def process(self, user_input: str) -> str:
        """处理用户输入.

        Args:
            user_input: 用户自然语言输入

        Returns:
            处理结果
        """
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input},
        ]

        response = await self._call_llm(messages)

        if "error" in response:
            return f"❌ {response['error']}"

        try:
            assistant_message = response["choices"][0]["message"]

            # 检查是否有工具调用
            if "tool_calls" not in assistant_message or not assistant_message["tool_calls"]:
                # 没有工具调用,返回文本响应
                return assistant_message.get("content", "我理解了,但没有执行任何操作。")

            # 执行所有工具调用
            results = []
            for tool_call in assistant_message["tool_calls"]:
                function = tool_call["function"]
                tool_name = function["name"]
                arguments = json.loads(function["arguments"])

                result = self._execute_tool_call(tool_name, arguments)
                results.append(result)

            return "\n".join(results)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"❌ 解析响应失败: {e}"

    def process_sync(self, user_input: str) -> str:
        """同步版本的处理方法.

        Args:
            user_input: 用户自然语言输入

        Returns:
            处理结果
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.process(user_input))
