#!/bin/bash

LOCAL_DIR="/home/skyline/crypto_pipeline/historical_data"
HDFS_DIR="/crypto_data_historical"
HDFS_COMBINED_DIR="/crypto_data"
HDFS_COMBINED_FILE="$HDFS_COMBINED_DIR/crypto_data_combined.csv"
NAMENODE="namenode"

LOG_FILE="/home/skyline/crypto_pipeline/upload_hdfs.log"
echo "[$(date)] Starting upload to HDFS" >> $LOG_FILE

if [ ! -d "$LOCAL_DIR" ]; then
    echo "[$(date)] Error: Directory $LOCAL_DIR does not exist" >> $LOG_FILE
    exit 1
fi

CSV_FILES=$(ls $LOCAL_DIR/*.csv 2>/dev/null)
if [ -z "$CSV_FILES" ]; then
    echo "[$(date)] Error: No CSV files found in $LOCAL_DIR" >> $LOG_FILE
    exit 1
fi

docker exec $NAMENODE hdfs dfs -mkdir -p $HDFS_DIR
if [ $? -ne 0 ]; then
    echo "[$(date)] Error: Failed to create HDFS directory $HDFS_DIR" >> $LOG_FILE
    exit 1
fi

for file in $LOCAL_DIR/*.csv; do
    filename=$(basename "$file")
    echo "[$(date)] Uploading $filename to HDFS" >> $LOG_FILE
    docker cp "$file" $NAMENODE:/tmp/$filename
    docker exec $NAMENODE hdfs dfs -put /tmp/$filename $HDFS_DIR/
    if [ $? -eq 0 ]; then
        echo "[$(date)] Successfully uploaded $filename to $HDFS_DIR" >> $LOG_FILE
        docker exec $NAMENODE rm /tmp/$filename
    else
        echo "[$(date)] Error: Failed to upload $filename to $HDFS_DIR" >> $LOG_FILE
    fi
done

echo "[$(date)] Combining CSV files without headers" >> $LOG_FILE
docker exec -it $NAMENODE bash -c "hdfs dfs -cat $HDFS_DIR/*.csv | grep -v '^cryptocurrency,' > /tmp/combined.csv"
if [ $? -ne 0 ]; then
    echo "[$(date)] Error: Failed to combine CSV files" >> $LOG_FILE
    exit 1
fi

docker exec -it $NAMENODE hdfs dfs -test -d $HDFS_COMBINED_DIR
if [ $? -ne 0 ]; then
    docker exec -it $NAMENODE hdfs dfs -mkdir -p $HDFS_COMBINED_DIR
    if [ $? -ne 0 ]; then
        echo "[$(date)] Error: Failed to create HDFS directory $HDFS_COMBINED_DIR" >> $LOG_FILE
        exit 1
    fi
fi

docker exec -it $NAMENODE hdfs dfs -put -f /tmp/combined.csv $HDFS_COMBINED_FILE
if [ $? -ne 0 ]; then
    echo "[$(date)] Error: Failed to upload combined CSV to $HDFS_COMBINED_FILE" >> $LOG_FILE
    exit 1
fi
docker exec -it $NAMENODE rm /tmp/combined.csv

echo "[$(date)] Upload and combination to HDFS completed" >> $LOG_FILE
