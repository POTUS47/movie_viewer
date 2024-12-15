
from flask import Flask
from flask_cors import CORS
from hive_db import close_hive_connection
from hive_routes import *


app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求

# 将路由函数注册到应用中
app.add_url_rule('/search_by_title_hive/<string:title>', view_func=search_by_title_hive, methods=['GET'])
app.add_url_rule('/search_by_time_hive/<string:title>', view_func=search_by_time_hive, methods=['GET'])
app.add_url_rule('/search_every_director_hive/<string:name>', view_func=search_every_director_hive, methods=['GET'])
app.add_url_rule('/search_by_director_hive/<string:name>', view_func=search_by_director_hive, methods=['GET'])
app.add_url_rule('/search_every_actor_hive/<string:name>', view_func=search_every_actor_hive, methods=['GET'])
app.add_url_rule('/search_by_actor_hive/<string:name>', view_func=search_by_actor_hive, methods=['GET'])
app.add_url_rule('/search_every_genre_hive/<string:name>', view_func=search_every_genre_hive, methods=['GET'])
app.add_url_rule('/search_by_genre_hive/<string:name>', view_func=search_by_genre_hive, methods=['GET'])
app.add_url_rule('/relation_actor_actor_hive/<string:name>', view_func=relation_actor_actor_hive, methods=['GET'])
app.add_url_rule('/relation_actor_director_hive/<string:name>', view_func=relation_actor_director_hive, methods=['GET'])
app.add_url_rule('/relation_director_actor_hive/<string:name>', view_func=relation_director_actor_hive, methods=['GET'])
app.add_url_rule('/search_by_rate_hive', view_func=search_by_rate_hive, methods=['GET'])
app.add_url_rule('/search_actor_combinations_by_genre_hive/<string:genre_name>', view_func=search_actor_combinations_by_genre_hive, methods=['GET'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)