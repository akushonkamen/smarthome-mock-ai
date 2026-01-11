"""Tests for intent recognition and query vs command classification."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.devices import Light, Thermostat
from smarthome_mock_ai.simulator import HomeSimulator


class TestIntentRecognition:
    """Test intent recognition for QUERY vs COMMAND classification."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator with default devices."""
        sim = HomeSimulator(persist_state=False)
        # Register test devices
        sim.register_device(Thermostat(device_id="thermostat", name="Thermostat", room="living_room"))
        sim.register_device(Light(device_id="living_room_light", name="Living Room Light", room="living_room"))
        return sim

    @pytest.fixture
    def agent(self, simulator):
        """Create an agent with the simulator."""
        # Disable logging for tests
        return SmartHomeAgent(simulator, enable_logging=False, enable_learning=False)

    @pytest.mark.asyncio
    async def test_query_temperature_no_state_change(self, agent, simulator):
        """Test that asking about temperature does NOT change the temperature.

        User: "现在温度多少?" (What's the temperature now?)
        Expected: QUERY intent → use get_device_state → NO temperature change
        """
        # Get initial temperature
        initial_status = simulator.get_device_details("thermostat")
        initial_temp = initial_status["current_state"]["target_temp"]

        # Mock the LLM response to return a get_device_state tool call
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_device_state",
                                    "arguments": '{"device_id": "thermostat"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
            result = await agent.process("现在温度多少?")

        # Verify temperature did NOT change
        final_status = simulator.get_device_details("thermostat")
        final_temp = final_status["current_state"]["target_temp"]

        assert initial_temp == final_temp, f"Temperature changed from {initial_temp} to {final_temp}!"
        assert result["success"] is True
        assert len(result["actions_taken"]) == 1
        assert result["actions_taken"][0]["tool"] == "get_device_state"

    @pytest.mark.asyncio
    async def test_command_cold_changes_temperature(self, agent, simulator):
        """Test that saying "it's cold" DOES change the temperature.

        User: "太冷了" (It's too cold)
        Expected: COMMAND intent → use set_temperature → temperature changes
        """
        # Get initial temperature
        initial_status = simulator.get_device_details("thermostat")
        initial_temp = initial_status["current_state"]["target_temp"]

        # Mock the LLM response to return a set_temperature tool call
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "set_temperature",
                                    "arguments": '{"device_id": "thermostat", "temp": 25}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
            result = await agent.process("太冷了")

        # Verify temperature DID change
        final_status = simulator.get_device_details("thermostat")
        final_temp = final_status["current_state"]["target_temp"]

        assert final_temp == 25, f"Temperature not set correctly: {final_temp}"
        assert final_temp != initial_temp, "Temperature should have changed!"
        assert result["success"] is True
        assert len(result["actions_taken"]) == 1
        assert result["actions_taken"][0]["tool"] == "set_temperature"

    @pytest.mark.asyncio
    async def test_query_light_status_no_change(self, agent, simulator):
        """Test that asking if light is on does NOT change the light.

        User: "客厅灯开着吗?" (Is the living room light on?)
        Expected: QUERY intent → use get_device_state → NO state change
        """
        # Get initial light state
        initial_status = simulator.get_device_details("living_room_light")
        initial_is_on = initial_status["current_state"]["is_on"]

        # Mock the LLM response to return a get_device_state tool call
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_device_state",
                                    "arguments": '{"device_id": "living_room_light"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
            result = await agent.process("客厅灯开着吗?")

        # Verify light state did NOT change
        final_status = simulator.get_device_details("living_room_light")
        final_is_on = final_status["current_state"]["is_on"]

        assert initial_is_on == final_is_on, "Light state changed!"
        assert result["actions_taken"][0]["tool"] == "get_device_state"

    @pytest.mark.asyncio
    async def test_command_turn_on_light_changes_state(self, agent, simulator):
        """Test that asking to turn on light DOES change the light.

        User: "打开客厅灯" (Turn on living room light)
        Expected: COMMAND intent → use turn_on_light → light turns on
        """
        # Make sure light is off initially
        simulator.turn_off_light("living_room_light")
        initial_status = simulator.get_device_details("living_room_light")
        assert initial_status["current_state"]["is_on"] is False

        # Mock the LLM response to return a turn_on_light tool call
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "turn_on_light",
                                    "arguments": '{"device_id": "living_room_light"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
            result = await agent.process("打开客厅灯")

        # Verify light DID turn on
        final_status = simulator.get_device_details("living_room_light")
        assert final_status["current_state"]["is_on"] is True
        assert result["actions_taken"][0]["tool"] == "turn_on_light"

    @pytest.mark.asyncio
    async def test_query_all_devices_no_changes(self, agent, simulator):
        """Test that asking for all device statuses does NOT change anything.

        User: "所有设备状态怎么样?" (How are all devices?)
        Expected: QUERY intent → use get_all_device_statuses → NO state changes
        """
        # Get initial state snapshot
        initial_state = simulator.get_all_statuses()

        # Mock the LLM response to return get_all_device_statuses
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_all_device_statuses",
                                    "arguments": "{}",
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
            result = await agent.process("所有设备状态怎么样?")

        # Verify NO state changes
        final_state = simulator.get_all_statuses()
        assert initial_state == final_state, "Device states changed during query!"
        assert result["actions_taken"][0]["tool"] == "get_all_device_statuses"

    def test_system_prompt_has_thought_protocol(self, agent):
        """Test that the system prompt includes the Thought Protocol."""
        prompt = agent._build_system_prompt()

        # Check for Thought Protocol
        assert "思维协议" in prompt or "Thought Protocol" in prompt
        assert "QUERY" in prompt
        assert "COMMAND" in prompt
        assert "CHIT-CHAT" in prompt

        # Check for Golden Rule
        assert "黄金法则" in prompt or "Golden Rule" in prompt
        assert "禁止" in prompt or "FORBID" in prompt

        # Check for few-shot examples
        assert "现在温度多少" in prompt
        assert "太冷了" in prompt
        assert "客厅灯开着吗" in prompt

    def test_tools_separated_by_intent(self, agent):
        """Test that tools are properly categorized into QUERY and COMMAND."""
        tools = agent.tools
        tool_names = [t["function"]["name"] for t in tools]

        # QUERY tools (should not change state)
        query_tools = {"get_device_state", "get_all_device_statuses"}

        # COMMAND tools (should change state)
        command_tools = {
            "turn_on_light",
            "turn_off_light",
            "set_light_brightness",
            "set_light_color",
            "set_temperature",
            "turn_on_fan",
            "turn_off_fan",
            "set_fan_speed",
            "open_curtain",
            "close_curtain",
            "lock_door",
            "unlock_door",
            "turn_off_all_lights",
            "turn_on_all_lights",
            "lock_all_doors",
            "unlock_all_doors",
            "close_all_curtains",
            "open_all_curtains",
        }

        # Verify all tools exist
        assert "get_device_state" in tool_names
        assert "get_all_device_statuses" in tool_names

        for query_tool in query_tools:
            assert query_tool in tool_names

        for command_tool in command_tools:
            assert command_tool in tool_names

        # Verify tool descriptions indicate intent
        for tool in tools:
            name = tool["function"]["name"]
            desc = tool["function"]["description"]

            if name in query_tools:
                # Query tools should mention not changing state
                assert "不改变" in desc or "查询" in desc or "获取" in desc

            if name in command_tools:
                # Command tools should mention changing state
                assert "改变" in desc or "设置" in desc or "打开" in desc or "关闭" in desc

    def test_get_device_state_tool_exists(self, agent):
        """Test that get_device_state tool is properly defined."""
        tools = agent.tools
        tool_names = [t["function"]["name"] for t in tools]

        assert "get_device_state" in tool_names

        # Find the get_device_state tool
        get_state_tool = None
        for tool in tools:
            if tool["function"]["name"] == "get_device_state":
                get_state_tool = tool
                break

        assert get_state_tool is not None

        # Verify it has the right structure
        func_def = get_state_tool["function"]
        assert "device_id" in func_def["parameters"]["properties"]
        assert func_def["parameters"]["properties"]["device_id"]["type"] == "string"
        assert "device_id" in func_def["parameters"]["required"]

    def test_tools_use_dynamic_device_list(self, agent, simulator):
        """Test that tools use the dynamic device list from simulator."""
        tools = agent.tools
        all_device_ids = simulator.list_all_devices()

        # Find get_device_state tool and check its enum
        for tool in tools:
            if tool["function"]["name"] == "get_device_state":
                device_id_param = tool["function"]["parameters"]["properties"]["device_id"]
                assert "enum" in device_id_param
                # All simulator devices should be in the enum
                tool_devices = set(device_id_param["enum"])
                sim_devices = set(all_device_ids)
                assert tool_devices == sim_devices
                break


class TestIntentRecognitionIntegration:
    """Integration tests for intent recognition with real scenarios."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator with multiple devices."""
        sim = HomeSimulator(persist_state=False)
        sim.register_device(Thermostat(device_id="thermostat", name="Main Thermostat", room="living_room"))
        sim.register_device(Light(device_id="living_room_light", name="Living Room Light", room="living_room"))
        sim.register_device(Light(device_id="bedroom_light", name="Bedroom Light", room="bedroom"))
        return sim

    @pytest.fixture
    def agent(self, simulator):
        """Create an agent."""
        return SmartHomeAgent(simulator, enable_logging=False, enable_learning=False)

    @pytest.mark.asyncio
    async def test_multiple_query_requests_no_state_changes(self, agent, simulator):
        """Test multiple consecutive QUERY requests don't change state."""
        initial_state = simulator.get_all_statuses()

        # Test 1: Query temperature
        mock_response_1 = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_device_state",
                                    "arguments": '{"device_id": "thermostat"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response_1)):
            await agent.process("温度多少?")

        # Test 2: Query light status
        mock_response_2 = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_device_state",
                                    "arguments": '{"device_id": "living_room_light"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response_2)):
            await agent.process("客厅灯亮不亮?")

        # Test 3: Query all devices
        mock_response_3 = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_all_device_statuses",
                                    "arguments": "{}",
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response_3)):
            await agent.process("所有设备状态")

        # Verify NO state changes after all queries
        final_state = simulator.get_all_statuses()
        assert initial_state == final_state, "State changed after QUERY operations!"

    @pytest.mark.asyncio
    async def test_command_then_query_sequence(self, agent, simulator):
        """Test a COMMAND followed by QUERY works correctly."""
        # COMMAND: Set temperature (should change)
        mock_command_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "set_temperature",
                                    "arguments": '{"device_id": "thermostat", "temp": 26}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_command_response)):
            await agent.process("太热了")

        # Verify temperature changed
        temp_after_command = simulator.get_device_details("thermostat")["current_state"]["target_temp"]
        assert temp_after_command == 26

        # QUERY: Ask temperature (should NOT change)
        mock_query_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_device_state",
                                    "arguments": '{"device_id": "thermostat"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_query_response)):
            await agent.process("现在温度多少?")

        # Verify temperature stayed the same (not changed by query)
        temp_after_query = simulator.get_device_details("thermostat")["current_state"]["target_temp"]
        assert temp_after_query == 26, "Query changed the temperature!"
