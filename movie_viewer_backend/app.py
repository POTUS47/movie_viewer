from flask import Flask
from flask_cors import CORS
from routes import *
from neo4j_routes import *


app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求

# 将路由函数注册到应用中
app.add_url_rule('/search_by_title/<string:title>', view_func=search_by_title, methods=['GET'])
app.add_url_rule('/movie_versions/<string:movie_id>', view_func=get_movie_versions, methods=['GET'])
app.add_url_rule('/search_by_time/',view_func=search_by_time,methods=['GET'])
app.add_url_rule('/search_every_director/<string:name>', view_func=search_every_director, methods=['GET'])
app.add_url_rule('/search_by_director/<string:name>', view_func=search_by_director, methods=['GET'])
app.add_url_rule('/search_every_actor/<string:name>', view_func=search_every_actor, methods=['GET'])
app.add_url_rule('/search_by_actor/<string:name>', view_func=search_by_actor, methods=['GET'])
app.add_url_rule('/search_every_genre/<string:name>', view_func=search_every_genre, methods=['GET'])
app.add_url_rule('/search_by_genre/<string:name>', view_func=search_by_genre, methods=['GET'])
app.add_url_rule('/relation_actor_actor/<string:name>', view_func=relation_actor_actor, methods=['GET'])
app.add_url_rule('/relation_actor_director/<string:name>', view_func=relation_actor_director, methods=['GET'])
app.add_url_rule('/relation_director_actor/<string:name>', view_func=relation_director_actor, methods=['GET'])
app.add_url_rule('/get_movies_by_score/', view_func=search_by_rate, methods=['GET'])
app.add_url_rule('/search_actor_combinations_by_genre/<string:genre_name>', view_func=search_actor_combinations_by_genre, methods=['GET'])
app.add_url_rule('/search_by_rate/',view_func=get_movies_by_score,methods=['GET'])


# 注册 Neo4j 查询路由
app.add_url_rule('/search_by_title_neo4j/<string:movie_name>', view_func=search_by_title_neo4j, methods=['GET'])




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)