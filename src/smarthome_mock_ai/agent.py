"""AI Agent - 使用 LLM 和 Function Calling 控制智能家居."""

import json
import os
from datetime import datetime
from typing import Any

import httpx

from smarthome_mock_ai.interaction_logger import InteractionLogger, get_interaction_logger
from smarthome_mock_ai.learning import PreferenceModel, get_preference_model


class SmartHomeAgent:
    """智能家居 AI Agent."""

    # API 配置
    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    @property
    def API_KEY(self) -> str:
        """获取 API Key."""
        return os.getenv("ZHIPU_API_KEY", "")

    def __init__(self, simulator: Any, enable_logging: bool = True, enable_learning: bool = True) -> None:
        """初始化 Agent.

        Args:
            simulator: HomeSimulator 实例
            enable_logging: 是否启用交互日志记录
            enable_learning: 是否启用习惯学习功能
        """
        self.simulator = simulator
        self.tools = self._define_tools()
        self.enable_logging = enable_logging
        self.enable_learning = enable_learning
        self.logger: InteractionLogger | None = get_interaction_logger() if enable_logging else None
        self.preference_model: PreferenceModel | None = get_preference_model() if enable_learning else None

        # Load existing preferences if available
        if self.preference_model:
            self.preference_model.load_preferences()

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
                    "name": "turn_on_all_lights",
                    "description": "打开所有的灯光设备",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_all_doors",
                    "description": "锁定所有的门 (通常用于离家、睡觉等场景)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "unlock_all_doors",
                    "description": "解锁所有的门 (通常用于回家场景)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "close_all_curtains",
                    "description": "关闭所有的窗帘 (通常用于看电视、睡觉等场景)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_all_curtains",
                    "description": "打开所有的窗帘 (通常用于起床、早上等场景)",
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
            f"重要规则:\n"
            f"1. 必须始终使用可用的工具/函数来执行操作,不要只回复文本\n"
            f"2. 理解用户意图时,立即调用相应的工具:\n"
            f'   - "太热了" → 调低温度(set_temperature到20-22度)或打开风扇\n'
            f'   - "太冷了" → 调高温度(set_temperature到25-26度)\n'
            f'   - "睡觉了"/"睡觉"/"晚安" → 关闭所有灯光(turn_off_all_lights)\n'
            f'   - "出门"/"离开" → 关闭所有灯光(turn_off_all_lights),锁定所有门(lock_all_doors)\n'
            f'   - "回家"/"回家啦" → 打开客厅灯(turn_on_light living_room_light),解锁所有门(unlock_all_doors)\n'
            f'   - "看电视" → 调暗客厅灯(set_light_brightness到30%),关闭所有窗帘(close_all_curtains)\n'
            f'   - "起床"/"早上好" → 打开所有窗帘(open_all_curtains),打开卧室灯\n'
            f'   - "太亮了" → 调暗灯光或关闭窗帘\n\n'
            f"3. 不要过度解释,直接执行工具调用\n"
            f"4. 如果用户询问状态,使用 get_all_device_statuses\n"
            f"5. 批量操作时优先使用批量工具(如turn_off_all_lights而非单独关闭每个灯)"
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
            # 配置 HTTP 客户端,禁用代理以避免连接问题
            async with httpx.AsyncClient(
                timeout=30.0,
                proxy=None,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            ) as client:
                response = await client.post(self.API_URL, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "No response"
            return {"error": f"API 请求失败: {e} - {error_detail}"}
        except httpx.ConnectError as e:
            return {"error": f"网络连接失败: {e}. 请检查网络连接或代理设置"}
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
        # Apply learned preferences before executing
        context = self._capture_context()
        adjusted_args, preference_message = self._apply_preferences(tool_name, arguments, context)

        if preference_message:
            # Log the preference adjustment
            result_messages = [preference_message]
        else:
            result_messages = []

        try:
            result = None
            if tool_name == "turn_on_light":
                result = self.simulator.turn_on_light(**adjusted_args)
            elif tool_name == "turn_off_light":
                result = self.simulator.turn_off_light(**adjusted_args)
            elif tool_name == "set_light_brightness":
                result = self.simulator.set_light_brightness(**adjusted_args)
            elif tool_name == "set_light_color":
                result = self.simulator.set_light_color(**adjusted_args)
            elif tool_name == "set_temperature":
                result = self.simulator.set_temperature(**adjusted_args)
            elif tool_name == "turn_on_fan":
                result = self.simulator.turn_on_fan(**adjusted_args)
            elif tool_name == "turn_off_fan":
                result = self.simulator.turn_off_fan(**adjusted_args)
            elif tool_name == "set_fan_speed":
                result = self.simulator.set_fan_speed(**adjusted_args)
            elif tool_name == "open_curtain":
                result = self.simulator.open_curtain(**adjusted_args)
            elif tool_name == "close_curtain":
                result = self.simulator.close_curtain(**adjusted_args)
            elif tool_name == "lock_door":
                result = self.simulator.lock_door(**adjusted_args)
            elif tool_name == "unlock_door":
                result = self.simulator.unlock_door(**adjusted_args)
            elif tool_name == "turn_off_all_lights":
                results = self.simulator.turn_off_all_lights()
                result = "\n".join(results)
            elif tool_name == "turn_on_all_lights":
                results = self.simulator.turn_on_all_lights()
                result = "\n".join(results)
            elif tool_name == "lock_all_doors":
                results = self.simulator.lock_all_doors()
                result = "\n".join(results)
            elif tool_name == "unlock_all_doors":
                results = self.simulator.unlock_all_doors()
                result = "\n".join(results)
            elif tool_name == "close_all_curtains":
                results = self.simulator.close_all_curtains()
                result = "\n".join(results)
            elif tool_name == "open_all_curtains":
                results = self.simulator.open_all_curtains()
                result = "\n".join(results)
            elif tool_name == "get_all_device_statuses":
                statuses = self.simulator.get_all_statuses()
                result = json.dumps(statuses, ensure_ascii=False, indent=2)
            else:
                return f"错误: 未知的工具 '{tool_name}'"

            # Combine preference message with result
            if result_messages:
                result_messages.append(result)
                return "\n".join(result_messages)
            return result

        except Exception as e:
            return f"执行失败: {e}"

    async def process(self, user_input: str) -> dict[str, Any]:
        """处理用户输入.

        Args:
            user_input: 用户自然语言输入

        Returns:
            处理结果字典,包含:
                - success: 是否成功
                - message: 结果消息
                - action_id: 动作ID (用于反馈)
                - actions_taken: 执行的动作列表
        """
        # Generate action ID
        action_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(user_input) % 10000:04d}"

        # Capture context before processing
        context = self._capture_context()

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input},
        ]

        response = await self._call_llm(messages)

        if "error" in response:
            error_result = {
                "success": False,
                "message": f"❌ {response['error']}",
                "action_id": action_id,
                "actions_taken": [],
            }
            # Log failed interaction
            if self.enable_logging and self.logger:
                self.logger.log_interaction(
                    user_command=user_input,
                    agent_action={"error": response["error"]},
                    context=context,
                    action_id=action_id,
                )
            return error_result

        try:
            assistant_message = response["choices"][0]["message"]

            # 检查是否有工具调用
            if "tool_calls" not in assistant_message or not assistant_message["tool_calls"]:
                # 没有工具调用,返回文本响应
                text_response = assistant_message.get("content", "我理解了,但没有执行任何操作。")
                result = {
                    "success": True,
                    "message": text_response,
                    "action_id": action_id,
                    "actions_taken": [],
                }
                # Log interaction with no tool calls
                if self.enable_logging and self.logger:
                    self.logger.log_interaction(
                        user_command=user_input,
                        agent_action={"response": text_response},
                        context=context,
                        action_id=action_id,
                    )
                return result

            # 执行所有工具调用
            actions_taken = []
            results = []
            for tool_call in assistant_message["tool_calls"]:
                function = tool_call["function"]
                tool_name = function["name"]
                arguments = json.loads(function["arguments"])

                action_record = {"tool": tool_name, "arguments": arguments}
                actions_taken.append(action_record)

                result = self._execute_tool_call(tool_name, arguments)
                results.append(result)

            result_message = "\n".join(results)
            result = {
                "success": True,
                "message": result_message,
                "action_id": action_id,
                "actions_taken": actions_taken,
            }

            # Log interaction with tool calls
            if self.enable_logging and self.logger:
                self.logger.log_interaction(
                    user_command=user_input,
                    agent_action={"actions": actions_taken, "result": result_message},
                    context=context,
                    action_id=action_id,
                )

            return result
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            error_result = {
                "success": False,
                "message": f"❌ 解析响应失败: {e}",
                "action_id": action_id,
                "actions_taken": [],
            }
            # Log failed interaction
            if self.enable_logging and self.logger:
                self.logger.log_interaction(
                    user_command=user_input,
                    agent_action={"error": str(e)},
                    context=context,
                    action_id=action_id,
                )
            return error_result

    def _capture_context(self) -> dict[str, Any]:
        """Capture the current context for logging.

        Returns:
            Context dictionary with time and device states
        """
        now = datetime.now()
        return {
            "timestamp": now.isoformat(),
            "time_of_day": now.hour,
            "day_of_week": now.weekday(),
            "device_states": self.simulator.get_all_statuses(),
        }

    def process_sync(self, user_input: str) -> dict[str, Any]:
        """同步版本的处理方法.

        Args:
            user_input: 用户自然语言输入

        Returns:
            处理结果字典
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.process(user_input))

    # ========== 偏好学习相关方法 ==========

    def _apply_preferences(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> tuple[dict[str, Any], str | None]:
        """Apply learned preferences to tool arguments.

        Args:
            tool_name: The tool being called
            arguments: Original arguments from LLM
            context: Current context

        Returns:
            Tuple of (adjusted_arguments, preference_message)
        """
        if self.preference_model is None:
            return arguments, None

        return self.preference_model.adjust_arguments(tool_name, arguments, context)

    def train_preferences(self) -> dict[str, Any]:
        """Train the preference model from interaction history.

        Returns:
            Training statistics dictionary
        """
        if self.preference_model is None:
            return {"error": "Learning is disabled"}

        stats = self.preference_model.train()

        # Save preferences after training
        if "error" not in stats:
            self.preference_model.save_preferences()

        return stats

    def get_preference_summary(self) -> dict[str, Any]:
        """Get a summary of learned preferences.

        Returns:
            Dictionary with preference statistics
        """
        if self.preference_model is None:
            return {"error": "Learning is disabled"}

        return self.preference_model.get_preference_summary()

    def should_retrain(self) -> bool:
        """Check if the model should be retrained based on recent feedback.

        Returns:
            True if there are enough new interactions to warrant retraining
        """
        if self.preference_model is None or self.logger is None:
            return False

        try:
            import sqlite3

            with sqlite3.connect(self.preference_model.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM interaction_logs
                    WHERE user_feedback IS NOT NULL
                    """
                )
                count = cursor.fetchone()[0]

                # Retrain after every 10 feedback entries
                return count >= 10 and count % 10 == 0

        except sqlite3.Error:
            return False
