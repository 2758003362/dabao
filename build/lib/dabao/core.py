"""
dabao.core - 包的核心功能模块
"""


def greet(name: str) -> str:
    """
    生成问候语

    参数:
        name: 要问候的人的名字

    返回:
        包含问候语的字符串
    """
    return f"你好，{name}！欢迎使用dabao包"


def calculate(a: float, b: float, operation: str = "add") -> float:
    """
    执行简单的数学运算

    参数:
        a: 第一个数字
        b: 第二个数字
        operation: 运算类型，支持 'add', 'subtract', 'multiply', 'divide'

    返回:
        运算结果

    异常:
        ValueError: 当运算类型不支持时
        ZeroDivisionError: 当除数为零时
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ZeroDivisionError("除数不能为零")
        return a / b
    else:
        raise ValueError(f"不支持的运算: {operation}")
