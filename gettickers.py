import os

from binance.client import Client
from decimal import Decimal

from main import exchange_info
#get list of tickers 
if os.path.exists("tickers.txt"):
  os.remove("tickers.txt")
tickers = open("tickers.txt","a")
for s in exchange_info['symbols']:
	ticker = s['symbol']
	l = len(ticker)
	lastthree = ticker[(l-3):l]
	if(lastthree == 'USD' and ticker[0:3] != 'USD'):
		tickers.write(ticker + "\n")
tickers.close()