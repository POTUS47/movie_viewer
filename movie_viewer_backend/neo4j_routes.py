from flask import request, jsonify
from neo4j_db import execute_query
import time
from datetime import date

def convert_date_to_str(data):
    """递归将数据中的 Date 类型转换为字符串"""
    if isinstance(data, dict):
        return {k: convert_date_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_date_to_str(item) for item in data]
    elif hasattr(data, "isoformat"):  # 处理 Date 类型
        return data.isoformat()
    return data

def search_by_title_neo4j(title):
    try:
        # 记录查询开始时间
        start_time = time.time()
        formatted_name = title.strip().lower()

        # 查询语句：返回整个 Movie 节点的所有属性
        query = """
        MATCH (m:Movie)
        WHERE toLower(m.movie_name) CONTAINS $title
        RETURN m
        """

        # 执行查询
        response = execute_query(query, {"title": formatted_name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 处理查询结果，将节点属性展开为字典
        results = [convert_date_to_str(record['m']) for record in response['records']]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.2f}s"
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500

def search_by_time_neo4j():
    query_type = request.args.get('type')
    year = request.args.get('year')
    month = request.args.get('month')
    quarter = request.args.get('quarter')
    weekday = request.args.get('weekday')

    # 构造 Cypher 查询语句和参数
    if query_type == 'year':
        cypher_query = """
            MATCH (m:Movie)
            WHERE m.release_time.year = $year
            RETURN m.movie_id AS movie_id, m.movie_name AS movie_name,
                   m.release_time AS release_time, m.score AS average_score
        """
        params = {"year": int(year)}
    elif query_type == 'month':
        cypher_query = """
            MATCH (m:Movie)
            WHERE m.release_time.year = $year
              AND m.release_time.month = $month
            RETURN m.movie_id AS movie_id, m.movie_name AS movie_name,
                   m.release_time AS release_time, m.score AS average_score
        """
        params = {"year": int(year), "month": int(month)}
    elif query_type == 'quarter':
        cypher_query = """
            MATCH (m:Movie)
            WHERE m.release_time.year = $year
              AND (m.release_time.month + 2) / 3 = $quarter
            RETURN m.movie_id AS movie_id, m.movie_name AS movie_name,
                   m.release_time AS release_time, m.score AS average_score
        """
        params = {"year": int(year), "quarter": int(quarter)}
    elif query_type == 'weekday':
        cypher_query = """
            MATCH (m:Movie)
            WHERE m.release_time.year = $year
              AND m.release_time.month = $month
              AND m.release_time.weekday = $weekday
            RETURN m.movie_id AS movie_id, m.movie_name AS movie_name,
                   m.release_time AS release_time, m.score AS average_score
        """
        params = {"year": int(year), "month": int(month), "weekday": int(weekday)}
    else:
        return jsonify({"error": "Invalid query type"}), 400

    # 使用 execute_query 执行查询
    result = execute_query(cypher_query, params)
    records = result['records']

    # 格式化结果，替换 release_time 为 release_date
    formatted_records = [
        {
            "movie_id": record['movie_id'],
            "movie_name": record['movie_name'],
            "release_date": convert_date_to_str(record['release_time']),  # 替换字段名
            "average_score": record['average_score']
        }
        for record in records
    ]

    return jsonify({
        'results': formatted_records,
        'query_time': f"{result['query_time']:.6f}"  # 查询时间
    })


# 查询所有导演
def search_every_director_neo4j(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        formatted_name = name.strip().lower()
        # Neo4j 查询：根据导演名字查找符合条件的导演
        query = """
         MATCH (d:Director)
         WHERE toLower(d.director_name) CONTAINS $name
         RETURN d.director_name AS director_name, d.director_id AS director_id
        """

        # 执行查询
        response = execute_query(query, {'name': formatted_name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 处理查询结果
        results = [
            {
                'director_name': record['director_name'],
                'director_id': record['director_id']
            }
            for record in response['records']
        ]

        if not results:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


def search_by_director_neo4j(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # 查询导演的电影信息
        query = """
        MATCH (d:Director)-[:DIRECTED]->(m:Movie)
        WHERE d.director_name = $name
        RETURN
            m.movie_id AS movie_id,
            m.movie_name AS movie_name,
            m.movie_runtime AS movie_runtime,
            m.version AS version
        """

        # 执行查询
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 处理结果
        results = [
            {
                "movie_id": record['movie_id'],
                "movie_name": record['movie_name'],
                "movie_runtime": record['movie_runtime'],
                "version": record['version']
            }
            for record in response['records']
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500

# 查询所有演员
def search_every_actor_neo4j(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        formatted_name = name.strip().lower()

        # 查询演员的名字（精确或模糊匹配）
        query = """
        MATCH (a:Actor)
        WHERE toLower(a.actor_name) CONTAINS $name
        RETURN a.actor_name AS actor_name, a.actor_id AS actor_id
        """

        response = execute_query(query, {"name": formatted_name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 处理结果
        results = [
            {"actor_name": record['actor_name'], "actor_id": record['actor_id']}
            for record in response.get('records', [])
        ]

        # 如果没有找到记录，返回空结果
        if not results:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


# 根据演员名字查询电影
def search_by_actor_neo4j(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询：根据演员名字查找参与的电影，返回所有非空属性
        query = """
        MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)
        WHERE a.actor_name = $name
        RETURN m.movie_id AS movie_id,
               m.movie_name AS movie_name,
               m.movie_runtime AS movie_runtime,
               m.version AS version
        """
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 构造查询结果，仅返回非空属性
        results = [
            {
                "movie_id": record['movie_id'],
                "movie_name": record['movie_name'],
                "movie_runtime": record['movie_runtime'],
                "version": record['version']
            }
            for record in response['records']
        ]

        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


# 查询所有电影类型
def search_every_genre_neo4j(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        formatted_name = name.strip().lower()

        # Neo4j 查询：查找匹配的电影类型
        query = """
        MATCH (g:Genre)
        WHERE toLower(g.genre_name) CONTAINS $name
        RETURN DISTINCT g.genre_name AS genre_name
        """
        # 执行查询
        response = execute_query(query, {"name": formatted_name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 构造查询结果
        result_dicts = [
            {'genre_name': record['genre_name'].strip()}
            for record in response['records']
        ]

        # 如果没有结果
        if not result_dicts:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': query_time
        })

    except Exception as err:
        # 捕获查询或连接错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_by_genre_neo4j(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询：根据类型名称查找所有关联的电影
        query = """
        MATCH (g:Genre {genre_name: $name})<-[:HAS_GENRE]-(m:Movie)
        RETURN m.movie_id AS movie_id, m.movie_name AS m.movie_name, m.movie_runtime AS movie_runtime, m.version AS version
        """
        # 执行查询
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 提取查询结果
        results = [
            {
                "movie_id": record["movie_id"],
                "movie_name": record["movie_name"],
                "movie_runtime": record["movie_runtime"],
                "version": record["version"]
            }
            for record in response["records"]
        ]

        # 如果没有找到任何电影，返回空结果
        if not results:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


# 查询演员之间的合作关系
def relation_actor_actor_neo4j(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询
        query = """
        MATCH (a1:Actor {actor_name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(a2:Actor)
        RETURN a2.actor_name AS co_name,
               COUNT(m) AS cooperation_count
        ORDER BY cooperation_count DESC
        """
        # 执行查询
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 提取查询结果
        results = [
            {
                "co_name": record["co_name"],
                "cooperation_count": record["cooperation_count"]
            }
            for record in response["records"]
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


# 查询导演与演员之间的合作关系
def relation_director_actor_neo4j(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询
        query = """
        MATCH (d:Director {director_name: $name})-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a:Actor)
        RETURN a.actor_name AS co_name,
               COUNT(m) AS cooperation_count
        ORDER BY cooperation_count DESC
        """
        # 执行查询
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 提取查询结果
        results = [
            {
                "co_name": record["co_name"],
                "cooperation_count": record["cooperation_count"]
            }
            for record in response["records"]
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


# 查询演员与导演之间的合作关系
def relation_actor_director_neo4j(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询
        query = """
        MATCH (a:Actor {actor_name: $name})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Director)
        RETURN d.director_name AS co_name,
               COUNT(m) AS cooperation_count
        ORDER BY cooperation_count DESC
        """
        # 执行查询
        response = execute_query(query, {"name": name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 提取查询结果
        results = [
            {
                "co_name": record["co_name"],
                "cooperation_count": record["cooperation_count"]
            }
            for record in response["records"]
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500



# 根据电影评分查询电影
def search_by_rate_neo4j():
    min_rating = request.args.get('min_rating')
    max_rating = request.args.get('max_rating')

    if not min_rating or not max_rating:
        return jsonify({'error': 'Min and Max rating are required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # 将查询的评分范围参数转换为 float 类型
        min_rating = float(min_rating)
        max_rating = float(max_rating)

        if min_rating > max_rating:
            return jsonify({'error': 'Min rating cannot be greater than max rating'}), 400

        # Neo4j 查询
        query = """
        MATCH (m:Movie)
        WHERE m.score >= $min_rating AND m.score <= $max_rating
        RETURN m.movie_id AS movie_id, m.movie_name AS movie_name, m.score AS rate
        ORDER BY m.score DESC
        """

        # 执行查询
        response = execute_query(query, parameters={"min_rating": min_rating, "max_rating": max_rating})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 提取查询结果
        results = [
            {
                "movie_id": record["movie_id"],
                "movie_name": record["movie_name"],
                "rate": record["rate"]
            }
            for record in response["records"]
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except ValueError:
        return jsonify({'error': 'Invalid rating values'}), 400
    except Exception as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500


# 根据电影类型查询演员组合
def search_actor_combinations_by_genre_neo4j(genre_name):
    if not genre_name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        # 记录查询开始时间
        start_time = time.time()

        # Neo4j 查询：根据类型名称查询合作过的演员组合
        query = """
        MATCH (g:Genre {genre_name: $genre_name})<-[:HAS_GENRE]-(m:Movie)<-[:ACTED_IN]-(a1:Actor),
              (m)<-[:ACTED_IN]-(a2:Actor)
        WHERE id(a1) < id(a2) // 避免重复组合
        WITH a1, a2, g, m
        OPTIONAL MATCH (r:Review)-[:REVIEWS]->(m)
        RETURN
            a1.actor_name AS actor1_name,
            a2.actor_name AS actor2_name,
            g.genre_name AS genre_name,
            COUNT(DISTINCT m) AS cooperation_count,
            COUNT(DISTINCT r) AS review_count
        ORDER BY review_count DESC
        """
        # 执行查询
        response = execute_query(query, {"genre_name": genre_name})

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 处理查询结果
        results = [
            {
                'actor1_name': record['actor1_name'],
                'actor2_name': record['actor2_name'],
                'genre_name': record['genre_name'],
                'cooperation_count': record['cooperation_count'],
                'review_count': record['review_count']
            }
            for record in response['records']
        ]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500


