import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv('/home/skyline/crypto_pipeline/.env')
API_KEY = os.getenv('COINGECKO_API_KEY')

if not API_KEY:
    raise ValueError("COINGECKO_API_KEY not found in .env file")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/skyline/crypto_pipeline/crypto_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))


def get_top_coins(per_page=50):
    """Получение списка топ-50 криптовалют с total_supply и circulating_supply."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    headers = {"x-cg-demo-api-key": API_KEY}
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "sparkline": False
    }
    try:
        response = session.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [
            (
                coin['id'],
                coin['name'],
                coin['symbol'].upper(),
                coin.get('total_supply', 0.0),
                coin.get('circulating_supply', 0.0)
            ) for coin in data
        ]
    except requests.RequestException as e:
        logger.error(f"Error fetching top coins: {e}")
        return []


def fetch_historical_data(coin_id, coin_name, coin_symbol, total_supply, circulating_supply, date):
    """Получение исторических данных для одной криптовалюты за конкретную дату."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
    headers = {"x-cg-demo-api-key": API_KEY}
    params = {"date": date.strftime('%d-%m-%Y'), "localization": False}
    try:
        response = session.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        market_data = data.get('market_data', {})
        return {
            'cryptocurrency': coin_name,
            'symbol': coin_symbol,
            'date': date.strftime('%Y-%m-%d 00:00:00'),
            'price_usd': market_data.get('current_price', {}).get('usd', 0.0),
            'market_cap': market_data.get('market_cap', {}).get('usd', 0.0),
            'volume_24h': market_data.get('total_volume', {}).get('usd', 0.0),
            'price_change_percent_24h': 0.0,
            'price_change_percent_7d': 0.0,
            'total_supply': total_supply,
            'circulating_supply': circulating_supply
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {coin_id} on {date}: {e}")
        return None
    except requests.RequestException as e:
        logger.error(f"Network error for {coin_id} on {date}: {e}")
        return None
    except KeyError as e:
        logger.warning(f"Missing data for {coin_id} on {date}: {e}")
        return None


def save_to_csv(df, output_dir, date_str):
    """Сохранение данных в CSV для конкретной даты."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = f"{output_dir}/crypto_data_{date_str}.csv"
    df.to_csv(output_file, index=False, header=True)
    logger.info(f"Data saved to {output_file}")
    return output_file


def collect_historical_data(days=30, output_dir="/home/skyline/crypto_pipeline/historical_data"):
    """Сбор исторических данных за указанное количество дней для топ-50 криптовалют."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    coins = get_top_coins()

    if not coins:
        logger.error("No coins retrieved. Exiting.")
        return

    logger.info(f"Collecting data for {len(coins)} coins from {start_date} to {end_date}")

    for current_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        date_str = current_date.strftime('%Y%m%d')
        output_file = f"{output_dir}/crypto_data_{date_str}.csv"

        if os.path.exists(output_file):
            logger.info(f"Skipping {current_date}: file {output_file} already exists")
            continue

        logger.info(f"Processing date: {current_date}")
        daily_data = []
        for coin_id, coin_name, coin_symbol, total_supply, circulating_supply in coins:
            data = fetch_historical_data(coin_id, coin_name, coin_symbol, total_supply, circulating_supply,
                                         current_date)
            if data:
                daily_data.append(data)
            time.sleep(2.5)

        if daily_data:
            df = pd.DataFrame(daily_data)
            save_to_csv(df, output_dir, date_str)
        else:
            logger.warning(f"No data collected for {current_date}")


if __name__ == "__main__":
    try:
        collect_historical_data(days=30)
    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        session.close()
