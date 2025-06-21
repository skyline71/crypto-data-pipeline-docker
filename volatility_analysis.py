from pyspark.sql import SparkSession
from pyspark.sql.functions import col, abs, avg

spark = SparkSession.builder \
    .appName("VolatilityAnalysis") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.hive.metastore.uris", "thrift://hive-metastore:9083") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.sql("SELECT segment, price_change_percent_24h FROM crypto_averages")

volatility_df = df.groupBy("segment") \
    .agg(avg(abs(col("price_change_percent_24h"))).alias("avg_abs_price_change_percent")) \
    .orderBy("avg_abs_price_change_percent")

volatility_df.show()

volatility_df.write.mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/volatility_results")

spark.stop()
