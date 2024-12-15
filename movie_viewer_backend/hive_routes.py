import time
from flask import request, jsonify
from hive_db import get_spark_session

# spark 会对 DataFrame API 和 Spark SQL 查询都会执行优化，两者在性能上没有太大区别

def search_by_title_hive(title):
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    try:
        spark = get_spark_session()

        # 防止由于用户输入单引号导致出现错误
        save_title = title.replace("'", "''")
        query = (f"""SELECT movie_id,movie_name,run_time AS movie_runtime,version
                     FROM movie 
                     WHERE movie_name LIKE '%{save_title}%'
                     """)

        # 方式二
        # # 构建 DataFrame API 查询
        # query_df = spark.table("movie") \
        #                 .filter(col("movie_name").like(f"%{save_title}%")) \
        #                 .select("movie_id", "movie_name", col("run_time").alias("movie_runtime"), "version")

        # 记录查询开始时间
        start_time = time.time()
        # 执行查询并获取结果
        result_df = spark.sql(query)
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        result_info = result_df.collect()
        results = [row.asDict() for row in result_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
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

    spark = get_spark_session()


    try:
        start_time = time.time()

        # 构建查询逻辑
        if query_type == "year" and year:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE year = {year}
            """

        elif query_type == "month" and year and month:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM (
                SELECT *,
                       YEAR(release_time) AS year_calc,
                       MONTH(release_time) AS month_calc
                FROM Movie
            ) movies
            WHERE year_calc = {year} AND month_calc = {month}
            """

        elif query_type == "quarter" and year and quarter:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM (
                SELECT *,
                       YEAR(release_time) AS year_calc,
                       QUARTER(release_time) AS quarter_calc
                FROM Movie
            ) movies
            WHERE year_calc = {year} AND quarter_calc = {quarter}
            """

        elif query_type == "weekday" and year and weekday and month:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM (
                SELECT *,
                       YEAR(release_time) AS year_calc,
                       MONTH(release_time) AS month_calc,
                       DAYOFWEEK(release_time) AS weekday_calc
                FROM Movie
            ) movies
            WHERE year_calc = {year} AND month_calc={month} AND weekday_calc = {weekday}
            """
        else:
            return jsonify({"error": "Invalid query parameters"}), 400

        # 执行查询
        movies_info = spark.sql(query)

        # 将 Spark DataFrame 转为字典列表
        results = [row.asDict() for row in movies_info.collect()]

        query_time = time.time() - start_time

        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f} seconds"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 关闭 SparkSession
        spark.stop()

def search_every_director_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        spark = get_spark_session()

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

        director_names_df = spark.sql(query)

        # 将结果转换为字典列表，确保每一项都是 {'director_name': value} 的形式
        director_names = [
            {'director_name': row.director_name.strip()}
            for row in director_names_df.collect()
        ]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 如果没有找到任何导演，返回空结果
        if not director_names:
            return jsonify({
                'query_time': query_time,
                'results': []
            }), 200

        # 返回查询结果和查询时间
        return jsonify({
            'query_time': query_time,
            'results': director_names
        }), 200

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def search_by_director_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        spark = get_spark_session()
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
                md.director_name = '{name}'
        """

        # 执行查询
        movies_info = spark.sql(query)

        # 收集结果
        results = [row.asDict() for row in movies_info.collect()]
        end_time = time.time()
        query_time = end_time - start_time

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def search_every_actor_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        spark = get_spark_session()

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

        actor_names_df = spark.sql(query)

        # 将结果转换为字典列表，确保每一项都是 {'actor_name': value} 的形式
        actor_names = [
            {'actor_name': row.actor_name.strip()}
            for row in actor_names_df.collect()
        ]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 如果没有找到任何演员，返回空结果
        if not actor_names:
            return jsonify({
                'query_time': query_time,
                'results': []
            }), 200

        # 返回查询结果和查询时间
        return jsonify({
            'query_time': query_time,
            'results': actor_names
        }), 200

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def search_by_actor_hive(name):
    if not name:
        return jsonify({'error': 'actor name is required'}), 400

    try:
        spark = get_spark_session()
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
                Movie_Actor md
            ON 
                m.movie_id = md.movie_id
            WHERE 
                md.actor_name = '{name}'
        """

        # 执行查询
        movies_info = spark.sql(query)

        # 收集结果
        results = [row.asDict() for row in movies_info.collect()]
        end_time = time.time()
        query_time = end_time - start_time

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def search_every_genre_hive(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        spark = get_spark_session()

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

        genre_names_df = spark.sql(query)

        # 将结果转换为字典列表，确保每一项都是 {'genre_name': value} 的形式
        genre_names = [
            {'genre_name': row.genre_name.strip()}
            for row in genre_names_df.collect()
        ]

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        # 如果没有找到任何类型，返回空结果
        if not genre_names:
            return jsonify({
                'query_time': query_time,
                'results': []
            }), 200

        # 返回查询结果和查询时间
        return jsonify({
            'query_time': query_time,
            'results': genre_names
        }), 200

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def search_by_genre_hive(name):
    if not name:
        return jsonify({'error': 'actor name is required'}), 400

    try:
        spark = get_spark_session()
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
                 Movie_Genre mg
             ON 
                 m.movie_id = mg.movie_id
             WHERE 
                 mg.genre_name = '{name}'
         """

        # 执行查询
        movies_info = spark.sql(query)

        # 收集结果
        results = [row.asDict() for row in movies_info.collect()]
        end_time = time.time()
        query_time = end_time - start_time

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def relation_actor_actor_hive(name):
    if not name:
        return jsonify({'error': 'actor name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        # 查找演员ID
        query_find_actor_id = f"""
            SELECT actor_id
            FROM Actor
            WHERE actor_name = '{name}'
            """
        actor_df = spark.sql(query_find_actor_id)

        # 如果没有找到对应的演员，则返回空结果
        if actor_df.rdd.isEmpty():
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f}"}), 200

        # 获取演员ID
        actor_id = actor_df.first().actor_id

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
        co_actors_df = spark.sql(query_find_cooperation)

        co_actors_info = co_actors_df.collect()
        end_time = time.time()
        query_time = end_time - start_time

        # 将 Spark Row 对象转换为字典列表
        results = [row.asDict() for row in co_actors_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def relation_director_actor_hive(name):
    if not name:
        return jsonify({'error': 'director name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        # 查找导演ID
        query_find_director_id = f"""
            SELECT director_id
            FROM Director
            WHERE director_name = '{name}'
            """
        director_df = spark.sql(query_find_director_id)

        if director_df.rdd.isEmpty():
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f}"}), 200

        # 获取演员ID
        director_id = director_df.first().director_id

        # 查找合作关系及合作次数
        query_find_cooperation = f"""
            WITH CooperatedActors AS (
                SELECT actor_id AS co_actor_id, cooperation_count
                FROM Actor_Director
                WHERE director_id = {director_id}
            )
            SELECT a.actor_name AS co_name, SUM(c.cooperation_count) AS cooperation_count
            FROM Actor a
            JOIN CooperatedActors c ON a.actor_id = c.co_actor_id
        """
        co_actors_df = spark.sql(query_find_cooperation)

        co_actors_info = co_actors_df.collect()
        end_time = time.time()
        query_time = end_time - start_time

        # 将 Spark Row 对象转换为字典列表
        results = [row.asDict() for row in co_actors_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500

def relation_actor_director_hive(name):
    if not name:
        return jsonify({'error': 'actor name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        # 查找演员ID
        query_find_actor_id = f"""
            SELECT actor_id
            FROM Actor
            WHERE actor_name = '{name}'
            """
        actor_df = spark.sql(query_find_actor_id)

        if actor_df.rdd.isEmpty():
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f}"}), 200

        # 获取演员ID
        actor_id = actor_df.first().director_id

        # 查找合作关系及合作次数
        query_find_cooperation = f"""
            WITH CooperatedDirectors AS (
                SELECT director_id AS co_director_id, cooperation_count
                FROM Actor_Director
                WHERE actor_id = {actor_id}
            )
            SELECT d.director_name AS co_name, SUM(c.cooperation_count) AS cooperation_count
            FROM Director d
            JOIN CooperatedDirectors c ON d.director_id = c.co_director_id
        """
        co_directors_df = spark.sql(query_find_cooperation)

        co_directors_info = co_directors_df.collect()
        end_time = time.time()
        query_time = end_time - start_time

        # 将 Spark Row 对象转换为字典列表
        results = [row.asDict() for row in co_directors_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': f"{query_time:.6f}"
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

        spark = get_spark_session()
        start_time = time.time()

        query = f"""
            SELECT movie_id, movie_name, average_score AS rate
            FROM Movie
            WHERE average_score BETWEEN '{min_rating}' AND '{max_rating}'
            ORDER BY average_score DESC
        """
        movies_df = spark.sql(query)
        movies_info = movies_df.collect()

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        results = [row.asDict() for row in movies_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
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
        spark = get_spark_session()
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
            WHERE f.genre_name = '{genre_name}'
            ORDER BY f.review_count DESC
        """

        start_time = time.time()
        cooperation_df = spark.sql(query)
        cooperation_info = cooperation_df.collect()
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        results = [row.asDict() for row in cooperation_info]

        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500
