import os
import random
import time
import decimal
import logging
import dotenv

from binance.client import Client
from decimal import getcontext,Decimal



NUM_ITERATIONS = 1
INTERVAL = 3660 #time between runs, 3660s, 1 hr
MIN_BUY = 10.50	#minimum amount to buy in USD
INITAL_BUY_USD = 11.00	#starting buy amount in USD
FEE = .000750	#fee as decimal


logging.basicConfig(filename='run.log', encoding='utf-8', level=logging.DEBUG)

dotenv.load_dotenv()
api_key = os.getenv('TEST_API_KEY')
api_secret = os.getenv('TEST_SECRET')


client = Client(api_key,api_secret,tld='us')
exchange_info = client.get_exchange_info()
acc_info = client.get_account()
getcontext().prec = 16

#Derecated code to get ticker, in own file now
	#client.API_URL = 'https://testnet.binance.vision/api'
	#get list of tickers 
	#if os.path.exists("tickers.txt"):
	#  os.remove("tickers.txt")
	#tickers = open("tickers.txt","a")
	#for s in exchange_info['symbols']:
	#	ticker = s['symbol']
	#	if(s['quoteAsset'] == 'USD' and ticker[0:3] != 'USD' and s['status'] == 'TRADING'):
	#		tickers.write(ticker + "\n")
	#		print(ticker + ":\n\t");
	#		print(s)
	#tickers.close()

#print out all cryptos held and amounts
for i in acc_info["balances"]:
	if(Decimal(i['free']) != 0.0):
		print(i['asset'] + ":" + i['free'] + '\n')
		if(i['asset'] != "USD"):
			#USDonly = false
			print("Cryptos other than USDC are held, please fix")
			#quit()
USDbal = client.get_asset_balance('USD')['free']
#print(USDbal)

#load all tickers into list
tickers = open("tickers.txt",'r')
coinlist = tickers.readlines()

#initalize the amoutn buying to the initial buy amount
buy_amt_USD = INITAL_BUY_USD

#limit the number of iterations
iterations_left = NUM_ITERATIONS

#main loop
while iterations_left>0 and USDbal >= MIN_BUY:

	#decrement num of iterations if iternation limited; should be commented out if running constantly
	iterations_left = iterations_left-1	
	try:
		#coin = random.choice(coinlist).strip()
		coin = 'ETHUSD'
		data = client.get_symbol_info(coin)
		
		
		step_size = Decimal(data['filters'][2]['stepSize'])
		min_notional = Decimal(data['filters'][3]['minNotional'])
		#print(data['filters'])
		
		coinprice = Decimal((client.get_symbol_ticker(symbol=coin))['price'])
		precision = data['baseAssetPrecision']
		decimal.getcontext().prec = precision
		
		
		buy_amt = (Decimal(buy_amt_USD - (buy_amt_USD * FEE))/Decimal(coinprice))
		
		#make the buy amount of the coin fit into the step size
		buy_amt = Decimal(buy_amt - (buy_amt % step_size)).normalize()
		
		
		cost_basis = buy_amt * coinprice
		print("Symbol:" + coin)
		print("Coin Price:" + str(coinprice))
		print('Buy Amount:' + str(buy_amt))
		print("Cost Basis:" + str(cost_basis))
		print('Precision:' + str(precision))
		print("Step Size:" + str(step_size))
		print("MIN_NOTIONAL:" + str(min_notional))
		
		#send buy order
		buy_order = client.create_test_order(
			symbol=coin,
			side='BUY',
			type='MARKET',
			quantity=buy_amt,)
	except Exception as e:
		#print exception along with error message
		print(e)
		print("Failed buy on token:" + coin)
		
		#remove the coin from the coin list, \n needs to be appended as coinlist contains nullterminator, returns not in list exception if not appended
		coinlist.remove(coin + '\n')
		continue
	else:
		print('\n\n\n' + str(buy_order) + '\n\n\n')
		buy_price_USD = buy_order['cummulativeQuoteQty']
		print('buy price USD:' +str(buy_price_USD))
		time.sleep(INTERVAL)
	try:
	
		#remove USD from end of coin to get base asset
		baseAsset = coin[0:(len(coin) -3)]
		
		#sell all of base asset
		sell_amt = Decimal(client.get_asset_balance(asset=baseAsset)['free'])
		print("Sell amt unnormalized:" + str(sell_amt))
		
		#conform to stepsize and precision
		sell_amt = Decimal(sell_amt - (sell_amt % step_size)).normalize()
		print("Sell amt normalized:" + str(sell_amt))
		
		
		#sellorder
		sell_order = client.create_test_order(
			symbol=coin,
			side='SELL',
			type='MARKET',
			quantity = sell_amt)
	except Exception as e:
	
		#If sell is failed print error and exit loop 
		print(e)
		print("Failed sell on token:" + coin)
		break
	else:
		print('\n\n\n' + str(sell_order) + '\n\n\n')
		sell_price_USD = sell_order['cummulativeQuoteQty']
		print('sell price USD:' +str(sell_price_USD))
		USDbal = Decimal(client.get_asset_balance('USD')['free'])
		if(USDbal < buy_amt_USD):
			buy_amt_USD = USDbal
		


