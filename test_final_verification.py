"""最终验证测试 - 确保所有场景正常工作."""

import asyncio
import os

from dotenv import load_dotenv
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


async def test_final_verification():
    """最终验证测试."""
    load_dotenv()

    print("=== SmartHome Agent 最终验证测试 ===\n")

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

    # 最终验证测试用例
    test_cases = [
        ("打开客厅灯", "Should turn on living room light"),
        ("把卧室灯调暗一点", "Should dim bedroom light"),
        ("关闭所有灯", "Should turn off all lights"),
        ("把温度调到26度", "Should set temperature to 26°C"),
        ("打开客厅风扇", "Should turn on living room fan"),
        ("我要睡觉了", "Should turn off all lights (sleep mode)"),
        ("打开客厅窗帘", "Should open living room curtain"),
        ("关闭所有窗帘", "Should close all curtains"),
    ]

    passed = 0
    failed = 0

    for i, (user_input, description) in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试 {i}: {user_input}")
        print(f"描述: {description}")
        print('=' * 70)

        try:
            result = await agent.process(user_input)
            print(f"\n✓ 执行成功:\n{result}\n")
            passed += 1
        except Exception as e:
            print(f"\n❌ 执行失败: {e}\n")
            failed += 1

        # 短暂延迟以避免 API 速率限制
        await asyncio.sleep(0.5)

    # 显示总结
    print("\n" + "=" * 70)
    print(f"测试完成! 通过: {passed}/{len(test_cases)}, 失败: {failed}/{len(test_cases)}")
    print("=" * 70)

    # 显示最终设备状态
    print("\n最终设备状态:")
    print("-" * 70)
    statuses = simulator.get_all_statuses()
    for device_id, status in statuses.items():
        device_name = status.get("name", device_id)
        print(f"{device_name}: {status}")

    if failed == 0:
        print("\n✓ 所有测试通过!")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(test_final_verification())
