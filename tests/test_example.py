"""示例测试文件 - 用于验证 CI/CD 流水线。"""

import pytest


def test_example_assertion():
    """示例测试 - 验证基本功能。"""
    assert True


def test_project_version():
    """测试项目版本号。"""
    from smarthome_mock_ai import __version__

    assert __version__ == "0.1.0"


def test_simple_math():
    """简单数学测试。"""
    result = 2 + 2
    assert result == 4


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, 1),
        (2, 4),
        (3, 9),
        (4, 16),
    ],
)
def test_square_function(input_value, expected):
    """参数化测试 - 计算平方。"""
    result = input_value**2
    assert result == expected
