from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, lag, when, count
from pyspark.sql.window import Window
import logging

# Настройка логирования с записью в файл
log_file = "/data/batch_processing.log"

# Настройка обработчиков для консоли и файла
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Обработчик для файла
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Обработчик для консоли
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Добавление обработчиков к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

spark = SparkSession.builder \
    .appName("CryptoBatchProcessing") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.hive.metastore.uris", "thrift://hive-metastore:9083") \
    .config("spark.hive.metastore.warehouse.dir", "hdfs://namenode:9000/user/hive/warehouse") \
    .config("spark.driver.extraClassPath", "/opt/bitnami/spark/jars/*") \
    .config("spark.executor.extraClassPath", "/opt/bitnami/spark/jars/*") \
    .config("spark.executor.memory", "2g") \
    .config("spark.executor.cores", "2") \
    .config("spark.sql.shuffle.partitions", "10") \
    .enableHiveSupport() \
    .getOrCreate()

try:
    logger.info("Starting batch processing")

    df = spark.sql("SELECT * FROM crypto_prices")
    df = df.withColumn("date", col("date").cast("timestamp"))
    logger.info("Data loaded from Hive")

    df_cleaned = df.dropDuplicates(["cryptocurrency", "symbol", "date"]) \
                   .na.drop(subset=["price_usd", "market_cap", "volume_24h"]) \
                   .filter((col("price_usd") > 0) & (col("market_cap") >= 0))
    logger.info(f"Cleaned data: {df_cleaned.count()} rows")

    df_cleaned.select("cryptocurrency", "symbol", "date", "price_usd", "market_cap", "volume_24h", "circulating_supply") \
              .show(10, truncate=False)

    window_spec = Window.partitionBy("cryptocurrency").orderBy("date")
    df_cleaned = df_cleaned.withColumn("prev_price_24h", lag("price_usd", 1).over(window_spec)) \
                          .withColumn("price_change_percent_24h",
                                      when(col("prev_price_24h").isNotNull(),
                                           ((col("price_usd") - col("prev_price_24h")) / col("prev_price_24h") * 100)).otherwise(0.0)) \
                          .withColumn("prev_price_7d", lag("price_usd", 7).over(window_spec)) \
                          .withColumn("price_change_percent_7d",
                                      when(col("prev_price_7d").isNotNull(),
                                           ((col("price_usd") - col("prev_price_7d")) / col("prev_price_7d") * 100)).otherwise(0.0))

    stablecoins = ["USDT", "USDC", "DAI", "USDS", "BSC-USD", "USDE"]
    df_cleaned = df_cleaned.withColumn("segment",
                                       when(col("symbol").isin(stablecoins), "stablecoin").otherwise("volatile"))

    window_spec_7d = Window.partitionBy("cryptocurrency").orderBy(col("date").cast("long")).rangeBetween(-7*24*60*60, 0)
    window_spec_30d = Window.partitionBy("cryptocurrency").orderBy(col("date").cast("long")).rangeBetween(-30*24*60*60, 0)
    df_with_averages = df_cleaned.withColumn("avg_price_7d", avg("price_usd").over(window_spec_7d)) \
                                .withColumn("avg_price_30d", avg("price_usd").over(window_spec_30d))
    logger.info("Calculated moving averages")

    df_metrics = df_with_averages.filter(col("cryptocurrency").isin(["Bitcoin", "Ethereum"])) \
                                .select("cryptocurrency", "date", "price_usd", "price_change_percent_24h", "avg_price_7d", "avg_price_30d") \
                                .orderBy("date")
    df_metrics.show(10, truncate=False)

    df_segment_agg = df_cleaned.groupBy("segment", "date").agg(
        avg("price_usd").alias("avg_price"),
        avg("market_cap").alias("avg_market_cap"),
        avg("volume_24h").alias("avg_volume_24h")
    )
    logger.info("Calculated segment aggregates")

    df_with_averages.write.partitionBy("cryptocurrency").mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/crypto_averages")
    df_segment_agg.write.partitionBy("segment").mode("overwrite").parquet("hdfs://namenode:9000/user/hive/warehouse/crypto_segment_aggregates")
    logger.info("Results saved to HDFS")

except Exception as e:
    logger.error(f"Error during processing: {e}")
    raise
finally:
    spark.stop()
    logger.info("Spark session stopped")
