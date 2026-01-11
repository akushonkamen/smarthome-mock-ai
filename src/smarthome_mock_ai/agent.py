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
        # Get dynamic device list for enum values
        all_devices = self.simulator.list_all_devices()
        all_metadata = self.simulator.get_all_metadata()

        # Group devices by type
        devices_by_type: dict[str, list[str]] = {}
        for device_id, metadata in all_metadata.items():
            device_type = metadata["device_type"]
            if device_type not in devices_by_type:
                devices_by_type[device_type] = []
            devices_by_type[device_type].append(device_id)

        tools = [
            # ========== 查询工具 (QUERY - 不改变状态) ==========
            {
                "type": "function",
                "function": {
                    "name": "get_device_state",
                    "description": "查询单个设备的当前状态(不改变设备状态)。当用户询问某个设备的状态时使用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "设备ID",
                                "enum": all_devices,
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_device_statuses",
                    "description": "获取所有设备的当前状态(不改变任何设备状态)。当用户询问整体状态或需要查看所有设备时使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            # ========== 控制工具 (COMMAND - 会改变状态) ==========
            {
                "type": "function",
                "function": {
                    "name": "turn_on_light",
                    "description": "打开指定的灯光设备 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": devices_by_type.get("light", []),
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
                    "description": "关闭指定的灯光设备 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": devices_by_type.get("light", []),
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
                    "description": "设置灯光的亮度级别 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": devices_by_type.get("light", []),
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
                    "description": "设置灯光的颜色 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "灯光设备ID",
                                "enum": devices_by_type.get("light", []),
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
                    "description": "设置温控器的目标温度 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "温控器设备ID",
                                "enum": devices_by_type.get("thermostat", []),
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
                    "description": "打开指定的风扇设备 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": devices_by_type.get("fan", []),
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
                    "description": "关闭指定的风扇设备 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": devices_by_type.get("fan", []),
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
                    "description": "设置风扇的速度等级 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "风扇设备ID",
                                "enum": devices_by_type.get("fan", []),
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
                    "description": "打开指定的窗帘 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "窗帘设备ID",
                                "enum": devices_by_type.get("curtain", []),
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
                    "description": "关闭指定的窗帘 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "窗帘设备ID",
                                "enum": devices_by_type.get("curtain", []),
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
                    "description": "锁定指定的门 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "门锁设备ID",
                                "enum": devices_by_type.get("door", []),
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
                    "description": "解锁指定的门 (改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "门锁设备ID",
                                "enum": devices_by_type.get("door", []),
                            }
                        },
                        "required": ["device_id"],
                    },
                },
            },
            # ========== 批量控制工具 (COMMAND - 会改变多个设备状态) ==========
            {
                "type": "function",
                "function": {
                    "name": "turn_off_all_lights",
                    "description": "关闭所有的灯光设备 (通常用于睡觉、离家等场景 - 改变状态)",
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
                    "description": "打开所有的灯光设备 (改变状态)",
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
                    "description": "锁定所有的门 (通常用于离家、睡觉等场景 - 改变状态)",
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
                    "description": "解锁所有的门 (通常用于回家场景 - 改变状态)",
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
                    "description": "关闭所有的窗帘 (通常用于看电视、睡觉等场景 - 改变状态)",
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
                    "description": "打开所有的窗帘 (通常用于起床、早上等场景 - 改变状态)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]
        return tools

    def _build_system_prompt(self) -> str:
        """构建系统提示词 with Thought Protocol.

        Returns:
            系统提示词字符串
        """
        all_metadata = self.simulator.get_all_metadata()

        # Build device list string
        device_list_str = ""
        for device_id, metadata in all_metadata.items():
            device_list_str += f"  - {device_id}: {metadata['name']} ({metadata['device_type']})\n"

        return (
            "# 智能家居控制助手\n\n"
            "你是一个专业的智能家居控制助手。用户会用自然语言描述他们的需求，你需要理解并控制相应的设备。\n\n"
            "## 可用设备列表\n"
            f"{device_list_str}\n"
            "## 思维协议 (Thought Protocol) - 必须严格遵循\n\n"
            "在处理用户请求之前，你必须先进行意图分类。按以下步骤思考：\n\n"
            "### 步骤 1: 意图分类\n"
            "判断用户输入属于以下哪一类：\n\n"
            "**CATEGORY: QUERY (查询)**\n"
            "- 用户询问信息、状态、当前值\n"
            "- 关键词: \"多少\"、\"是什么\"、\"怎么样\"、\"温度\"、\"状态\"、\"亮度\"、\"开了吗\"\n"
            "- 规则: **仅使用 get_device_state 或 get_all_device_statuses**\n"
            "- **禁止**: 任何会改变状态的工具 (set_*, turn_*, open_*, close_*, lock_*, unlock_*)\n\n"
            "**CATEGORY: COMMAND (命令)**\n"
            "- 用户要求改变、调整、操作设备\n"
            "- 关键词: \"打开\"、\"关闭\"、\"设置\"、\"太热\"、\"太冷\"、\"我要\"、场景描述\n"
            "- 规则: **使用控制工具** (set_*, turn_*, open_*, close_*, lock_*, unlock_*)\n\n"
            "**CATEGORY: CHIT-CHAT (闲聊)**\n"
            "- 一般性对话、问候、感谢\n"
            "- 规则: **不使用任何工具**，直接回复文本\n\n"
            "### 步骤 2: 执行验证\n"
            "- 如果是 QUERY：只能使用查询工具，绝对不能调用任何会改变状态的工具\n"
            "- 如果是 COMMAND：使用相应的控制工具\n"
            "- 如果用户问\"X是什么\"，绝不能改变 X，只能报告 X 的状态\n\n"
            "## 示例 (Few-Shot Examples)\n\n"
            "### QUERY 示例 (只查询，不改变状态):\n\n"
            "用户: \"现在温度多少?\"\n"
            "思考: 用户询问当前温度 → QUERY 类别 → 使用 get_device_state 查询 thermostat\n"
            "工具: get_device_state(device_id=\"thermostat\")\n\n"
            "用户: \"客厅灯开着吗?\"\n"
            "思考: 用户询问灯的状态 → QUERY 类别 → 使用 get_device_state 查询\n"
            "工具: get_device_state(device_id=\"living_room_light\")\n\n"
            "用户: \"所有设备状态怎么样?\"\n"
            "思考: 用户询问整体状态 → QUERY 类别 → 使用 get_all_device_statuses\n"
            "工具: get_all_device_statuses()\n\n"
            "### COMMAND 示例 (执行操作):\n\n"
            "用户: \"太冷了\"\n"
            "思考: 用户表示冷，暗示需要升温 → COMMAND 类别 → 设置温度\n"
            "工具: set_temperature(device_id=\"thermostat\", temp=25)\n\n"
            "用户: \"打开客厅灯\"\n"
            "思考: 用户明确要求开灯 → COMMAND 类别 → 打开灯光\n"
            "工具: turn_on_light(device_id=\"living_room_light\")\n\n"
            "用户: \"我要睡觉了\"\n"
            "思考: 用户场景暗示需要关灯 → COMMAND 类别 → 关闭所有灯\n"
            "工具: turn_off_all_lights()\n\n"
            "### 关键规则:\n\n"
            "1. **黄金法则**: 如果用户问\"X是什么/多少/怎么样\"，绝不能改变 X，只能查询并报告\n"
            "2. QUERY 类别只能用: get_device_state, get_all_device_statuses\n"
            "3. COMMAND 类别才能用: set_*, turn_*, open_*, close_*, lock_*, unlock_*\n"
            "4. 优先使用批量操作工具 (如 turn_off_all_lights 而非单独关闭每个灯)\n\n"
            "## 常见场景处理:\n\n"
            "- \"太热了\" → COMMAND → set_temperature(20-22) 或 turn_on_fan\n"
            "- \"太冷了\" → COMMAND → set_temperature(25-26)\n"
            "- \"睡觉了\"/\"晚安\" → COMMAND → turn_off_all_lights, lock_all_doors\n"
            "- \"出门\"/\"离开\" → COMMAND → turn_off_all_lights, lock_all_doors\n"
            "- \"回家\"/\"回家啦\" → COMMAND → turn_on_light(living_room_light), unlock_all_doors\n"
            "- \"看电视\" → COMMAND → set_light_brightness(living_room_light, 30), close_all_curtains\n"
            "- \"起床\"/\"早上好\" → COMMAND → open_all_curtains\n"
            "- \"太亮了\" → COMMAND → set_light_brightness 或 close_curtain\n\n"
            "## 重要提醒:\n\n"
            "- 先思考意图类别，再选择工具\n"
            "- QUERY 请求只查询，不改变状态\n"
            "- COMMAND 请求才改变状态\n"
            "- 当用户询问\"现在温度多少\"、\"灯开着吗\"等问题时，**必须**使用 get_device_state，**禁止**使用 set_temperature\n"
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
            # ========== 查询工具 (QUERY) ==========
            if tool_name == "get_device_state":
                device_id = arguments.get("device_id")
                details = self.simulator.get_device_details(device_id)
                if details:
                    result = f"设备 {device_id} 状态:\n{json.dumps(details, ensure_ascii=False, indent=2)}"
                else:
                    result = f"设备 {device_id} 不存在"
            elif tool_name == "get_all_device_statuses":
                statuses = self.simulator.get_all_statuses()
                result = json.dumps(statuses, ensure_ascii=False, indent=2)

            # ========== 控制工具 (COMMAND) ==========
            elif tool_name == "turn_on_light":
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
