import dmPython
import pandas as pd

from flask import Flask, jsonify, Response, request

import json
from typing import List, Dict

from datetime import datetime

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

import xml.etree.ElementTree as ET

# 创建Flask应用实例
app = Flask(__name__)

def convert_datetime(obj):
    """将datetime对象转换为字符串，以便JSON序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

def get_multiple_result_sets(strSp, strParam):
    # 数据库连接参数
    conn_params = {
        'server': 'localhost',  # 服务器地址
        'user': 'JZX',  # 用户名
        'password': 'XFgs@345',  # 密码
        'port': 5236,  # 端口号，默认5236
        'autoCommit': True  # 是否自动提交
    }

    result_sets = []  # 存储所有结果集
    conn = None  # 初始化conn为None，避免未定义错误
    cursor = None  # 初始化cursor为None
    try:
        # 建立连接
        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()

        # 调用返回多个结果集的存储过程
        cursor.callproc(strSp, (strParam,))  # 修复参数元组格式（确保逗号，避免被识别为单个参数）

        # 获取所有结果集
        while True:
            # 获取列名
            columns = [column[0] for column in cursor.description] if cursor.description else []

            # 获取当前结果集的所有行
            rows = []
            for row in cursor.fetchall():
                # 将每行转换为字典
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)

            # 如果有数据，添加到结果列表
            if rows:
                result_sets.append(rows)

            # 检查是否还有更多结果集
            if not cursor.nextset():
                break

        conn.commit()

    except Exception as e:
        print(f"操作错误: {str(e)}")
        if conn is not None:  # 仅当连接成功创建时才执行回滚
            try:
                conn.rollback()
            except Exception as rollback_err:
                print(f"回滚失败: {str(rollback_err)}")
    finally:
        # 确保游标和连接关闭（仅当存在时）
        if cursor is not None:
            try:
                cursor.close()
            except Exception as close_cursor_err:
                print(f"关闭游标失败: {str(close_cursor_err)}")
        if conn is not None:
            try:
                conn.close()
            except Exception as close_conn_err:
                print(f"关闭连接失败: {str(close_conn_err)}")

    return result_sets

def tables_to_json(tables_data: Dict[str, List[Dict]]) -> str:
    """将多个表的数据转换为JSON字符串"""
    return json.dumps(tables_data, ensure_ascii=False, indent=2)

# 1. 获取所有用户 (GET请求)
@app.route('/users', methods=['GET','POST'])
def get_users():
    try:
        if request.method == 'GET':
            # 处理GET请求，从查询参数获取
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            # 处理POST请求，先尝试从JSON获取，再尝试从表单获取
            data = request.get_json() or request.form
            param1 = data.get('param1') if data.get('param1') else None
            param2 = data.get('param2') if data.get('param2') else None

        tables = get_multiple_result_sets(param1, param2)

        # 转换为JSON
        json_result = json.dumps(
            tables,
            default=convert_datetime,
            ensure_ascii=False,
            indent=4
        )

        return json_result
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理错误: {str(e)}'
        }), 500

# 2. 返回存储过程数据JSON格式 (GET POST请求)
@app.route('/jsonService', methods=['GET','POST'])
def get_json():
    try:
        if request.method == 'GET':
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            # 兼容多种POST数据格式
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()  # 表单数据转换为字典
            param1 = data.get('param1', '')
            param2 = data.get('param2', '')

        tables = get_multiple_result_sets(param1, param2)

        json_result = json.dumps(
            tables,
            default=convert_datetime,
            ensure_ascii=False,
            indent=4
        )

        return json_result

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理错误: {str(e)}'
        }), 500

def result_sets_to_xml(result_sets, root_name="ResultSets", encoding="utf-8"):
    """将result_sets列表转换为XML"""
    root = ET.Element(root_name)
    root.set("generated_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.set("total_sets", str(len(result_sets)))

    for set_idx, result_set in enumerate(result_sets, 1):
        # 假设结果集结构为列表嵌套字典（适配当前代码返回格式）
        if not result_set:
            continue  # 跳过空结果集
        # 提取列名（从第一行数据中获取）
        columns = list(result_set[0].keys()) if result_set else []
        # 表名默认使用"ResultSet_{序号}"（原代码未返回表名，此处为兼容处理）
        table_name = f"ResultSet_{set_idx}"

        set_node = ET.SubElement(root, "ResultSet")
        set_node.set("id", str(set_idx))
        set_node.set("table_name", table_name)
        set_node.set("row_count", str(len(result_set)))
        set_node.set("column_count", str(len(columns)))

        # 列定义节点
        columns_node = ET.SubElement(set_node, "Columns")
        for col in columns:
            col_node = ET.SubElement(columns_node, "Column")
            col_node.text = col

        # 数据行节点
        rows_node = ET.SubElement(set_node, "Rows")
        for row_idx, row in enumerate(result_set, 1):
            row_node = ET.SubElement(rows_node, "Row")
            row_node.set("index", str(row_idx))

            for col_idx, col_name in enumerate(columns):
                value = row.get(col_name)
                # 处理特殊数据类型
                if isinstance(value, datetime):
                    cell_text = value.strftime("%Y-%m-%d %H:%M:%S")
                elif value is None:
                    cell_text = ""
                else:
                    cell_text = str(value)

                cell_node = ET.SubElement(row_node, "Cell")
                cell_node.set("column", col_name)
                cell_node.set("column_index", str(col_idx))
                cell_node.text = cell_text

    # 格式化XML
    rough_xml = ET.tostring(root, encoding=encoding)
    pretty_xml = minidom.parseString(rough_xml).toprettyxml(indent="  ", encoding=encoding)
    return "\n".join([line for line in pretty_xml.decode(encoding).split("\n") if line.strip()])

# 3. 返回存储过程数据XML格式 (GET POST请求)
@app.route('/xmlService', methods=['GET', 'POST'])
def get_xml(encoding="utf-8"):
    try:
        if request.method == 'GET':
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            param1 = data.get('param1', '')
            param2 = data.get('param2', '')

        tables = get_multiple_result_sets(param1, param2)
        xml_data = result_sets_to_xml(tables)
        return Response(xml_data, mimetype='application/xml')  # 正确设置XML响应类型
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理错误: {str(e)}'
        }), 500

# 启动服务
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)