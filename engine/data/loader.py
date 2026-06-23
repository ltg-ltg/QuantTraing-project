import yfinance as yf
from fredapi import Fred
import os
import time
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent

# Universe_size = 24
UNIVERSE = [
	# Tech
	'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META',
	# Finance
	'JPM', 'GS', 'BAC', 'WFC', 'BLK',
	# Healthcare
	'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK',
	# Energy
	'XOM', 'CVX', 'COP',
	# Consumer
	'AMZN', 'TSLA', 'WMT', 'HD',
	# Index ETF
	'SPY', 'QQQ'
]

MACRO_SERIES = {
    'FEDFUNDS': 'Fed Funds Rate',
    'DGS10': '10Y Treasury',
    'T10Y2Y': 'Yield Curve',
    'CPIAUCSL': 'CPI',
    'UNRATE': 'Unemployment',
    'VIXCLS': 'VIX'
}

def load_prices(tickers, start='2010-01-01', batch_size=50, sleep=2, retries=3):
	price_data = []
	for i in range(0, len(tickers), batch_size):
		batch = tickers[i:i+batch_size]
		for attempt in range(retries):
			try:
				data = yf.download(batch, start=start)
				price_data.append(data)
				time.sleep(sleep) # prevent rate limit
				break
			except Exception as e:
				print(f"yf Download attempt {attempt + 1} failed: {e}")
	return pd.concat(price_data, axis=1)

def load_prices_cashed(tickers, start='2010-01-01', cache_path=BASE_DIR / 'data' / 'cache' / 'prices.parquet'):
	if cache_path.exists():
		cached = pd.read_parquet(cache_path)
		last_date = cached.index[-1]
		today = datetime.now().date()
		if last_date.date() >= today - timedelta(days=1): # return if it's already up to date
			return cached
		
		new_data = yf.download(tickers, start=last_date + timedelta(days=1))
		updated = pd.concat([cached, new_data])
		updated = updated[~updated.index.duplicated(keep='last')] # deduplication
		updated.to_parquet(cache_path)
		return updated
	
	df = load_prices(tickers, start=start)
	cache_path.parent.mkdir(parents=True, exist_ok=True)
	df.to_parquet(cache_path)
	return df

def load_macro(start='2010-01-01'):
	load_dotenv()
	fred = Fred(api_key=os.getenv('FRED_API_KEY'))
	return {
		name: fred.get_series(series_id, observation_start=start)
		for series_id, name in MACRO_SERIES.items()
	}

print(load_prices_cashed(UNIVERSE))
print(load_macro())