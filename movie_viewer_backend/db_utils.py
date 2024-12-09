import mysql.connector

# 配置数据库连接参数
db_config = {
    'user': 'root',
    'password': 'Zhmmysql:2024',
    'host': 'localhost',  # 或者是你的数据库服务器地址
    'database': 'moviesql'
}

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**db_config)