from flask import request, jsonify
from neo4j_db import execute_query
import time

def search_by_title_neo4j(movie_name):
    try:
        # 记录查询开始时间
        start_time = time.time()
        
        # 查询语句
        query = """
        MATCH (m:Movie {movie_name: $movie_name})
        RETURN m.movie_name, m.movie_runtime, m.movie_id
        """
        response = execute_query(query, {"movie_name": movie_name})  # 不需要使用通配符
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        # 处理查询结果
        results = [
            {
                'movie_name': record['m.movie_name'],
                'movie_runtime': record['m.movie_runtime'],
                'movie_id': record['m.movie_id']
            }
            for record in response['records']
        ]
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
