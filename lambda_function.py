## sample lambda code 
import json
import pandas
import requests
from datetime import timezone 
import datetime, time

## ------------------------------- config ------------------------------##
def config():
	# Config Data
	config_data = {
		'supported_resolutions': ['1D','2D', '3D', '4D', '5D','6D' ,'1W', '1M'], #'1', '5', '15', '30', '60', 
		'supports_group_request': True,
		'supports_marks': False,
		'supports_search': False,
		'supports_timescale_marks': False,
	}
	
	return json.dumps(config_data)

## ------------------------------- symbol_info ------------------------------##

symbol_info_data = {	
	'symbol': [],
	'description': [],
	'exchange-listed': "NYSE",
	'exchange-traded': "NYSE",
	'minmovement': 1,
	'minmovement2': 0,
	'pricescale': [],
	'has-dwm': True,
	'has-intraday': True,
	'has-no-volume': [],
	'type': [],
	'ticker': [],
	'timezone': "Asia/Kolkata",
	'session-regular': "0000-2400",
}

def build_symbol_info():
	global symbol_info_data
	df = pandas.read_csv("input_file.csv")
	ticker = []
	symbol = []
	pricescale = []
	has_no_volume = []
	symbol_type = []
	symbol_with_tickers = []

	for index, row in df.iterrows():
		ticker.append(str(row['AMFI CODE']))
		symbol.append(row['Scheme Name'])
		symbol_with_tickers.append(str(row['AMFI CODE'])+"~0")# +" : "+str(row['Scheme Name']))
		pricescale.append(100)
		has_no_volume.append(True)
		symbol_type.append("stock")
	
	symbol_info_data['symbol'] = ticker #symbol_with_tickers
	symbol_info_data['description'] = symbol
	symbol_info_data['pricescale'] = pricescale
	symbol_info_data['has-no-volume'] = has_no_volume
	symbol_info_data['type'] = symbol_type
	symbol_info_data['ticker'] = ticker
	

def symbol_info():
	build_symbol_info()
	return json.dumps(symbol_info_data)


## ------------------------------- history ------------------------------##
hist_data = {
	's': "ok",
	't': [],
	'c': []}

no_data = {'s':'no_data'}
flag = True

def config_hostorical_data(request_data):
	
	symbol = request_data['symbol']
	api_data = requests.get(f"https://api.mfapi.in/mf/"+str(symbol))
	#print(api_data.data)
	if api_data.ok:
		data = json.loads(api_data.text)['data']
		close = []
		date1 = []
		for row in data:
			dt = datetime.datetime.strptime(row['date'], '%d-%m-%Y')
			utc_time = dt.replace(tzinfo = timezone.utc) 
			utc_timestamp = int(utc_time.timestamp())
			close.append(row['nav'])
			date1.append(utc_timestamp)
		
		hist_data['t'] = date1[::-1]
		hist_data['o'] = hist_data['h'] = hist_data['l'] = hist_data['c'] = close[::-1]
		hist_data['v'] = [0 for x in close]
		#hist_data['s'] = 'no_data'

# Get history
def history(request_data):
	global flag
	if flag:
		config_hostorical_data(request_data)
		return json.dumps(hist_data)

## ------------------------------- time ------------------------------##
def get_server_time():
	return str(int(time.time()))

## ------------------------------- lambda_handler ------------------------------##

def lambda_handler(event, context):
	endpoint = event['rawPath'].split("/")[-1]
	#endpoint = event.split("/")[-1]
	
	## config
	if endpoint == 'config':
		return config()
	
	## symbol_info
	if endpoint == 'symbol_info':
		return symbol_info()

	## history
	if endpoint == 'history':
		return history(event['queryStringParameters'])
		#return history({'symbol':"100822"})
	
	## time
	if endpoint == 'time':
		return get_server_time()
	
	return json.dumps({'responce':None})
