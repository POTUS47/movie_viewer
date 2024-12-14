# hive_db.py
from pyhive import hive
import threading

# 配置Hive数据库连接参数
hive_config = {
    'host': 'localhost',
    'port': 10000,
}

# 线程局部存储
_thread_locals = threading.local()


def get_hive_connection(database_name='amazon2'):
    """获取Hive数据库连接，并可选地切换到指定的数据库"""
    if not hasattr(_thread_locals, "connection") or _thread_locals.connection is None:
        _thread_locals.connection = hive.Connection(**hive_config)

        cursor = _thread_locals.connection.cursor()
        try:
            switch_database(cursor, database_name)
        finally:
            cursor.close()

    return _thread_locals.connection


def switch_database(cursor, database_name):
    """切换到指定的数据库"""
    use_db_query = f"USE {database_name}"
    cursor.execute(use_db_query)


def close_hive_connection():
    """关闭Hive数据库连接"""
    if hasattr(_thread_locals, "connection") and _thread_locals.connection is not None:
        _thread_locals.connection.close()
        _thread_locals.connection = None
