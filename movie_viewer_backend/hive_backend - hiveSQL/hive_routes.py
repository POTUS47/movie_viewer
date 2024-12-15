import time
from flask import request, jsonify
from hive_db import get_hive_connection

# spark 会对 DataFrame API 和 Spark SQL 查询都会执行优化，两者在性能上没有太大区别

def search_by_title_hive(title):#ok
    print("Starting search_by_title_hive...")
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_title = title.replace("'", "''")
        query = (f"""SELECT movie_id, movie_name, run_time AS movie_runtime, version
                     FROM movie 
                     WHERE movie_name LIKE '%{save_title}%'""")
        print(f"Executing query: {query}")
        # 记录查询开始时间
        start_time = time.time()

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


def search_by_time_hive():
    query_type = request.args.get('type')
    year = request.args.get('year')
    month = request.args.get('month')
    quarter = request.args.get('quarter')
    weekday = request.args.get('weekday')

    if not all([query_type, year]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        start_time = time.time()

        # 构建查询逻辑
        if query_type == "year" and year:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE YEAR(release_time) = {year}
            """

        elif query_type == "month" and year and month:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE YEAR(release_time) = {year} AND MONTH(release_time) = {month}
            """

        elif query_type == "quarter" and year and quarter:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE YEAR(release_time) = {year} AND QUARTER(release_time) = {quarter}
            """

        elif query_type == "weekday" and year and weekday and month:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE YEAR(release_time) = {year} AND MONTH(release_time) = {month} AND DAYOFWEEK(release_time) = {weekday}
            """
        else:
            return jsonify({"error": "Invalid query parameters"}), 400

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({"error": str(err)}), 500


def search_every_director_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT DISTINCT director_name
            FROM Director
            WHERE director_name = '{save_name}'
               OR director_name LIKE '{save_name} %'
               OR director_name LIKE '% {save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 如果没有找到任何导演，返回空结果
        if not results:
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': [row['director_name'] for row in result_dicts],  # 使用字典的列名访问
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500



def search_by_director_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT 
                m.movie_id AS movie_id,
                m.movie_name AS movie_name,
                m.run_time AS movie_runtime,
                m.version AS version
            FROM 
                Movie m
            JOIN 
                Movie_Director md
            ON 
                m.movie_id = md.movie_id
            WHERE 
                md.director_name = '{save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_every_actor_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT DISTINCT actor_name
            FROM Actor
            WHERE actor_name = '{save_name}'
               OR actor_name LIKE '{save_name} %'
               OR actor_name LIKE '% {save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 如果没有找到任何演员，返回空结果
        if not results:
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': [row['actor_name'] for row in result_dicts],  # 使用字典的列名访问
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_by_actor_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT 
                m.movie_id AS movie_id,
                m.movie_name AS movie_name,
                m.run_time AS movie_runtime,
                m.version AS version
            FROM 
                Movie m
            JOIN 
                Movie_Actor ma
            ON 
                m.movie_id = ma.movie_id
            WHERE 
                ma.actor_name = '{save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_every_genre_hive(name):
    if not name:
        return jsonify({'error': 'genre name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT DISTINCT genre_name
            FROM Movie_Genre
            WHERE genre_name = '{save_name}'
               OR genre_name LIKE '{save_name} %'
               OR genre_name LIKE '% {save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 如果没有找到任何演员，返回空结果
        if not results:
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': [row['genre_name'] for row in result_dicts],  # 使用字典的列名访问
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_by_genre_hive(name):
    if not name:
        return jsonify({'error': 'genre name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT 
                m.movie_id AS movie_id,
                m.movie_name AS movie_name,
                m.run_time AS movie_runtime,
                m.version AS version
            FROM 
                Movie m
            JOIN 
                Movie_genre ma
            ON 
                m.movie_id = ma.movie_id
            WHERE 
                ma.genre_name = '{save_name}'
        """

        # 执行查询并获取结果
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def relation_actor_actor_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        # 查找演员ID
        query_find_actor_id = f"""
            SELECT actor_id
            FROM Actor
            WHERE actor_name = '{save_name}'
        """
        cursor.execute(query_find_actor_id)
        actor_result = cursor.fetchone()

        # 如果没有找到对应的演员，则返回空结果
        if not actor_result:
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 获取演员ID
        actor_id = actor_result[0]

        # 查找合作关系及合作次数（两种情况：actor1 或 actor2）
        query_find_cooperation = f"""
        WITH CooperatedActors AS (
            SELECT actor2_id AS co_actor_id, cooperation_count
            FROM Actor_Actor
            WHERE actor1_id = {actor_id}
            UNION ALL
            SELECT actor1_id AS co_actor_id, cooperation_count
            FROM Actor_Actor
            WHERE actor2_id = {actor_id}
        )
        SELECT a.actor_name AS co_name, SUM(c.cooperation_count) AS cooperation_count
        FROM Actor a
        JOIN CooperatedActors c ON a.actor_id = c.co_actor_id
        GROUP BY a.actor_name
        """
        cursor.execute(query_find_cooperation)
        co_actors_results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in co_actors_results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def relation_director_actor_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        # 查找导演ID
        query_find_director_id = f"""
            SELECT director_id
            FROM Director
            WHERE director_name = '{save_name}'
        """
        cursor.execute(query_find_director_id)
        director_result = cursor.fetchone()

        # 如果没有找到对应的导演，则返回空结果
        if not director_result:
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 获取导演ID
        director_id = director_result[0]

        # 查找合作关系及合作次数
        query_find_cooperation = f"""
            WITH CooperatedActors AS (
                SELECT actor_id AS co_actor_id, COUNT(*) AS cooperation_count
                FROM Movie_Director md
                JOIN Movie_Actor ma ON md.movie_id = ma.movie_id
                WHERE md.director_id = {director_id}
                GROUP BY actor_id
            )
            SELECT a.actor_name AS co_name, c.cooperation_count
            FROM Actor a
            JOIN CooperatedActors c ON a.actor_id = c.co_actor_id
        """
        cursor.execute(query_find_cooperation)
        co_actors_results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in co_actors_results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def relation_actor_director_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_name = name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        # 查找演员ID
        query_find_actor_id = f"""
            SELECT actor_id
            FROM Actor
            WHERE actor_name = '{save_name}'
        """
        cursor.execute(query_find_actor_id)
        actor_result = cursor.fetchone()

        # 如果没有找到对应的演员，则返回空结果
        if not actor_result:
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f} seconds"}), 200

        # 获取演员ID
        actor_id = actor_result[0]

        # 查找合作关系及合作次数
        query_find_cooperation = f"""
            WITH CooperatedDirectors AS (
                SELECT director_id AS co_director_id, COUNT(*) AS cooperation_count
                FROM Movie_Actor ma
                JOIN Movie_Director md ON ma.movie_id = md.movie_id
                WHERE ma.actor_id = {actor_id}
                GROUP BY director_id
            )
            SELECT d.director_name AS co_name, c.cooperation_count
            FROM Director d
            JOIN CooperatedDirectors c ON d.director_id = c.co_director_id
        """
        cursor.execute(query_find_cooperation)
        co_directors_results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in co_directors_results]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_by_rate_hive():
    min_rating = request.args.get('min_rating')
    max_rating = request.args.get('max_rating')

    if not min_rating or not max_rating:
        return jsonify({'error': 'Min and Max rating are required'}), 400

    try:
        min_rating = float(min_rating)
        max_rating = float(max_rating)

        if min_rating > max_rating:
            return jsonify({'error': 'Min rating cannot be greater than max rating'}), 400

        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT movie_id, movie_name, average_score AS rate
            FROM Movie
            WHERE average_score BETWEEN {min_rating} AND {max_rating}
            ORDER BY average_score DESC
        """
        cursor.execute(query)
        movies_info = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in movies_info]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except ValueError:
        return jsonify({'error': 'Invalid rating values'}), 400
    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


def search_actor_combinations_by_genre_hive(genre_name):
    if not genre_name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        # 获取Hive连接
        conn = get_hive_connection()
        cursor = conn.cursor()

        # 防止单引号导致SQL错误
        save_genre_name = genre_name.replace("'", "''")

        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT
                a1.actor_name AS actor1_name,
                a2.actor_name AS actor2_name,
                f.genre_name,
                f.cooperation_count,
                f.review_count
            FROM New_Actor_Actor_Genre f
            JOIN Actor a1 ON a1.actor_id = f.actor1_id
            JOIN Actor a2 ON a2.actor_id = f.actor2_id
            WHERE f.genre_name = '{save_genre_name}'
            ORDER BY f.review_count DESC
        """

        cursor.execute(query)
        cooperation_info = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in cooperation_info]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,
            'query_time': f"{query_time:.6f} seconds"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500