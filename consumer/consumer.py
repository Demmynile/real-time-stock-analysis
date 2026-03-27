from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import from_json, col
import os

# Directory where Spark will store checkpoint data
checkpoint_dir = "/tmp/checkpoint/kafka_to_postgres"
if not os.path.exists(checkpoint_dir):
    os.makedirs(checkpoint_dir)


postgres_config = {
    "url": "jdbc:postgresql://postgres:5432/stock_data",
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "dbtable": os.getenv("POSTGRES_TABLE", "stock_prices"),
    "driver": "org.postgresql.Driver"
}

# Schema matching Kafka data
kafka_data_schema = StructType([
    StructField("date", StringType()),
    StructField("high", StringType()),
    StructField("low", StringType()),
    StructField("open", StringType()),
    StructField("close", StringType()),
    StructField("symbol", StringType())
])

# Create Spark session
spark = (SparkSession.builder
         .appName("KafkaSparkStreaming")
         .getOrCreate()
)

# Read stream from Kafka
df = (spark.readStream.format("kafka")
      .option("kafka.bootstrap.servers", "kafka:9092")
      .option("subscribe", "stock_analysis")
      .option("startingOffsets", "latest")
      .option("failOnDataLoss", "false")
      .load()
)

# Convert Kafka value (JSON string) to structured columns
parsed_df = (df
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    .select(from_json(col("value"), kafka_data_schema).alias("data"))
    .select("data.*")
)

# Processed dataframe
processed_df = parsed_df.select(
    col("date").cast(TimestampType()).alias("date"),
    col("high").alias("high"),
    col("low").alias("low"),
    col("open").alias("open"),
    col("close").alias("close"),
    col("symbol").alias("symbol")
)

def write_to_postgres(batch_df, batch_id):
    # Writes a microbatch DataFrame to PostgreSQL using JDBC in 'append' mode.
    batch_df.write \
        .format("jdbc") \
        .mode("append") \
        .options(**postgres_config) \
        .save()


# Stream to PostgreSQL using foreachBatch
query = (
    processed_df.writeStream
    .foreachBatch(write_to_postgres)  # Use foreachBatch for JDBC sinks
    .option("checkpointLocation", checkpoint_dir)  # Directory where Spark will store its checkpoint data, crucial in streaming to enable fault tolerance
    .outputMode("append")  # Or "append", depending on your use case and table schema
    .start()
)
# Keep stream running
query.awaitTermination()