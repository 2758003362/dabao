import dmPython
import pandas as pd

from flask import Flask, jsonify, request

import json
from typing import List, Dict

from datetime import datetime

# 创建Flask应用实例
app = Flask(__name__)

def get_multiple_result_sets():
    # 数据库连接参数（请根据实际环境调整服务器地址/账号密码）
    conn_params = {
        'server': '192.168.0.191',  # 达梦数据库服务器地址
        'user': 'JZX',              # 数据库用户名
        'password': 'XFgs@345',     # 数据库密码
        'port': 5236,               # 达梦默认端口5236
        'autoCommit': True          # 开启自动提交
    }

    result_sets = []  # 存储存储过程返回的所有结果集
    try:
        # 建立达梦数据库连接
        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()

        # 调用达梦存储过程（JZX.GET_TEST0）
        cursor.callproc("JZX.GET_TEST0")

        # 循环获取所有结果集（存储过程可能返回多个表数据）
        while True:
            # 获取当前结果集的列名
            columns = [column[0] for column in cursor.description] if cursor.description else []
            # 获取当前结果集的所有行数据
            rows = []
            for row in cursor.fetchall():
                # 每行数据转换为「列名:值」的字典格式
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)
            # 若当前结果集有数据，添加到总列表
            if rows:
                result_sets.append(rows)
            # 检查是否还有下一个结果集，无则退出循环
            if not cursor.nextset():
                break

        conn.commit()  # 提交事务（若存储过程有写操作）

    except Exception as e:
        # 捕获异常并打印错误信息，回滚事务
        print(f"达梦数据库操作错误: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        # 关闭游标和连接，释放资源
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    return result_sets

def convert_datetime(obj):
    """将datetime类型转换为字符串，解决JSON序列化问题"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')  # 统一时间格式
    raise TypeError(f"不支持的序列化类型: {type(obj)}")

# 1. 接口：获取存储过程返回的所有数据（原/users接口复用）
@app.route('/users', methods=['GET'])
def get_users():
    # 调用函数获取达梦存储过程结果
    tables_data = get_multiple_result_sets()
    # 转换为JSON字符串（处理datetime、中文显示）
    json_result = json.dumps(
        tables_data,
        default=convert_datetime,  # 自定义时间序列化
        ensure_ascii=False,        # 中文不转义
        indent=4                   # 格式化输出，便于阅读
    )
    return json_result

# 2. 接口：获取单个模拟用户（保留原功能，可删除）
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # 模拟用户数据（实际项目可删除，替换为数据库查询）
    users = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25}
    ]
    # 查找匹配ID的用户
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify({"user": user})
    return jsonify({"error": "用户不存在"}), 404  # 404：资源不存在

# 启动Flask服务（关键：关闭debug模式，避免权限问题）
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # 允许局域网内其他设备访问
        port=5000,       # 服务端口（可根据需求修改）
        debug=False      # 生产环境必须关闭debug，避免多进程权限错误
    )