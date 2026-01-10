"""测试 Agent 高级场景."""

import asyncio
import os

from dotenv import load_dotenv
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


async def test_advanced_scenarios():
    """测试 Agent 高级场景."""
    load_dotenv()

    print("=== SmartHome Agent 高级场景测试 ===\n")

    # 检查 API Key
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 未设置 ZHIPU_API_KEY,跳过 LLM 测试")
        print("   提示: 在 .env 文件中设置您的 API Key\n")
        return

    # 初始化
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    # 先打开一些设备作为初始状态
    print("=== 设置初始状态 ===")
    simulator.turn_on_light("living_room_light")
    simulator.turn_on_light("bedroom_light")
    simulator.turn_on_light("kitchen_light")
    simulator.set_temperature("thermostat", 22)
    print("✓ 已打开客厅灯、卧室灯、厨房灯\n")

    # 显示初始状态
    print("=== 初始设备状态 ===")
    statuses = simulator.get_all_statuses()
    for device_id, status in statuses.items():
        if status.get("is_on"):
            device_name = status.get("name", device_id)
            print(f"  {device_name}: 开启")
    print()

    # 高级测试用例
    test_cases = [
        "我要睡觉了",
        "太热了",
        "我要看电视",
        "回家啦",
    ]

    for i, user_input in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}: {user_input}")
        print('=' * 60)
        result = await agent.process(user_input)
        print(f"\n执行结果:\n{result}\n")

        # 显示相关设备状态
        print("当前相关设备状态:")
        print("-" * 60)
        statuses = simulator.get_all_statuses()

        # 灯光状态
        lights_on = [
            f"{s['name']}({s.get('room', 'N/A')})"
            for s in statuses.values()
            if s.get("name") and "灯" in s["name"] and s.get("is_on")
        ]
        if lights_on:
            print(f"  开启的灯光: {', '.join(lights_on)}")
        else:
            print("  所有灯光已关闭")

        # 温控器状态
        thermostat = statuses.get("thermostat", {})
        if thermostat:
            print(f"  温度: {thermostat.get('target_temp', 'N/A')}°C (模式: {thermostat.get('mode', 'N/A')})")

        # 风扇状态
        fans_on = [
            f"{s['name']}({s.get('room', 'N/A')})"
            for s in statuses.values()
            if s.get("name") and "风扇" in s["name"] and s.get("is_on")
        ]
        if fans_on:
            print(f"  开启的风扇: {', '.join(fans_on)}")

        # 窗帘状态
        print("  窗帘:", end=" ")
        curtains = [
            f"{s['name']}({s.get('position', 0)}%)"
            for s in statuses.values()
            if s.get("name") and "窗帘" in s["name"]
        ]
        print(", ".join(curtains) if curtains else "无")

    print("\n" + "=" * 60)
    print("✓ 所有高级场景测试完成!")


if __name__ == "__main__":
    asyncio.run(test_advanced_scenarios())
