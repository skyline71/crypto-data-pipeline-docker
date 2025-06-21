from pyspark.sql import SparkSession
from pyspark.sql.functions import col, abs

spark = SparkSession.builder \
    .appName("CorrelationAnalysis") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.hive.metastore.uris", "thrift://hive-metastore:9083") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.sql("SELECT volume_24h, price_change_percent_24h FROM crypto_averages WHERE segment = 'volatile'")

correlation = df.stat.corr("volume_24h", "price_change_percent_24h", method="pearson")

print(f"Pearson correlation between volume_24h and abs(price_change_percent_24h): {correlation:.2f}")

anomaly_df = df.filter(abs(col("price_change_percent_24h")) >= 3) \
    .agg({"volume_24h": "avg"}) \
    .withColumnRenamed("avg(volume_24h)", "avg_volume_anomalies")

normal_df = df.filter(abs(col("price_change_percent_24h")) < 3) \
    .agg({"volume_24h": "avg"}) \
    .withColumnRenamed("avg(volume_24h)", "avg_volume_normal")

anomaly_df.show()
normal_df.show()

anomaly_df.write.mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/anomaly_volume")
normal_df.write.mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/normal_volume")

spark.stop()
