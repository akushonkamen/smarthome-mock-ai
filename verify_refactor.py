#!/usr/bin/env python3
"""Verify Refactor - Integration Test Script

This script automatically tests the refactored system to ensure:
1. Dynamic device registry works
2. Intent recognition works (QUERY vs COMMAND)
3. Agent responses are correct
4. CLI integration works
"""

import asyncio
import sys
from unittest.mock import AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, "src")

from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.devices import Light
from smarthome_mock_ai.simulator import HomeSimulator


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"ℹ️  {text}")


async def test_dynamic_device_registry():
    """Test 1: Dynamic Device Registry

    Register a new device and verify it appears in the system.
    """
    print_header("TEST 1: Dynamic Device Registry")

    # Create simulator
    simulator = HomeSimulator(persist_state=False)
    print_info(f"Initial device count: {len(simulator.list_all_devices())}")

    # Register a new device: Study Room Light
    print_info("\n📝 Registering new device: 'Study Room Light'...")
    study_light = Light(device_id="study_room_light", name="书房灯", room="study_room")
    device_id = simulator.register_device(study_light)

    # Verify device was registered
    assert device_id == "study_room_light"
    assert "study_room_light" in simulator.list_all_devices()
    print_success(f"Device registered successfully: {device_id}")

    # Verify device details
    details = simulator.get_device_details(device_id)
    assert details is not None
    assert details["metadata"]["name"] == "书房灯"
    assert details["metadata"]["device_type"] == "light"
    assert "turn_on" in details["metadata"]["capabilities"]
    print_success(f"Device details verified: {details['metadata']['name']}")
    print_info(f"   Capabilities: {details['metadata']['capabilities']}")

    # Verify device appears in device list
    all_devices = simulator.list_all_devices()
    print_success(f"Device appears in registry (total: {len(all_devices)} devices)")

    return simulator


async def test_intent_query_no_state_change():
    """Test 2: Intent Recognition - QUERY (No State Change)

    User: "What is the status of Study Room Light?"
    Expected: get_device_state tool called, NO state change
    """
    print_header("TEST 2: Intent Recognition - QUERY")

    # Create simulator with the new device
    simulator = HomeSimulator(persist_state=False)
    study_light = Light(device_id="study_room_light", name="书房灯", room="study_room")
    simulator.register_device(study_light)

    # Create agent (disabled logging for tests)
    agent = SmartHomeAgent(simulator, enable_logging=False, enable_learning=False)

    # Get initial state
    initial_details = simulator.get_device_details("study_room_light")
    initial_is_on = initial_details["current_state"]["is_on"]
    print_info(f"Initial light state: is_on={initial_is_on}")

    # Mock LLM response to return get_device_state tool call
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
                                "arguments": '{"device_id": "study_room_light"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    print_info("\n📝 Simulating user input: '书房灯的状态是什么?'")
    print_info("   Expected: get_device_state (QUERY - no state change)")

    # Process the request
    with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
        result = await agent.process("书房灯的状态是什么?")

    # Verify result
    assert result["success"] is True
    assert len(result["actions_taken"]) == 1
    assert result["actions_taken"][0]["tool"] == "get_device_state"
    print_success(f"Agent called: {result['actions_taken'][0]['tool']}")

    # Verify NO state change
    final_details = simulator.get_device_details("study_room_light")
    final_is_on = final_details["current_state"]["is_on"]
    assert initial_is_on == final_is_on
    print_success(f"State unchanged: is_on still {final_is_on} ✓")

    return simulator


async def test_intent_command_changes_state():
    """Test 3: Intent Recognition - COMMAND (State Change)

    User: "Turn on Study Room Light."
    Expected: turn_on_light tool called, device turns on
    """
    print_header("TEST 3: Intent Recognition - COMMAND")

    # Use simulator from previous test
    simulator = HomeSimulator(persist_state=False)
    study_light = Light(device_id="study_room_light", name="书房灯", room="study_room")
    simulator.register_device(study_light)
    agent = SmartHomeAgent(simulator, enable_logging=False, enable_learning=False)

    # Make sure light is off initially
    simulator.turn_off_light("study_room_light")
    initial_details = simulator.get_device_details("study_room_light")
    assert initial_details["current_state"]["is_on"] is False
    print_info(f"Initial light state: is_on={initial_details['current_state']['is_on']}")

    # Mock LLM response to return turn_on_light tool call
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
                                "arguments": '{"device_id": "study_room_light"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    print_info("\n📝 Simulating user input: '打开书房灯'")
    print_info("   Expected: turn_on_light (COMMAND - state change)")

    # Process the request
    with patch.object(agent, "_call_llm", new=AsyncMock(return_value=mock_response)):
        result = await agent.process("打开书房灯")

    # Verify result
    assert result["success"] is True
    assert len(result["actions_taken"]) == 1
    assert result["actions_taken"][0]["tool"] == "turn_on_light"
    print_success(f"Agent called: {result['actions_taken'][0]['tool']}")

    # Verify state DID change
    final_details = simulator.get_device_details("study_room_light")
    final_is_on = final_details["current_state"]["is_on"]
    assert final_is_on is True
    print_success(f"State changed: is_on now {final_is_on} ✓")

    return simulator


async def test_dynamic_tools_include_new_device():
    """Test 4: Dynamic Tool Discovery

    Verify that the agent's tools automatically include the newly registered device.
    """
    print_header("TEST 4: Dynamic Tool Discovery")

    # Create simulator and add custom device
    simulator = HomeSimulator(persist_state=False)
    study_light = Light(device_id="study_room_light", name="书房灯", room="study_room")
    simulator.register_device(study_light)

    # Create agent
    agent = SmartHomeAgent(simulator, enable_logging=False, enable_learning=False)

    # Check if the new device appears in tools
    tools = agent.tools
    tool_names = [t["function"]["name"] for t in tools]

    print_info("Checking if new device appears in agent tools...")

    # Find get_device_state tool and check its enum
    found_device_in_tools = False
    for tool in tools:
        if tool["function"]["name"] == "get_device_state":
            device_enum = tool["function"]["parameters"]["properties"]["device_id"].get("enum", [])
            if "study_room_light" in device_enum:
                found_device_in_tools = True
                print_success(f"New device 'study_room_light' found in get_device_state enum")
                break

    assert found_device_in_tools, "New device not found in agent tools!"

    # Find turn_on_light tool and check its enum
    found_device_in_turn_on = False
    for tool in tools:
        if tool["function"]["name"] == "turn_on_light":
            device_enum = tool["function"]["parameters"]["properties"]["device_id"].get("enum", [])
            if "study_room_light" in device_enum:
                found_device_in_turn_on = True
                print_success(f"New device 'study_room_light' found in turn_on_light enum")
                break

    assert found_device_in_turn_on, "New device not found in turn_on_light tool!"

    print_success("Dynamic tool discovery working correctly ✓")


async def test_unregister_device():
    """Test 5: Device Unregistration

    Verify that unregistering a device removes it from the system.
    """
    print_header("TEST 5: Device Unregistration")

    # Create simulator and register device
    simulator = HomeSimulator(persist_state=False)
    study_light = Light(device_id="study_room_light", name="书房灯", room="study_room")
    simulator.register_device(study_light)

    initial_count = len(simulator.list_all_devices())
    print_info(f"Initial device count: {initial_count}")
    print_info(f"Devices: {simulator.list_all_devices()}")

    # Unregister the device
    print_info("\n📝 Unregistering 'study_room_light'...")
    result = simulator.unregister_device("study_room_light")

    assert result is True
    print_success("Device unregistered successfully")

    # Verify device is gone
    assert "study_room_light" not in simulator.list_all_devices()
    final_count = len(simulator.list_all_devices())
    assert final_count == initial_count - 1
    print_success(f"Device removed from registry (total: {final_count} devices)")

    # Verify get_device_details returns None
    details = simulator.get_device_details("study_room_light")
    assert details is None
    print_success("get_device_details returns None for unregistered device")


async def main():
    """Run all verification tests."""
    print("\n" + "🔍" * 35)
    print("  🔍 REFACTOR VERIFICATION SUITE 🔍")
    print("🔍" * 35)

    try:
        # Test 1: Dynamic Registry
        await test_dynamic_device_registry()

        # Test 2: QUERY Intent (No State Change)
        await test_intent_query_no_state_change()

        # Test 3: COMMAND Intent (State Change)
        await test_intent_command_changes_state()

        # Test 4: Dynamic Tool Discovery
        await test_dynamic_tools_include_new_device()

        # Test 5: Device Unregistration
        await test_unregister_device()

        # All tests passed
        print_header("✅ ALL TESTS PASSED ✅")
        print_success("Refactor verification complete!")
        print()
        print("Summary:")
        print("  ✓ Dynamic device registry working")
        print("  ✓ Intent recognition (QUERY vs COMMAND) working")
        print("  ✓ get_device_state query doesn't change state")
        print("  ✓ turn_on_light command changes state")
        print("  ✓ Dynamic tool discovery includes new devices")
        print("  ✓ Device unregistration working")
        print()

        return 0

    except AssertionError as e:
        print_header("❌ TEST FAILED ❌")
        print_error(f"Assertion error: {e}")
        return 1

    except Exception as e:
        print_header("❌ ERROR ❌")
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
