from flask import request, jsonify
from db_utils import get_db_connection
import time
import mysql

def search_by_title(title):
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 查询语句
        query = "SELECT * FROM Movie_Dimension WHERE movie_name LIKE %s"
        cursor.execute(query, (f'%{title}%',))
        
        results = cursor.fetchall()
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def get_movie_versions(movie_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询合并记录
        merge_query = """
        SELECT original_movie_id 
        FROM merge_record 
        WHERE merged_movie_id = %s
        """
        cursor.execute(merge_query, (movie_id,))
        merged_records = cursor.fetchall()
        print(merged_records)

        new_record = {'original_movie_id': movie_id}
        merged_records.append(new_record)
        print(merged_records)

        # 获取所有原始电影信息
        original_movies = []
        for record in merged_records:
            original_id = record['original_movie_id']
            original_query = "SELECT * FROM TESTDATA WHERE movie_id = %s"
            cursor.execute(original_query, (original_id,))
            original_movie = cursor.fetchone()
            if original_movie:
                original_movies.append(original_movie)

        cursor.close()
        conn.close()

        return jsonify({
            'merged_movie_id': movie_id,
            'original_movies': original_movies
        })

    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_by_time():
    query_type = request.args.get('type')
    year = request.args.get('year')
    month = request.args.get('month')
    quarter = request.args.get('quarter')
    weekday = request.args.get('weekday')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 记录查询开始时间
    start_time = time.time()

    if query_type == 'year':
        sql = """
            SELECT m.movie_name,m.release_date,m.average_score
            FROM Movie_Fact m
            JOIN Time_Dimension t ON m.release_date = t.release_date
            WHERE t.year = %s
        """
        cursor.execute(sql, (year,))
    elif query_type == 'month':
        sql = """
            SELECT m.movie_name,m.release_date,m.average_score
            FROM Movie_Fact m
            JOIN Time_Dimension t ON m.release_date = t.release_date
            WHERE t.year = %s AND t.month = %s
        """
        cursor.execute(sql, (year, month))
    elif query_type == 'quarter':
        sql = """
            SELECT m.movie_name,m.release_date,m.average_score
            FROM Movie_Fact m
            JOIN Time_Dimension t ON m.release_date = t.release_date
            WHERE t.year = %s AND t.quarter = %s
        """
        cursor.execute(sql, (year, quarter))
    elif query_type == 'weekday':
        sql = """
            SELECT m.movie_name,m.release_date,m.average_score
            FROM Movie_Fact m
            JOIN Time_Dimension t ON m.release_date = t.release_date
            WHERE t.year = %s AND t.month = %s AND t.day_of_week = %s
        """
        cursor.execute(sql, (year,month,weekday))

    # 记录查询结束时间
    end_time = time.time()
    query_time = end_time - start_time

    results = cursor.fetchall()
    print(results)
    cursor.close()
    conn.close()

    return jsonify({
        'results': results,
        'query_time': f"{query_time:.6f}"  # 示例查询时间
    })



def search_every_director(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT DISTINCT director_name 
        FROM Movie_Director_Fact 
        WHERE director_name = %s
           OR director_name LIKE CONCAT(%s, ' %%')
           OR director_name LIKE CONCAT('%% ', %s)
        """
        cursor.execute(director_query, (name, name, name))
        movie_ids = cursor.fetchall()
        print(movie_ids)

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': query_time}), 200

        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': movie_ids,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_by_director(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT movie_id 
        FROM Movie_Director_Fact 
        WHERE director_name = %s
        """
        cursor.execute(director_query, (name,))
        movie_ids = cursor.fetchall()
        print(movie_ids)
        
        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 提取所有的 movie_id
        movie_ids_list = [movie['movie_id'] for movie in movie_ids]
        
        # 如果没有找到任何电影ID，直接返回空结果
        if not movie_ids_list:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 第二步：根据 movie_id 在 Movie_Dimension 中得到关于电影的其他信息
        placeholders = ', '.join(['%s'] * len(movie_ids_list))  # 创建占位符字符串
        movie_query = f"""
        SELECT * 
        FROM Movie_Dimension 
        WHERE movie_id IN ({placeholders})
        """
        
        cursor.execute(movie_query, movie_ids_list)  # 传递参数列表
        results = cursor.fetchall()
       
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    


def search_every_actor(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT DISTINCT actor_name 
        FROM Movie_Actor_Fact 
        WHERE actor_name = %s
           OR actor_name LIKE CONCAT(%s, ' %%')
           OR actor_name LIKE CONCAT('%% ', %s)
        """
        cursor.execute(director_query, (name, name, name))
        movie_ids = cursor.fetchall()
        print(movie_ids)

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': query_time}), 200

        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': movie_ids,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_by_actor(name):
    if not name:
        return jsonify({'error': 'Actor name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT movie_id 
        FROM Movie_Actor_Fact 
        WHERE actor_name = %s
        """
        cursor.execute(director_query, (name,))
        movie_ids = cursor.fetchall()
        print(movie_ids)
        
        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 提取所有的 movie_id
        movie_ids_list = [movie['movie_id'] for movie in movie_ids]
        
        # 如果没有找到任何电影ID，直接返回空结果
        if not movie_ids_list:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 第二步：根据 movie_id 在 Movie_Dimension 中得到关于电影的其他信息
        placeholders = ', '.join(['%s'] * len(movie_ids_list))  # 创建占位符字符串
        movie_query = f"""
        SELECT * 
        FROM Movie_Dimension 
        WHERE movie_id IN ({placeholders})
        """
        
        cursor.execute(movie_query, movie_ids_list)  # 传递参数列表
        results = cursor.fetchall()
       
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500


def search_every_genre(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT DISTINCT genre_name 
        FROM Genre_Dimension 
        WHERE genre_name LIKE %s
        """
        cursor.execute(director_query, (f'%{name}%',))
        movie_ids = cursor.fetchall()
        print(movie_ids)

        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time

        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': query_time}), 200

        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': movie_ids,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_by_genre(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT movie_id 
        FROM Movie_Genre_Fact 
        WHERE genre_name = %s
        """
        cursor.execute(director_query, (name,))
        movie_ids = cursor.fetchall()
        print(movie_ids)
        
        if not movie_ids:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 提取所有的 movie_id
        movie_ids_list = [movie['movie_id'] for movie in movie_ids]
        
        # 如果没有找到任何电影ID，直接返回空结果
        if not movie_ids_list:
            cursor.close()
            conn.close()
            return jsonify({'results': [], 'query_time': 0}), 200
        
        # 第二步：根据 movie_id 在 Movie_Dimension 中得到关于电影的其他信息
        placeholders = ', '.join(['%s'] * len(movie_ids_list))  # 创建占位符字符串
        movie_query = f"""
        SELECT * 
        FROM Movie_Dimension 
        WHERE movie_id IN ({placeholders})
        """
        
        cursor.execute(movie_query, movie_ids_list)  # 传递参数列表
        results = cursor.fetchall()
       
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def relation_actor_actor(name):
    if not name:
        return jsonify({'error': 'Genre name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT a.actor_name AS co_name, f.cooperation_count
        FROM Actor_Actor_Cooperation_Fact f
        JOIN Actor_Dimension a ON a.actor_id = CASE 
            WHEN f.actor1_id = (SELECT actor_id FROM Actor_Dimension WHERE actor_name = %s) THEN f.actor2_id 
            ELSE f.actor1_id 
        END
        WHERE f.actor1_id = (SELECT actor_id FROM Actor_Dimension WHERE actor_name = %s)
            OR f.actor2_id = (SELECT actor_id FROM Actor_Dimension WHERE actor_name = %s)
        ORDER BY f.cooperation_count DESC;
        """
        cursor.execute(director_query, (name,name,name))
        results = cursor.fetchall()
       
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def relation_director_actor(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT a.actor_name AS co_name, f.cooperation_count
        FROM Movie_Director_Actor_Cooperation_Fact f
        JOIN Director_Dimension d ON d.director_id = f.director_id
        JOIN Actor_Dimension a ON a.actor_id = f.actor_id
        WHERE d.director_name = %s
        ORDER BY f.cooperation_count DESC;
        """
        cursor.execute(director_query, (name,))
        results = cursor.fetchall()
       
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    
def relation_actor_director(name):
    if not name:
        return jsonify({'error': 'Director name is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        # 第一步：从 Movie_Director_Fact 表中根据导演名字查到 movie_id
        director_query = """
        SELECT d.director_name AS co_name, f.cooperation_count
        FROM Movie_Director_Actor_Cooperation_Fact f
        JOIN Director_Dimension d ON d.director_id = f.director_id
        JOIN Actor_Dimension a ON a.actor_id = f.actor_id
        WHERE a.actor_name = %s
        ORDER BY f.cooperation_count DESC;
        """
        cursor.execute(director_query, (name,))
        results = cursor.fetchall()
       
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_by_rate():
    min_rating = request.args.get('min_rating')
    max_rating = request.args.get('max_rating')

    if not min_rating or not max_rating:
        return jsonify({'error': 'Min and Max rating are required'}), 400

    try:
        min_rating = float(min_rating)
        max_rating = float(max_rating)
        
        if min_rating > max_rating:
            return jsonify({'error': 'Min rating cannot be greater than max rating'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 记录查询开始时间
        start_time = time.time()
        
        query = """
        SELECT movie_id, movie_name, average_score AS rate
        FROM Movie_Fact
        WHERE average_score BETWEEN %s AND %s
        ORDER BY average_score DESC
        """
        
        cursor.execute(query, (min_rating, max_rating))
        results = cursor.fetchall()
        
        # 记录查询结束时间
        end_time = time.time()
        query_time = end_time - start_time
        
        cursor.close()
        conn.close()
        
        # 返回查询结果和查询时间
        return jsonify({
            'results': results,
            'query_time': query_time
        })
    
    except ValueError:
        return jsonify({'error': 'Invalid rating values'}), 400
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500
    

def search_actor_combinations_by_genre(genre_name):
    if not genre_name:
        return jsonify({'error': 'Genre name is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            a1.actor_name AS actor1_name,
            a2.actor_name AS actor2_name,
            f.genre_name,
            f.cooperation_count,
            f.review_count
        FROM Actor_Actor_Genre_Cooperation_Fact f
        JOIN Actor_Dimension a1 ON a1.actor_id = f.actor1_id
        JOIN Actor_Dimension a2 ON a2.actor_id = f.actor2_id
        WHERE f.genre_name = %s
        ORDER BY f.review_count DESC
        """
        
        cursor.execute(query, (genre_name,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()
        
        return jsonify({
            'results': results
        })

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500