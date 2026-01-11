"""Integration test for the AI Agent."""

import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, "src")
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


async def test_basic_operations():
    """Test basic device operations."""
    print("=== Testing SmartHome AI Agent ===\n")

    # Initialize
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    # Test 1: Direct simulator operations
    print("1. Testing direct simulator operations:")
    result = simulator.turn_on_light("living_room_light")
    print(f"   {result}")

    result = simulator.set_temperature("thermostat", 24.0)
    print(f"   {result}")

    # Test 2: Check device statuses
    print("\n2. Device statuses after manual operations:")
    statuses = simulator.get_all_statuses()
    living_room_light = statuses["living_room_light"]
    thermostat = statuses["thermostat"]
    print(f"   Living room light: is_on={living_room_light['is_on']}")
    print(f"   Thermostat: target_temp={thermostat['target_temp']}°C")

    # Test 3: AI Agent processing (if API key available)
    api_key = os.getenv("ZHIPU_API_KEY")
    if api_key and api_key != "your_api_key_here":
        print("\n3. Testing AI Agent with LLM:")

        test_commands = [
            "关闭所有灯",
            "把温度调到25度",
        ]

        for cmd in test_commands:
            print(f"\n   Command: '{cmd}'")
            try:
                result = await agent.process(cmd)
                print(f"   Result: {result}")
            except Exception as e:
                print(f"   Error: {e}")
    else:
        print("\n3. Skipping AI Agent tests (API key not configured)")

    print("\n=== All tests completed ===")


def main():
    """Main entry point."""
    load_dotenv()

    try:
        asyncio.run(test_basic_operations())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
