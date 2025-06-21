# Анализ динамики цен криптовалют с использованием Hadoop-экосистемы

![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.4.0-orange)
![Hadoop](https://img.shields.io/badge/Hadoop-2.7.7-yellowgreen)

## 📌 О проекте

Проект реализует ETL-конвейер для анализа динамики цен криптовалют с использованием:
- **REST API CoinGecko** (источник данных)
- **Hadoop-экосистемы** (HDFS, Spark, Hive, Kafka)
- **Docker-контейнеризации**

Ключевые особенности:
- Lambda-архитектура (пакетная + потоковая обработка)
- Автоматизированный сбор данных (50 криптовалют, обновление каждые 10 мин)
- Выявление аномалий (>3% изменения цены за 24ч)
- Сравнительный анализ stablecoins vs волатильных активов

## 📊 Основные результаты

1. **Stablecoins** демонстрируют:
   - Волатильность < 0.1%
   - Стабильную капитализацию (±0.5-1%)

2. **Волатильные активы** (Bitcoin, Ethereum):
   - Средняя дневная волатильность: 1.83-2.94%
   - Корреляция цен: 0.67
   - Недельный тренд: -0.42% (BTC), -3.12% (ETH)

3. **Аномалии**:
   - 5.2% скачок Bitcoin (10.04.2025)
   - 15% рост объема торгов при аномалиях

## 🛠 Технологический стек

| Компонент       | Назначение                          |
|-----------------|-------------------------------------|
| **HDFS**        | Распределенное хранение данных      |
| **Spark**       | Пакетная обработка и аналитика      |
| **Spark Streaming** | Реалтайм-анализ аномалий        |
| **Hive**        | SQL-интерфейс для аналитических запросов |
| **Kafka**       | Потоковая передача данных           |
| **MariaDB**     | Промежуточное хранение сырых данных |

## 🚀 Запуск проекта

### Предварительные требования
- Docker 20.10+
- Docker Compose 1.29+
- 8+ GB RAM

### Инструкция по развертыванию

1. Клонировать репозиторий:  
git clone https://github.com/skyline71/crypto-data-pipeline-docker.git  
cd crypto-data-pipeline-docker

3. Запустить контейнеры:  
docker-compose up -d

4. Инициализировать Hive-таблицы:  
docker exec -it hive-server beeline -u jdbc:hive2://localhost:10000 \
  -f /opt/hive/scripts/create_tables.hql

5. Запустить ETL-процессы:
## Сбор данных
docker exec -it python-stream python /data/fetch_crypto_data.py

## Пакетная обработка
docker exec -it spark-master spark-submit /data/batch_processing.py

## Потоковая обработка
docker exec -it spark-master spark-submit /data/spark_streaming.py

## 📈 Примеры аналитических запросов

1. Средняя волатильность по криптовалютам:  
SELECT  
  cryptocurrency,  
  AVG(ABS(price_change_percent_24h)) AS avg_volatility  
FROM crypto_averages  
GROUP BY cryptocurrency  
ORDER BY avg_volatility DESC;  


2. Корреляция цен BTC/ETH:  
df.stat.corr("bitcoin_price", "ethereum_price")

## 📜 Лицензия

Проект распространяется под лицензией Apache-2.0 license. Подробнее см. в файле [LICENSE](LICENSE).

---

**Автор**: [skyline71](https://github.com/skyline71)  
**Контакты**: romanmozzherin2015@gmail.com

© 2025
