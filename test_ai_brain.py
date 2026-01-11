"""Test AI Brain functionality with LLM integration."""

import asyncio
import sys
from dotenv import load_dotenv

sys.path.insert(0, "src")
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


async def test_ai_brain():
    """Test the AI Brain with various natural language inputs."""
    load_dotenv()

    # Initialize
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    print("=" * 70)
    print("🧠 Testing AI Brain with LLM Integration")
    print("=" * 70)

    test_cases = [
        ("太热了", "User complaint about heat"),
        ("把温度调到25度", "Direct temperature command"),
        ("打开客厅灯", "Direct light control"),
        ("我要睡觉了", "Sleep scenario - should turn off all lights"),
        ("查看所有设备状态", "Status query"),
    ]

    for user_input, description in test_cases:
        print(f"\n{'─' * 70}")
        print(f"📝 Test: {description}")
        print(f"👤 User Input: \"{user_input}\"")
        print("🤖 AI Processing...")

        result = await agent.process(user_input)

        print(f"✅ Result:\n{result}")

    print("\n" + "=" * 70)
    print("✅ All AI Brain tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_ai_brain())
