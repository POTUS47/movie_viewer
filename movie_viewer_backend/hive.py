from flask import Flask, jsonify, request
from pyspark.sql import SparkSession
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)
spark = None

def get_spark_session():
    global spark
    if not spark:
        spark = SparkSession.builder \
            .appName("FlaskApp") \
            .master("local") \
            .enableHiveSupport() \
            .getOrCreate()
        spark.sql("use default")
    return spark

@app.teardown_appcontext
def close_spark_session(exception=None):
    global spark
    if spark:
        spark.stop()
        spark = None

@app.route('/search_by_title_hive/<string:title>', methods=['GET'])
def search_by_title_hive(title):
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    try:
        spark = get_spark_session()
        # 防止单引号导致错误
        save_title = title.replace("'", "''")
        query = (f"""SELECT movie_id,movie_name,run_time AS movie_runtime,version
                     FROM movie 
                     WHERE movie_name LIKE '%{save_title}%'
                     """)
        # 记录查询开始时间
        start_time = time.time()
        # 执行查询并获取结果
        result_df = spark.sql(query)

        result_info = result_df.collect()
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        results = [row.asDict() for row in result_info]

        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })

    except Exception as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


@app.route('/search_by_time_hive', methods=['GET'])
def search_by_time_hive():
    query_type = request.args.get('type')
    year = request.args.get('year')
    month = request.args.get('month')
    quarter = request.args.get('quarter')
    weekday = request.args.get('weekday')

    if not all([query_type, year]):
        return jsonify({"error": "Missing required parameters"}), 400

    
    try:
        spark = get_spark_session()
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
            FROM Movie
            WHERE year = {year} AND month = {month}
            """

        elif query_type == "quarter" and year and quarter:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE year = {year} AND quarter = {quarter}
            """

        elif query_type == "weekday" and year and weekday and month:
            query = f"""
            SELECT 
                movie_name,
                release_time AS release_date,
                average_score
            FROM Movie
            WHERE year = {year} AND month = {month} AND day_of_week = {weekday}
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
            'query_time': f"{query_time:.6f}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 关闭 SparkSession
        spark.stop()


@app.route('/search_every_director_hive/<string:name>', methods=['GET'])
def search_every_director_hive(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()
        query = f"""
            SELECT DISTINCT director_name
            FROM Director
            WHERE director_name = '{name}'
               OR director_name LIKE '{name} %'
               OR director_name LIKE '% {name}'
        """

        director_names_df = spark.sql(query)
        director_names = director_names_df.collect()

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        result_dicts = [
            {'director_name': row['director_name'].strip()}
            for row in director_names
        ]

        if not director_names:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,  # 使用字典的列名访问
            'query_time': query_time
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


@app.route('/search_by_director_hive/<string:name>', methods=['GET'])
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


@app.route('/search_every_actor_hive/<string:name>', methods=['GET'])
def search_every_actor_hive(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        query = f"""
            SELECT DISTINCT actor_name
            FROM Actor
            WHERE actor_name = '{name}'
               OR actor_name LIKE '{name} %'
               OR actor_name LIKE '% {name}'
        """

        actor_names_df = spark.sql(query)
        actor_names = actor_names_df.collect()

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        result_dicts = [
            {'actor_name': row['actor_name'].strip()}
            for row in actor_names
        ]
        if not actor_names:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results': result_dicts,  # 使用字典的列名访问
            'query_time': query_time
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


@app.route('/search_by_actor_hive/<string:name>', methods=['GET'])
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


@app.route('/search_every_genre_hive/<string:name>', methods=['GET'])
def search_every_genre_hive(name):
    if not name:
        return jsonify({'error': 'genre name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        query = f"""
             SELECT DISTINCT genre_name
             FROM Movie_Genre
             WHERE genre_name = '{name}'
                OR genre_name LIKE '{name} %'
                OR genre_name LIKE '% {name}'
         """

        genre_names_df = spark.sql(query)
        genre_names = genre_names_df.collect()

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        result_dicts = [
            {'genre_name': row['genre_name'].strip()}
            for row in genre_names
        ]
        if not genre_names:
            return jsonify({'results': [], 'query_time': query_time}), 200

        # 返回查询结果和查询时间
        return jsonify({
            'results':result_dicts,  # 使用字典的列名访问
            'query_time': query_time
        })

    except Exception as err:
        # 捕获其他数据库连接或查询错误
        print(f"Error: {err}")
        return jsonify({'error': 'Database query failed'}), 500


@app.route('/search_by_genre_hive/<string:name>', methods=['GET'])
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


@app.route('/relation_actor_actor_hive/<string:name>', methods=['GET'])
def relation_actor_actor_hive(name):
    if not name:
        return jsonify({'error': 'actor name is required'}), 400

    try:
        spark = get_spark_session()
        # 记录查询开始时间
        start_time = time.time()

        # 查找合作关系及合作次数（两种情况：actor1 或 actor2）
        query_find_cooperation = f"""
            WITH CooperatedActors AS (
                        SELECT actor2_name AS co_name, cooperation_count
                        FROM Actor_Actor
                        WHERE actor1_name = '{name}'
                        UNION ALL
                        SELECT actor1_name AS co_name, cooperation_count
                        FROM Actor_Actor
                        WHERE actor2_name = '{name}'
                    )
                    SELECT co_name, cooperation_count
                    FROM CooperatedActors
                    ORDER BY cooperation_count DESC
            """

        co_actors_df = spark.sql(query_find_cooperation)

        # 如果没有找到任何合作记录，则返回空结果
        if co_actors_df.rdd.isEmpty():
            end_time = time.time()
            query_time = end_time - start_time
            return jsonify({'results': [], 'query_time': f"{query_time:.6f}"}), 200

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


@app.route('/relation_actor_director_hive/<string:name>', methods=['GET'])
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


@app.route('/relation_director_actor_hive/<string:name>', methods=['GET'])
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


@app.route('/search_by_rate_hive', methods=['GET'])
def search_by_rate_hive():
    min_rating = request.args.get('min_rating')
    max_rating = request.args.get('max_rating')

    if not min_rating or not max_rating:
        return jsonify({'error': 'Min and Max rating are required'}), 400

    try:
        spark = get_spark_session()
        min_rating = float(min_rating)
        max_rating = float(max_rating)

        if min_rating > max_rating:
            return jsonify({'error': 'Min rating cannot be greater than max rating'}), 400

        
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


@app.route('/search_actor_combinations_by_genre_hive/<string:genre_name>', methods=['GET'])
def search_actor_combinations_by_genre_hive(genre_name):
    if not genre_name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        spark = get_spark_session()
        query = f"""
            SELECT
                actor1_name,
                actor2_name,
                genre_name,
                cooperation_count,
                review_count
            FROM Actor_Actor_Genre 
            WHERE genre_name = '{genre_name}'
            ORDER BY review_count DESC
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
