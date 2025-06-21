import mariadb
import pandas as pd
import time
import os
import socket
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/skyline/crypto_pipeline/stream_mariadb.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def wait_for_mariadb(host="mariadb", port=3306, timeout=30):
    start_time = time.time()
    while True:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            logger.info("MariaDB is up!")
            break
        except socket.error:
            if time.time() - start_time > timeout:
                raise Exception("Timeout waiting for MariaDB")
            logger.info("Waiting for MariaDB...")
            time.sleep(2)

try:
    wait_for_mariadb()
    conn = mariadb.connect(
        host="mariadb",
        user="root",
        password="rootpassword",
        database="crypto_db"
    )
    logger.info("Connected to MariaDB")
except mariadb.Error as e:
    logger.error(f"Error connecting to MariaDB: {e}")
    exit(1)

spool_dir = "/home/skyline/crypto_pipeline/crypto_stream"
os.makedirs(spool_dir, exist_ok=True)

while True:
    try:
        query = "SELECT * FROM crypto_prices ORDER BY RAND() LIMIT 100"
        df = pd.read_sql(query, conn)
        if len(df) == 0:
            logger.warning("No records retrieved from MariaDB")
        else:
            timestamp = int(time.time())
            spool_file = f"{spool_dir}/crypto_data_{timestamp}.csv"
            df.to_csv(spool_file, index=False, header=False)
            logger.info(f"Saved {len(df)} records to {spool_file}")
    except mariadb.Error as e:
        logger.error(f"Error querying MariaDB: {e}")
    time.sleep(10)

conn.close()
