"""
测试dabao包的核心功能
"""

import pytest
from dabao import greet, calculate


def test_greet():
    """测试问候语功能"""
    assert greet("测试用户") == "你好，测试用户！欢迎使用dabao包"
    assert greet("") == "你好，！欢迎使用dabao包"


def test_calculate_add():
    """测试加法运算"""
    assert calculate(2, 3) == 5
    assert calculate(-1, 1) == 0


def test_calculate_subtract():
    """测试减法运算"""
    assert calculate(5, 3, "subtract") == 2
    assert calculate(3, 5, "subtract") == -2


def test_calculate_multiply():
    """测试乘法运算"""
    assert calculate(2, 3, "multiply") == 6
    assert calculate(-2, 3, "multiply") == -6


def test_calculate_divide():
    """测试除法运算"""
    assert calculate(6, 3, "divide") == 2
    assert calculate(5, 2, "divide") == 2.5

    with pytest.raises(ZeroDivisionError):
        calculate(5, 0, "divide")


def test_calculate_invalid_operation():
    """测试无效运算类型"""
    with pytest.raises(ValueError):
        calculate(2, 3, "power")
