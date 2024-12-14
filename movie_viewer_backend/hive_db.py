from pyspark.sql import SparkSession


class SparkSessionSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls._create_spark_session()
            # 设置默认数据库为 amazon2
            cls._instance.sql("USE amazon2")
        return cls._instance

    @classmethod
    def _create_spark_session(cls):
        return SparkSession.builder \
            .enableHiveSupport() \
            .appName("Amazon2 Analysis") \
            .getOrCreate()


# 提供一个简单的接口函数
def get_spark_session():
    """获取并配置好默认数据库的Spark会话"""
    return SparkSessionSingleton.get_instance()


# 提供一个关闭 SparkSession 的方法
def close_spark_session():
    if SparkSessionSingleton._instance:
        SparkSessionSingleton._instance.stop()
        SparkSessionSingleton._instance = None


###################################### 下面是成功连接hive的例子
# from pyspark.sql import SparkSession
#
# # 创建或获取一个带有Hive支持的SparkSession
# spark = SparkSession.builder \
#     .enableHiveSupport() \
#     .getOrCreate()
#
# # 使用SQL语句切换到amazon数据库
# spark.sql("USE amazon2")
#
# # 显示amazon数据库中的所有表
# # tables_df = spark.catalog.listTables("amazon")
# print("Tables in the 'amazon' database:")
# # tables_df.show()
#
# # 或者使用SQL查询来显示所有表
# spark.sql("SHOW TABLES").show()
