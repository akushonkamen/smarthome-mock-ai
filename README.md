# SmartHome Mock AI

一个基于 LLM 的智能家居自动化模拟系统，采用"仿真优先"(Simulation First) 架构设计。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户语音/文本指令                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM 推理引擎                             │
│         (GPT-4 / Claude / 本地模型)                          │
│              理解自然语言意图                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Intent Parser (意图解析器)                 │
│    - 提取动作类型 (打开/关闭/调节)                             │
│    - 识别设备目标 (灯光/空调/窗帘...)                          │
│    - 解析参数值 (亮度/温度/颜色...)                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Virtual Device Manager (虚拟设备管理器)           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 虚拟灯光设备  │  │ 虚拟空调设备  │  │ 虚拟窗帘设备  │  ...  │
│  │ - 状态模拟   │  │ - 温度模拟   │  │ - 开合模拟   │         │
│  │ - 日志记录   │  │ - 能耗模拟   │  │ - 日光模拟   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Event Bus (事件总线)                        │
│         - 设备状态变更通知                                     │
│         - 场景联动触发                                         │
│         - 日志收集与监控                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 核心特性

- **LLM 驱动**: 使用大语言模型理解复杂的自然语言指令
- **意图解析**: 结构化解析用户意图为可执行的操作指令
- **虚拟设备**: 完整的设备行为模拟，无需物理硬件
- **场景自动化**: 支持多设备联动和自动化场景
- **可扩展架构**: 模块化设计，易于添加新设备类型

## 📁 项目结构

```
smarthome-mock-ai/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD 流水线配置
├── src/
│   └── smarthome_mock_ai/
│       ├── __init__.py
│       ├── core/               # 核心模块
│       │   ├── llm_client.py   # LLM 客户端
│       │   ├── intent_parser.py # 意图解析器
│       │   └── event_bus.py    # 事件总线
│       ├── devices/            # 设备模块
│       │   ├── base.py         # 设备基类
│       │   ├── light.py        # 灯光设备
│       │   ├── thermostat.py   # 温控设备
│       │   └── curtain.py      # 窗帘设备
│       └── scenarios/          # 场景模块
│           └── automation.py   # 自动化场景
├── tests/                      # 测试目录
│   ├── test_core/
│   ├── test_devices/
│   └── test_scenarios/
├── pyproject.toml              # Poetry 配置
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Poetry (推荐的依赖管理工具)

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/smarthome-mock-ai.git
cd smarthome-mock-ai

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行测试并查看覆盖率
poetry run pytest --cov=src/smarthome_mock_ai --cov-report=html
```

### 代码规范检查

```bash
# 运行 ruff 检查
poetry run ruff check .

# 自动修复问题
poetry run ruff check . --fix

# 格式化代码
poetry run ruff format .
```

## 🧪 CI/CD 流水线

项目使用 GitHub Actions 进行持续集成：

- **触发条件**: `push` 和 `pull_request` 到 `main` 或 `develop` 分支
- **Python 版本**: 测试 Python 3.10, 3.11, 3.12
- **检查项目**:
  - 代码安装
  - Ruff 代码规范检查
  - Ruff 格式检查
  - Pytest 测试执行
  - 代码覆盖率上传

## 🔮 使用示例

```python
from smarthome_mock_ai import SmartHomeController

# 初始化控制器
controller = SmartHomeController()

# 处理自然语言指令
response = controller.process_command(
    "请把客厅的灯光调暗一点，然后将温度设定为 24 度"
)

print(response)
# 输出: "已将客厅灯光亮度调至 70%，空调温度已设定为 24°C"
```

## 🛠️ 技术栈

- **Python 3.10+**: 现代异步编程特性
- **Poetry**: 依赖管理和打包
- **Pytest**: 测试框架
- **Ruff**: 快速的 Python 代码检查和格式化工具
- **GitHub Actions**: CI/CD 自动化

## 📝 开发路线图

- [x] 项目初始化和 CI/CD 配置
- [ ] 实现 LLM 客户端和意图解析器
- [ ] 开发虚拟设备管理器
- [ ] 实现事件总线系统
- [ ] 添加场景自动化功能
- [ ] Web API 接口
- [ ] 前端控制面板

## 🤝 贡献指南

欢迎贡献！请先查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

Your Name - [@your_username](https://github.com/your_username)

## 🙏 致谢

感谢所有开源项目的贡献者
