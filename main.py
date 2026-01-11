"""SmartHome Mock AI - 主程序入口."""

import asyncio
import os
import sys
from typing import Any, NoReturn

from dotenv import load_dotenv
from smarthome_mock_ai.agent import SmartHomeAgent
from smarthome_mock_ai.simulator import HomeSimulator
from smarthome_mock_ai.voice import VoiceListener, get_default_voice_listener


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
  record / r    - 使用语音输入 (🎤 按下开始录音)
  preferences   - 显示已学习的用户偏好
  train         - 重新训练偏好模型
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


async def process_command(
    user_input: str,
    agent: SmartHomeAgent,
    simulator: HomeSimulator,
    voice_listener: VoiceListener | None = None
) -> bool:
    """处理用户命令.

    Args:
        user_input: 用户输入
        agent: AI Agent 实例
        simulator: 模拟器实例
        voice_listener: 语音监听器实例

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

    # Handle voice recording command
    if user_input.lower() in ["record", "r"]:
        await handle_voice_input(agent, simulator, voice_listener)
        return True

    # Handle preferences command
    if user_input.lower() == "preferences":
        await handle_preferences_command(agent)
        return True

    # Handle train command
    if user_input.lower() == "train":
        await handle_train_command(agent)
        return True

    # 使用 AI Agent 处理自然语言命令
    print("\n🤖 正在处理您的请求...\n")
    result = await agent.process(user_input)

    # Print the result message
    print(f"{result['message']}\n")

    # Collect feedback if action was performed
    if result["success"] and result["action_id"] and result.get("actions_taken"):
        await collect_feedback(result["action_id"], agent.logger)

    return True


async def collect_feedback(action_id: str, logger: Any) -> None:
    """Collect user feedback for an action.

    Args:
        action_id: The ID of the action to get feedback for
        logger: The interaction logger instance
    """
    if logger is None:
        return

    try:
        feedback = input("👆 这是否正确? (y/n, 或按 Enter 跳过): ").strip().lower()

        if not feedback:
            return  # User skipped feedback

        if feedback in ["y", "yes", "是"]:
            # Positive feedback
            logger.record_feedback(action_id, 1)
            print("✓ 感谢您的反馈!\n")
        elif feedback in ["n", "no", "否"]:
            # Negative feedback - ask for correction
            correction = input("📝 请描述正确的操作 (或按 Enter 跳过): ").strip()
            if correction:
                logger.record_feedback(action_id, -1, correction)
                print("✓ 感谢您的反馈! 我们会学习这个改进。\n")
            else:
                logger.record_feedback(action_id, -1)
                print("✓ 反馈已记录。\n")
        else:
            print("⚠️  无效输入,已跳过反馈。\n")

    except Exception as e:
        print(f"⚠️  记录反馈时出错: {e}\n")


async def handle_preferences_command(agent: SmartHomeAgent) -> None:
    """Handle the 'preferences' command.

    Args:
        agent: SmartHomeAgent instance
    """
    summary = agent.get_preference_summary()

    if "error" in summary:
        print(f"\n❌ {summary['error']}\n")
        return

    print("\n📊 已学习的用户偏好:\n")

    tool_display_names = {
        "set_temperature": "温度设置",
        "set_light_brightness": "灯光亮度",
        "set_fan_speed": "风扇速度",
    }

    if not summary["tools"]:
        print("  尚未学习到任何偏好。\n")
        print("  提示: 多次使用系统并纠正错误的建议,系统将逐渐学习您的偏好。\n")
        return

    for tool_name, contexts in summary["tools"].items():
        display_name = tool_display_names.get(tool_name, tool_name)
        print(f"  🎯 {display_name}:")

        for context, prefs in contexts.items():
            print(f"    场景: {context}")
            for pref in prefs[:3]:  # Show top 3
                print(f"      - 值: {pref['value']}, 置信度: {pref['confidence']}")
        print()

    print(f"  总共学习了 {summary['total_preferences']} 个偏好。\n")


async def handle_train_command(agent: SmartHomeAgent) -> None:
    """Handle the 'train' command to retrain the preference model.

    Args:
        agent: SmartHomeAgent instance
    """
    print("\n📚 正在重新训练偏好模型...\n")

    stats = agent.train_preferences()

    if "error" in stats:
        print(f"❌ 训练失败: {stats['error']}\n")
        return

    print(f"✓ 训练完成!\n")
    print(f"  处理的交互记录: {stats.get('total_interactions', 0)}")
    print(f"  学习的偏好数量: {stats.get('preferences_learned', 0)}")

    if stats.get("tools_updated"):
        print(f"  更新的工具: {', '.join(stats['tools_updated'])}")

    print()


async def handle_voice_input(
    agent: SmartHomeAgent,
    simulator: HomeSimulator,
    voice_listener: VoiceListener | None = None
) -> None:
    """Handle voice input from the user.

    Args:
        agent: AI Agent 实例
        simulator: 模拟器实例
        voice_listener: 语音监听器实例
    """
    if voice_listener is None:
        print("\n❌ 语音功能未初始化。请确保已安装 pyaudio 库。\n")
        return

    if not voice_listener.is_available():
        print("\n❌ 未检测到麦克风设备。请检查:\n")
        print("   1. 是否已连接麦克风\n")
        print("   2. 系统声音设置是否正确\n")
        print("   3. 是否已安装 pyaudio: pip install pyaudio\n")
        return

    # Check for OpenAI API key
    if not voice_listener.OPENAI_API_KEY:
        print("\n❌ 未设置 OPENAI_API_KEY 环境变量。")
        print("   请在 .env 文件中添加您的 OpenAI API Key 以使用语音转文字功能。\n")
        return

    try:
        # Listen and transcribe
        print("\n" + "="*50)
        print("🎤 语音输入模式")
        print("="*50 + "\n")

        transcribed_text = await voice_listener.listen_and_transcribe()

        if not transcribed_text:
            print("\n⚠️ 未能识别到语音内容,请重试。\n")
            return

        print(f"\n📝 识别结果: \"{transcribed_text}\"\n")

        # Process the transcribed text through the agent
        print("🤖 正在处理您的请求...\n")
        result = await agent.process(transcribed_text)
        print(f"{result['message']}\n")

        # Collect feedback if action was performed
        if result["success"] and result["action_id"] and result.get("actions_taken"):
            await collect_feedback(result["action_id"], agent.logger)

    except RuntimeError as e:
        print(f"\n❌ 语音输入错误: {e}\n")
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}\n")


async def run_cli() -> NoReturn:
    """运行 CLI 主循环."""
    print_banner()
    print_help()

    # 初始化模拟器和 Agent
    simulator = HomeSimulator()
    agent = SmartHomeAgent(simulator)

    # Train preferences on startup
    print("📚 正在加载您的偏好设置...")
    stats = agent.train_preferences()
    if "error" not in stats and stats.get("total_interactions", 0) > 0:
        print(f"✓ 已加载 {stats['total_interactions']} 条历史交互记录")
        if stats.get("preferences_learned", 0) > 0:
            print(f"✓ 已学习 {stats['preferences_learned']} 个用户偏好")
    print()

    # Initialize voice listener
    voice_listener = None
    try:
        voice_listener = get_default_voice_listener()
        if voice_listener.is_available():
            print("✅ 语音输入已就绪! (输入 'r' 或 'record' 开始录音)")
        else:
            print("⚠️  未检测到麦克风,语音输入功能不可用")
    except Exception as e:
        print(f"⚠️  语音功能初始化失败: {e}")

    print("\n✅ 系统已就绪! 输入您的命令或自然语言指令 (输入 'help' 查看帮助)\n")

    while True:
        try:
            user_input = input("🏠 您的需求 > ").strip()
            should_continue = await process_command(user_input, agent, simulator, voice_listener)
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
