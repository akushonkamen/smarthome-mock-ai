"""测试 Agent 功能."""

import asyncio
import os

from dotenv import load_dotenv
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


async def test_agent():
    """测试 Agent 基本功能."""
    load_dotenv()

    print("=== SmartHome Agent 测试 ===\n")

    # 检查 API Key
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 未设置 ZHIPU_API_KEY,跳过 LLM 测试")
        print("   提示: 在 .env 文件中设置您的 API Key\n")
        return

    # 初始化
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    print(f"✓ 已初始化 {len(simulator.list_all_devices())} 个设备\n")

    # 测试用例
    test_cases = [
        "打开客厅灯",
        "把温度调到25度",
        "关闭所有灯",
    ]

    for i, user_input in enumerate(test_cases, 1):
        print(f"测试 {i}: {user_input}")
        print("-" * 50)
        result = await agent.process(user_input)
        print(f"结果: {result}\n")

    # 显示最终状态
    print("\n最终设备状态:")
    print("-" * 50)
    statuses = simulator.get_all_statuses()
    for device_id, status in statuses.items():
        device_name = status.get("name", device_id)
        print(f"{device_name}: {status}")

    print("\n✓ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_agent())
