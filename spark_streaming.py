from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, when, abs, from_csv
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

spark = SparkSession.builder \
    .appName("CryptoStreaming") \
    .master("spark://spark-master:7077") \
    .config("spark.streaming.stopGracefullyOnShutdown", "true") \
    .getOrCreate()

schema_str = (
    "cryptocurrency STRING, symbol STRING, date STRING, price_usd DOUBLE, market_cap DOUBLE, "
    "volume_24h DOUBLE, price_change_percent_24h DOUBLE, price_change_percent_7d DOUBLE, "
    "total_supply DOUBLE, circulating_supply DOUBLE"
)

streaming_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "crypto_stream") \
    .option("startingOffsets", "earliest") \
    .load() \
    .selectExpr("CAST(value AS STRING)") \
    .select(from_csv(col("value"), schema_str).alias("data")) \
    .select("data.*")

streaming_df = streaming_df.withColumn("date", col("date").cast("timestamp"))

anomaly_query = streaming_df \
    .filter(abs(col("price_change_percent_24h")) >= 3) \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start()

spark.streams.awaitAnyTermination()
