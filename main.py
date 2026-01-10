"""SmartHome Mock AI - 主程序入口."""

import asyncio
import os
import sys
from typing import NoReturn

from dotenv import load_dotenv
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator


def print_banner() -> None:
    """打印欢迎横幅."""
    banner = r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🏠 SmartHome Mock AI - 智能家居控制系统                  ║
║                                                           ║
║   使用自然语言控制您的虚拟智能家居设备                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help() -> None:
    """打印帮助信息."""
    help_text = """
📖 可用命令:
  help          - 显示此帮助信息
  status        - 查看所有设备状态
  devices       - 列出所有可用设备
  reset         - 重置所有设备到初始状态
  clear         - 清空屏幕
  exit / quit   - 退出程序

💬 自然语言示例:
  "打开客厅灯"
  "太热了"
  "我要睡觉了"
  "把温度调到25度"
  "关闭所有灯"
  "打开客厅风扇并调到2档"
  "我要看电视"
  "回家啦"
"""
    print(help_text)


def print_device_list(simulator: HomeSimulator) -> None:
    """打印设备列表.

    Args:
        simulator: 模拟器实例
    """
    print("\n📱 可用设备列表:\n")
    categories = {
        "💡 灯光": ["living_room_light", "bedroom_light", "kitchen_light", "bathroom_light"],
        "🌡️  温控": ["thermostat"],
        "💨 风扇": ["living_room_fan", "bedroom_fan"],
        "🪟 窗帘": ["living_room_curtain", "bedroom_curtain"],
        "🚪 门锁": ["front_door", "back_door"],
    }

    for category, device_ids in categories.items():
        print(f"  {category}")
        for device_id in device_ids:
            device = simulator.get_device(device_id)
            print(f"    - {device_id}: {device.name}")
        print()


def print_device_statuses(simulator: HomeSimulator) -> None:
    """打印所有设备状态.

    Args:
        simulator: 模拟器实例
    """
    statuses = simulator.get_all_statuses()

    print("\n📊 设备状态:\n")

    for device_id, status in statuses.items():
        device_type = status.get("name", device_id)
        location = status.get("room", status.get("location", "未知"))

        print(f"  {device_type} ({location})")

        # 根据设备类型显示不同信息
        if "is_on" in status:  # 灯光或风扇
            state = "开启" if status["is_on"] else "关闭"
            print(f"    状态: {state}")
            if "brightness" in status:
                print(f"    亮度: {status['brightness']}%")
            if "color" in status:
                print(f"    颜色: {status['color']}")
            if "speed" in status:
                print(f"    速度: {status['speed']}档")
        elif "current_temp" in status:  # 温控器
            print(f"    当前温度: {status['current_temp']}°C")
            print(f"    目标温度: {status['target_temp']}°C")
            print(f"    模式: {status['mode']}")
        elif "position" in status:  # 窗帘
            print(
                f"    位置: {status['position']}% ({"打开" if status['position'] > 0 else "关闭"})"
            )
        elif "is_locked" in status:  # 门锁
            lock_state = "已锁定" if status["is_locked"] else "已解锁"
            door_state = "关闭" if status["is_closed"] else "打开"
            print(f"    锁定: {lock_state}")
            print(f"    门: {door_state}")
        print()


async def process_command(user_input: str, agent: SmartHomeAgent, simulator: HomeSimulator) -> bool:
    """处理用户命令.

    Args:
        user_input: 用户输入
        agent: AI Agent 实例
        simulator: 模拟器实例

    Returns:
        是否继续运行
    """
    user_input = user_input.strip()

    if not user_input:
        return True

    # 处理系统命令
    if user_input.lower() in ["exit", "quit", "q"]:
        return False

    if user_input.lower() == "help":
        print_help()
        return True

    if user_input.lower() == "devices":
        print_device_list(simulator)
        return True

    if user_input.lower() == "status":
        print_device_statuses(simulator)
        return True

    if user_input.lower() == "reset":
        simulator.reset_all()
        print("✓ 所有设备已重置到初始状态\n")
        return True

    if user_input.lower() == "clear":
        os.system("clear" if os.name == "posix" else "cls")
        print_banner()
        return True

    # 使用 AI Agent 处理自然语言命令
    print("\n🤖 正在处理您的请求...\n")
    result = await agent.process(user_input)
    print(f"{result}\n")

    return True


async def run_cli() -> NoReturn:
    """运行 CLI 主循环."""
    print_banner()
    print_help()

    # 初始化模拟器和 Agent
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    print("✅ 系统已就绪! 输入您的命令或自然语言指令 (输入 'help' 查看帮助)\n")

    while True:
        try:
            user_input = input("🏠 您的需求 > ").strip()
            should_continue = await process_command(user_input, agent, simulator)
            if not should_continue:
                print("\n👋 再见! 感谢使用 SmartHome Mock AI\n")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断,再见!\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 发生错误: {e}\n")


def main() -> None:
    """主函数入口."""
    # 加载环境变量
    load_dotenv()

    # 检查 API Key
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置 ZHIPU_API_KEY 环境变量")
        print("   AI 功能将无法使用,请在 .env 文件中设置 API Key")
        print("   提示: 复制 .env.example 为 .env 并填入您的 API Key\n")

    # 运行异步主循环
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出,再见!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
