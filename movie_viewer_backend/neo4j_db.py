from neo4j import GraphDatabase
from flask import jsonify
import time

# 配置 Neo4j 数据库连接参数
NEO4J_URI = "bolt://localhost:7687"  # 或者是你的 Neo4j 服务器地址
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Zhmmysql:2024"

def get_neo4j_driver():
    """获取 Neo4j 数据库驱动"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def execute_query(query, parameters=None):
    """执行 Neo4j 查询，并返回包含查询时间和结果的数据"""
    driver = get_neo4j_driver()
    with driver.session() as session:
        start_time = time.time()  # 记录查询开始时间
        
        # 执行查询并获取结果
        result = session.run(query, parameters or {})
        
        end_time = time.time()  # 记录查询结束时间
        query_time = end_time - start_time
        
        records = [record.data() for record in result]
        driver.close()
        
        return {
            'records': records,
            'query_time': query_time
        }