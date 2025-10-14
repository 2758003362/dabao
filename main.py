import dmPython
import pandas as pd

from flask import Flask, jsonify, request

import json
from typing import List, Dict

from datetime import datetime

# 创建Flask应用实例
app = Flask(__name__)


def get_multiple_result_sets():
    """调用达梦存储过程JZX.GET_TEST0，返回所有结果集"""
    # 数据库连接参数（请根据实际环境修改）
    conn_params = {
        'server': '192.168.0.191',  # 数据库IP
        'user': 'JZX',  # 用户名
        'password': 'XFgs@345',  # 密码
        'port': 5236,  # 达梦默认端口
        'autoCommit': True  # 自动提交事务
    }

    result_sets = []  # 存储所有结果集
    try:
        # 建立数据库连接
        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()

        # 调用存储过程
        cursor.callproc("JZX.GET_TEST0")

        # 循环获取所有结果集
        while True:
            # 获取列名
            columns = [col[0] for col in cursor.description] if cursor.description else []
            # 转换行数据为字典
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if rows:
                result_sets.append(rows)

            # 检查是否有下一个结果集
            if not cursor.nextset():
                break

        conn.commit()

    except Exception as e:
        print(f"数据库操作异常: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        # 释放资源
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    return result_sets


def convert_datetime(obj):
    """处理datetime类型的JSON序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"不支持的类型: {type(obj)}")


# API接口：获取存储过程数据
@app.route('/users', methods=['GET'])
def get_users():
    db_data = get_multiple_result_sets()
    json_response = json.dumps(
        db_data,
        default=convert_datetime,
        ensure_ascii=False,
        indent=4
    )
    return json_response


# 示例接口：获取单个用户
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    mock_users = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25}
    ]
    target_user = next((u for u in mock_users if u['id'] == user_id), None)
    if target_user:
        return jsonify({"user": target_user})
    return jsonify({"error": "用户不存在"}), 404


# 启动服务
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
