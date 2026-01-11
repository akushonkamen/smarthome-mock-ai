# SmartHome Mock AI

一个基于 LLM 的智能家居自动化模拟系统，采用"仿真优先"(Simulation First) 架构设计，集成语音交互、偏好学习和持久化存储。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户语音/文本指令                                 │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────┐                         ┌────────────────┐
│ Voice Listener│                         │   Text Input   │
│  (语音识别)    │                         │   (文本输入)    │
└───────┬───────┘                         └────┬───────────┘
        │                                      │
        └──────────────────┬───────────────────┘
                           ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                      SmartHomeAgent                          │
        │  ┌────────────────┐    ┌─────────────────┐                   │
        │  │ PreferenceModel │    │ InteractionLogger│                   │
        │  │  (偏好学习)      │    │  (交互日志)       │                   │
        │  └────────┬───────┘    └────────┬─────────┘                   │
        │           │                      │                             │
        │  ┌────────▼──────────────────────▼─────────┐                 │
        │  │        LLM 推理引擎 (GLM-4)               │                 │
        │  │   Function Calling + 智能参数调整         │                 │
        │  └────────────────┬─────────────────────────┘                 │
        └───────────────────┼──────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                 Intent Parser (意图解析器)                    │
        │    - 提取动作类型 (打开/关闭/调节)                             │
        │    - 识别设备目标 (灯光/空调/窗帘...)                          │
        │    - 解析参数值 (亮度/温度/颜色...)                            │
        └───────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              HomeSimulator (虚拟设备管理器)                    │
        │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
        │  │ 虚拟灯光设备  │  │ 虚拟空调设备  │  │ 虚拟窗帘设备  │  ...  │
        │  │ - 状态模拟   │  │ - 温度模拟   │  │ - 开合模拟   │         │
        │  │ - 日志记录   │  │ - 能耗模拟   │  │ - 日光模拟   │         │
        │  └─────────────┘  └─────────────┘  └─────────────┘         │
        └───────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                   Persistence Layer                          │
        │  ┌──────────────────┐    ┌──────────────────┐              │
        │  │  DeviceStateManager│    │ InteractionLogger │              │
        │  │   (JSON 状态存储)   │    │  (SQLite 日志)    │              │
        │  └──────────────────┘    └──────────────────┘              │
        └──────────────────────────────────────────────────────────────┘
```

## 🎯 核心特性

### 1. 🤖 LLM 驱动
- 使用智谱AI GLM-4模型理解复杂的自然语言指令
- 基于 OpenAI 兼容的 Function Calling API 实现智能工具调用
- 支持复杂的场景理解和多步操作

### 2. 💡 虚拟设备模拟
无需物理硬件，完整的设备行为模拟：
- **智能灯光**: 亮度、颜色控制
- **智能温控器**: 温度、模式控制
- **智能风扇**: 开关、速度控制
- **智能窗帘**: 开合、位置控制
- **智能门锁**: 锁定、解锁

### 3. 🎯 智能场景识别
- "我要睡觉了" → 自动关闭所有灯光
- "太热了" → 调低温度或打开风扇
- "我要看电视" → 调暗灯光并关闭窗帘
- "出门了" → 关闭所有灯光并锁门
- "回家啦" → 打开灯光并调到舒适温度

### 4. 🎤 语音交互
- 支持语音输入（基于 OpenAI Whisper API）
- 实时语音转文字
- 命令：输入 `r` 或 `record` 开始录音

### 5. 🧠 偏好学习
- 自动学习用户使用习惯
- 基于时间段和场景的个性化推荐
- 置信度评估和智能参数调整
- 用户反馈机制（纠正错误的操作）

### 6. 💾 持久化存储
- **设备状态持久化**: 自动保存设备状态到 JSON 文件
- **交互历史记录**: SQLite 数据库存储所有交互
- **用户反馈记录**: 记录正/负反馈用于模型训练

### 7. ⚡ 友好的 CLI 界面
- 彩色输出和清晰的命令反馈
- 实时状态显示
- 丰富的系统命令

## 📁 项目结构

```
smarthome-mock-ai/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD 流水线配置
├── data/                       # 数据目录（自动创建）
│   ├── devices.json            # 设备状态持久化
│   ├── smarthome.db            # SQLite 数据库
│   └── preferences.json        # 用户偏好存储
├── src/
│   └── smarthome_mock_ai/
│       ├── __init__.py         # 包初始化
│       ├── devices.py          # 虚拟设备定义
│       ├── simulator.py        # 设备模拟器和管理器
│       ├── agent.py            # AI Agent (LLM + Function Calling)
│       ├── voice.py            # 语音输入模块
│       ├── learning.py         # 偏好学习模块
│       ├── device_persistence.py  # 设备状态持久化
│       ├── interaction_logger.py # 交互日志记录
│       └── persistence.py      # 数据库连接管理
├── tests/                      # 测试目录
│   ├── test_persistence.py
│   ├── test_learning.py
│   ├── test_voice.py
│   └── ...
├── main.py                     # CLI 程序入口
├── .env.example                # 环境变量示例
├── pyproject.toml              # Poetry 配置
├── TODO.md                     # 开发路线图
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Poetry (推荐的依赖管理工具)

### 安装

```bash
# 克隆仓库
git clone https://github.com/akushonkamen/smarthome-mock-ai.git
cd smarthome-mock-ai

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 配置 API Key
cp .env.example .env
# 编辑 .env 文件，添加：
# ZHIPU_API_KEY=your_zhipu_api_key
# OPENAI_API_KEY=your_openai_api_key  # 用于语音转文字功能（可选）
```

### 运行程序

```bash
# 启动 CLI 交互界面
poetry run python main.py
```

### CLI 命令

启动后，您可以使用以下命令：

| 命令 | 说明 |
|------|------|
| `help` | 显示帮助信息 |
| `status` | 查看所有设备状态 |
| `devices` | 列出所有可用设备 |
| `record` / `r` | 使用语音输入（需要麦克风） |
| `preferences` | 显示已学习的用户偏好 |
| `train` | 重新训练偏好模型 |
| `reset` | 重置所有设备到初始状态 |
| `clear` | 清空屏幕 |
| `exit` / `quit` | 退出程序 |

### 自然语言示例

```bash
# 灯光控制
🏠 您的需求 > 打开客厅灯
🏠 您的需求 > 把卧室灯调暗一点
🏠 您的需求 > 设置灯光为红色

# 温度控制
🏠 您的需求 > 太热了
🏠 您的需求 > 把温度调到25度

# 场景自动化
🏠 您的需求 > 我要睡觉了
🏠 您的需求 > 我要看电视
🏠 您的需求 > 出门了
🏠 您的需求 > 回家啦

# 复合指令
🏠 您的需求 > 打开客厅灯并调到50%亮度
```

### 用户反馈

每次执行操作后，系统会询问是否正确：

```bash
👆 这是否正确? (y/n, 或按 Enter 跳过):
```

- 输入 `y` - 正确，系统会加强这个偏好
- 输入 `n` - 错误，系统会询问正确的操作并学习
- 按 Enter - 跳过反馈

## 🧪 测试

```bash
# 运行所有测试
poetry run pytest

# 运行测试并查看覆盖率
poetry run pytest --cov=src/smarthome_mock_ai --cov-report=html

# 运行特定测试文件
poetry run pytest tests/test_persistence.py
```

### 代码规范检查

```bash
# 运行 ruff 检查
poetry run ruff check .

# 自动修复问题
poetry run ruff check . --fix
```

## 🔮 使用示例

### Python API 使用

```python
from smarthome_mock_ai.simulator import HomeSimulator
from smarthome_mock_ai.agent import SmartHomeAgent
import asyncio

# 初始化
simulator = HomeSimulator()
agent = SmartHomeAgent(simulator)

# 处理自然语言指令
async def control_home():
    # 单个指令
    result = await agent.process("打开客厅灯")
    print(result)

    # 场景指令
    result = await agent.process("我要睡觉了")
    # 输出: ✓ 已关闭 客厅灯
    #       ✓ 已关闭 卧室灯
    #       ✓ 已关闭 厨房灯
    #       ✓ 已关闭 浴室灯

    # 复合指令
    result = await agent.process("把温度调到25度，打开风扇")
    print(result)

asyncio.run(control_home())
```

### 偏好学习示例

```python
from smarthome_mock_ai.learning import PreferenceModel

# 创建偏好模型
model = PreferenceModel()

# 训练模型（从历史交互中学习）
stats = model.train()
print(f"学习了 {stats['preferences_learned']} 个偏好")

# 预测用户偏好
context = {"time_period": "evening", "user_input": "有点冷"}
adjusted_params = model.adjust_arguments("set_temperature", {"temp": 22}, context)
# 可能会返回: {"temp": 24}  # 如果用户在晚上喜欢更温暖
```

### 语音输入示例

```bash
# 在 CLI 中
🏠 您的需求 > r

# 系统会提示：
🎤 语音输入模式
# 请开始说话...
# [正在录音...]
# [录音完成]

📝 识别结果: "打开客厅灯"

🤖 正在处理您的请求...
✓ 已打开 客厅灯

👆 这是否正确? (y/n, 或按 Enter 跳过):
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| **Python** | 3.10+ |
| **LLM** | 智谱AI GLM-4 |
| **HTTP 客户端** | httpx |
| **语音识别** | SpeechRecognition + OpenAI Whisper API |
| **数据库** | SQLite3 |
| **环境变量管理** | python-dotenv |
| **依赖管理** | Poetry |
| **测试框架** | Pytest + pytest-asyncio |
| **代码检查** | Ruff |
| **CI/CD** | GitHub Actions |

## 📝 开发路线图

### ✅ Phase 1: Foundation (已完成)
- [x] 项目初始化和 CI/CD 配置
- [x] 实现虚拟设备管理器
- [x] 实现 AI Agent 和 CLI 界面
- [x] LLM 客户端和 Function Calling

### ✅ Phase 2: Persistence Layer (已完成)
- [x] SQLite 数据库基础设施
- [x] 设备状态持久化
- [x] 交互历史记录

### ✅ Phase 3: Voice Interface (已完成)
- [x] 语音输入模块
- [x] OpenAI Whisper API 集成
- [x] CLI 语音模式

### ✅ Phase 4: Reinforcement Learning (已完成)
- [x] 用户反馈机制
- [x] 偏好学习模型
- [x] 智能参数调整

### ✅ Phase 5: Final Polish (已完成)
- [x] 完整回归测试
- [x] 文档更新

### 🚀 未来计划
- [ ] 更多设备类型（扫地机器人、智能插座等）
- [ ] 事件总线和场景联动
- [ ] Web API 接口
- [ ] 前端控制面板
- [ ] 多用户支持
- [ ] 云端同步

## 🧠 偏好学习机制

系统使用上下文强盗（Contextual Bandit）算法学习用户偏好：

### 学习的维度

1. **时间上下文**: 早晨、下午、晚上、深夜等
2. **自然语言线索**: "太热"、"太冷"、"有点暗"等
3. **设备类型**: 灯光、温度、风扇等

### 示例学习场景

```
用户输入: "太热了"
时间: 晚上 8 点
系统操作: 设置温度到 24°C
用户反馈: ✓ 正确

→ 学习到偏好: 晚上 + "太热" → 24°C

下次同样场景:
用户输入: "太热了"
时间: 晚上 8 点
系统操作: 自动设置到 24°C（已学习偏好）
```

## 💾 数据存储

### 设备状态持久化
- **文件**: `data/devices.json`
- **内容**: 所有设备的状态（开关、亮度、温度等）
- **时机**: 每次设备状态变更时自动保存

### 交互日志
- **文件**: `data/smarthome.db`
- **表**: `interaction_logs`
- **字段**:
  - `id`: 主键
  - `timestamp`: 时间戳
  - `user_command`: 用户命令
  - `agent_action`: Agent 执行的操作
  - `user_feedback`: 用户反馈 (+1/-1)
  - `corrected_command`: 纠正的命令

### 用户偏好
- **文件**: `data/preferences.json`
- **内容**: 学习到的用户偏好（权重、置信度）

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

Your Name - [@your_username](https://github.com/your_username)

## 🙏 致谢

- [智谱AI](https://open.bigmodel.cn/) - 提供 GLM-4 大语言模型 API
- [OpenAI](https://openai.com/) - 提供 Whisper API 和 Function Calling 规范
- 所有开源项目的贡献者
