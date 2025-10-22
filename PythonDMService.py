import dmPython
import pandas as pd
from flask import Flask, jsonify, Response, request
import json
from typing import List, Dict
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import xml.etree.ElementTree as ET
import os
import sys

# 创建Flask应用实例
app = Flask(__name__)


def setup_environment():
    """设置运行时环境，确保达梦加密库能被正确加载"""
    # 获取当前可执行文件所在目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 添加当前目录到库搜索路径
    lib_path = f"{base_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    os.environ['LD_LIBRARY_PATH'] = lib_path

    print(f"环境设置完成 - 库搜索路径: {lib_path}")
    print(f"当前目录文件列表: {os.listdir(base_path)}")


def convert_datetime(obj):
    """将datetime对象转换为字符串，以便JSON序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")


def get_multiple_result_sets(strSp, strParam):
    """调用达梦数据库存储过程并返回多个结果集"""
    # 数据库连接参数
    conn_params = {
        'server': 'localhost',  # 服务器地址
        'user': 'JZX',  # 用户名
        'password': 'XFgs@345',  # 密码
        'port': 5236,  # 端口号，默认5236
        'autoCommit': True  # 是否自动提交
    }

    result_sets = []  # 存储所有结果集
    conn = None  # 显式初始化conn变量
    cursor = None  # 显式初始化cursor变量

    try:
        # 建立连接
        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()

        # 调用返回多个结果集的存储过程
        cursor.callproc(strSp, (strParam,))

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

        if conn:
            conn.commit()

        print(f"成功获取 {len(result_sets)} 个结果集")

    except dmPython.Error as e:
        error_msg = str(e)
        print(f"达梦数据库错误: {error_msg}")

        # 检测加密模块错误
        if "加密模块加载失败" in error_msg or "CODE:-70089" in error_msg:
            print("🔍 检测到加密模块问题，检查环境变量...")
            print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', '未设置')}")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"目录内容: {os.listdir('.')}")

        if conn:
            conn.rollback()
        # 返回空结果集而不是抛出异常
        return []

    except Exception as e:
        print(f"操作错误: {str(e)}")
        if conn:
            conn.rollback()
        # 返回空结果集而不是抛出异常
        return []

    finally:
        # 安全关闭连接和游标
        try:
            if cursor:
                cursor.close()
        except Exception as e:
            print(f"关闭游标时出错: {e}")

        try:
            if conn:
                conn.close()
        except Exception as e:
            print(f"关闭连接时出错: {e}")

    return result_sets


def tables_to_json(tables_data: Dict[str, List[Dict]]) -> str:
    """将多个表的数据转换为JSON字符串"""
    return json.dumps(tables_data, ensure_ascii=False, indent=2)


@app.route('/users', methods=['GET', 'POST'])
def get_users():
    """获取用户数据接口"""
    try:
        if request.method == 'GET':
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            data = request.get_json() or request.form
            param1 = data.get('param1')
            param2 = data.get('param2')

        if not param1:
            return jsonify({"success": False, "message": "param1参数不能为空"})

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
        })


@app.route('/jsonService', methods=['GET', 'POST'])
def get_json():
    """JSON服务接口"""
    try:
        if request.method == 'GET':
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            # 处理多种POST数据格式
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form

            param1 = data.get('param1', '') if data else ''
            param2 = data.get('param2', '') if data else ''

        if not param1:
            return jsonify({"success": False, "message": "param1参数不能为空"})

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
        })


def result_sets_to_xml(result_sets, root_name="ResultSets", encoding="utf-8"):
    """将result_sets列表转换为XML"""
    root = ET.Element(root_name)
    root.set("generated_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.set("total_sets", str(len(result_sets)))

    for set_idx, result_set in enumerate(result_sets, 1):
        if not result_set:  # 跳过空结果集
            continue

        set_node = ET.SubElement(root, "ResultSet")
        set_node.set("id", str(set_idx))

        # 假设result_set是行数据列表
        if result_set and len(result_set) > 0:
            # 获取列名（从第一行数据推断）
            first_row = result_set[0]
            columns = list(first_row.keys()) if isinstance(first_row, dict) else []

            set_node.set("row_count", str(len(result_set)))
            set_node.set("column_count", str(len(columns)))

            # 添加列定义
            columns_node = ET.SubElement(set_node, "Columns")
            for col in columns:
                col_node = ET.SubElement(columns_node, "Column")
                col_node.text = col

            # 添加数据行
            rows_node = ET.SubElement(set_node, "Rows")
            for row_idx, row in enumerate(result_set, 1):
                row_node = ET.SubElement(rows_node, "Row")
                row_node.set("index", str(row_idx))

                for col_idx, (col_name, value) in enumerate(row.items() if isinstance(row, dict) else []):
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

    rough_xml = ET.tostring(root, encoding=encoding)
    pretty_xml = minidom.parseString(rough_xml).toprettyxml(indent="  ", encoding=encoding)

    return "\n".join([line for line in pretty_xml.decode(encoding).split("\n") if line.strip()])


@app.route('/xmlService', methods=['GET', 'POST'])
def get_xml():
    """XML服务接口"""
    try:
        if request.method == 'GET':
            param1 = request.args.get('param1')
            param2 = request.args.get('param2')
        else:
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form

            param1 = data.get('param1', '') if data else ''
            param2 = data.get('param2', '') if data else ''

        if not param1:
            return jsonify({"success": False, "message": "param1参数不能为空"})

        tables = get_multiple_result_sets(param1, param2)
        xml_data = result_sets_to_xml(tables)

        # 设置正确的Content-Type
        response = Response(xml_data, content_type='application/xml; charset=utf-8')
        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理错误: {str(e)}'
        })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 测试数据库连接
        conn_params = {
            'server': 'localhost',
            'user': 'JZX',
            'password': 'XFgs@345',
            'port': 5236,
            'autoCommit': True
        }

        conn = dmPython.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as status")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': '服务正常',
            'database': '连接成功',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'健康检查失败: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


@app.route('/env', methods=['GET'])
def show_environment():
    """显示环境信息（用于调试）"""
    env_info = {
        'current_directory': os.getcwd(),
        'files_in_directory': os.listdir('.'),
        'ld_library_path': os.environ.get('LD_LIBRARY_PATH', '未设置'),
        'python_version': sys.version,
        'dmPython_version': getattr(dmPython, '__version__', '未知'),
        'system_path': sys.path
    }

    return jsonify(env_info)


# 启动服务
if __name__ == '__main__':
    # 设置环境
    setup_environment()

    print("=" * 50)
    print("达梦API服务启动中...")
    print("环境信息:")
    print(f"工作目录: {os.getcwd()}")
    print(f"库路径: {os.environ.get('LD_LIBRARY_PATH', '未设置')}")
    print("=" * 50)

    # 生产环境建议关闭debug模式
    app.run(host='0.0.0.0', port=5000, debug=False)