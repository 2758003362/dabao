import dmPython
import pandas as pd

from flask import Flask, jsonify, request

import json
from typing import List, Dict

from datetime import datetime

# 创建Flask应用实例
app = Flask(__name__)


def get_multiple_result_sets():
    """调用达梦存储过程JZX.GET_TEST0，返回所有结果集（核心数据库逻辑）"""
    # 🔔 请根据实际环境调整数据库连接参数
    conn_params = {
        'server': '192.168.0.191',  # 数据库服务器IP
        'user': 'JZX',  # 数据库用户名
        'password': 'XFgs@345',  # 数据库密码
        'port': 5236,  # 达梦默认端口（通常为5236）
        'autoCommit': True  # 开启自动提交，避免事务阻塞
    }

    result_sets = []  # 存储存储过程返回的所有表数据
    try:
        # 建立达梦数据库连接
        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()

        # 调用达梦存储过程
        cursor.callproc("JZX.GET_TEST0")

        # 循环获取所有结果集（处理存储过程多表返回场景）
        while True:
            # 获取当前结果集的列名（无数据时cursor.description为None）
            columns = [col[0] for col in cursor.description] if cursor.description else []
            # 读取行数据，转换为「列名:值」的字典格式（便于JSON序列化）
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if rows:  # 若当前结果集有数据，添加到总列表
                result_sets.append(rows)

            # 检查是否还有下一个结果集，无则退出循环
            if not cursor.nextset():
                break

        conn.commit()  # 提交事务（若存储过程包含插入/更新操作）

    except Exception as e:
        # 捕获异常并打印错误信息，回滚事务
        print(f"达梦数据库操作异常: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        # 关闭游标和连接，释放资源（避免内存泄漏）
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    return result_sets


def convert_datetime(obj):
    """自定义JSON序列化函数，处理datetime类型（避免JSON报错）"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')  # 统一时间格式为「年-月-日 时:分:秒」
    raise TypeError(f"不支持的序列化类型: {type(obj)}")


# 🔗 API接口1：获取存储过程返回的所有数据（GET请求）
@app.route('/users', methods=['GET'])
def get_users():
    # 调用函数获取数据库数据
    db_data = get_multiple_result_sets()
    # 转换为JSON字符串（支持中文、格式化输出）
    json_response = json.dumps(
        db_data,
        default=convert_datetime,  # 处理datetime字段
        ensure_ascii=False,  # 中文不转义
        indent=4  # 格式化输出，便于调试
    )
    return json_response


# 🔗 API接口2：获取单个模拟用户（示例功能，可按需删除）
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    mock_users = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25}
    ]
    target_user = next((u for u in mock_users if u['id'] == user_id), None)
    if target_user:
        return jsonify({"user": target_user})
    return jsonify({"error": "用户不存在"}), 404  # 404状态码：资源未找到


# 🚀 启动Flask服务（生产环境配置）
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # 允许局域网访问
        port=5000,  # 服务端口（可修改）
        debug=False  # 关闭调试模式，避免安全风险
    )