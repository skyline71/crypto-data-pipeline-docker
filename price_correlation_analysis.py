from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder \
    .appName("PriceCorrelationAnalysis") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.hive.metastore.uris", "thrift://hive-metastore:9083") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.sql("SELECT cryptocurrency, date, price_usd FROM crypto_averages WHERE cryptocurrency IN ('Bitcoin', 'Ethereum')")

bitcoin_df = df.filter(col("cryptocurrency") == "Bitcoin").select("date", col("price_usd").alias("bitcoin_price"))
ethereum_df = df.filter(col("cryptocurrency") == "Ethereum").select("date", col("price_usd").alias("ethereum_price"))

joined_df = bitcoin_df.join(ethereum_df, "date", "inner")

correlation = joined_df.stat.corr("bitcoin_price", "ethereum_price", method="pearson")

print(f"Pearson correlation between Bitcoin and Ethereum prices: {correlation:.2f}")

joined_df.select("bitcoin_price", "ethereum_price").write.mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/price_correlation")

spark.stop()
