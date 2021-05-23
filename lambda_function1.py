## sample lambda code 
import json
from datetime import timezone 
import datetime, time
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import datetime,time,os,random;
import pandas
import numpy as np
import requests as r
import indicators

cors_header =  {
    'statusCode': 200,
    'headers': {
            'Access-Control-Allow-Headers': 'Accept',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*'
        },
        'body': None
    }


#----------------------------------------- INDICATORS -----------------------------------------#
# RSI indicator calculation
def RSI(df, base="close", period=21, target="rsi"):
    """Pandas RSI CALCULATOR"""

    delta = df[base].diff()
    up, down = delta.copy(), delta.copy()

    up[up < 0] = 0
    down[down > 0] = 0

    rUp = up.ewm(com=period - 1,  adjust=False).mean()
    rDown = down.ewm(com=period - 1, adjust=False).mean().abs()

    df['RSI_' + str(period)] = 100 - 100 / (1 + rUp / rDown)
    df['RSI_' + str(period)].fillna(0, inplace=True)
    df[target] = df['RSI_' + str(period)]
    return df


# EMA indicator calculation
def EMA(df, base, period, target, alpha=False):
    """Pandas EMA """

    con = pandas.concat([df[:period][base].rolling(
        window=period).mean(), df[period:][base]])

    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        df[target] = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        df[target] = con.ewm(span=period, adjust=False).mean()

    df[target].fillna(0, inplace=True)
    return df


# SMA indicator calculation
def SMA(df, base, period, target):
    """Pandas SMA CALCULATOR"""

    df[target] = df[base].rolling(window=period).mean()
    df[target].fillna(0, inplace=True)
    return df


# YEST indicator calculation
def YEST(df, base, period, target):
    """ YEST indicator calculation """

    df[target] = df[base].shift()
    df[target].fillna(0, inplace=True)
    return df
#----------------------------------------- END INDICATORS -----------------------------------------#



#--------------------------- Get Historical Data & Apply indicators ---------------------------#
def apply_indicators(df, pmap, from_date):
    """ Apply all indicators"""
    # df['date'] = pandas.to_datetime(df['date'])
    # df.set_index('date', inplace=True)
    df['datetime'] = df['date']

    # indicators
    df = RSI(df, 'close', pmap['rsi1']) #rsi1
    df = RSI(df, 'close', pmap['rsi2'])  #rsi2
    df = EMA(df=df, base='close', period=pmap['ema1'], target='ema5') #ema1
    df = RSI(df, 'ema5', pmap['rsi3'], "greenline") #rsi3 
    df = SMA(df=df, base='greenline',period=pmap['sma1'], target='redline') #sma1
    # df = SMA(df, 'RSI_9','greenline', 5)
    df = SMA(df=df, base='close', target='SMA200', period=pmap['sma2']) #sma2
    df = SMA(df=df, base='close', target='SMA50', period=pmap['sma3']) #sma3
    df = YEST(df=df, base='greenline', target='yestgreenline', period=pmap['yest1']) #yest1 

    df['date']  = df['date'].dt.strftime('%Y-%m-%d')

    #compute Ylw triangle
    conditions = (df['greenline']>20) & (df['yestgreenline']<20) & (df['yestgreenline']>1) & (df['yestgreenline']<99)
    df.loc[conditions, "ylw_tri"] = 1
    df["ylw_tri"].fillna(0, inplace=True) 
    
    #compute Green triangle
    conditions2 = (df['SMA50']<df['SMA200']) & (df['greenline']>40) & (df['yestgreenline']<40) & (df['yestgreenline']>1)
    df.loc[conditions2, "green_tri"] = 1
    df["green_tri"].fillna(0, inplace=True)

    #compute Blue triangle
    conditions3 = (df['SMA50']>df['SMA200']) & (df['greenline']>40) & (df['yestgreenline']<40) & (df['yestgreenline']>1) & (df['SMA200']>1)
    df.loc[conditions3, "blue_tri"] = 1
    df["blue_tri"].fillna(0, inplace=True)

    df['f_date']=str(from_date)
    mask = df['date'] >= df['f_date']
    df = df.loc[mask]
    print(df)
    return df


def get_historical_data(kite=None,instrument_token=None, from_date=None, to_date=None,interval="15minute", continuous=False, oi=True, param=None): #retrive get historical data
    data = None
    try:
        if kite is None:
            print("Kite object is not initialized...")
            return

        data = kite.historical_data(instrument_token=instrument_token, from_date=from_date, to_date=to_date, interval=interval, oi=oi)
        
        df = pandas.DataFrame(data)

        #apply_indicators 
        df = apply_indicators(df, param, from_date)

        df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:00')
        tmp_data = df.to_dict('index')

        data = [x[1] for x in tmp_data.items()]
    except Exception as e:
        print(f"get_historical_data - {e}")
        raise e

    ## return data
    return data

## ------------------------------ map parameters -------------------------##
def map_param(request_data):
    """ Map param which are coming through URL """
    pmap = {}
    try:
        pmap['instrument_token'] = request_data['instrument_token']
    except Exception as e:
        pmap['instrument_token'] = None
    
    try:
        pmap['from_date'] = request_data['from_date']
    except Exception as e:
        pmap['from_date'] = None #'2020-01-10' format 'YYYY-MM-DD'
    
    try:
        pmap['to_date'] = request_data['to_date']
    except Exception as e:
        pmap['to_date'] = None #'2020-01-10' format 'YYYY-MM-DD'

    try:
        pmap['interval'] = request_data['interval']
    except Exception as e:
        pmap['interval'] = '15minute'

    # indicators params
    # df = fn.RSI(df, 'close', 14) #rsi1
    try:
        pmap['rsi1'] = request_data['rsi1']
    except Exception as e:
        pmap['rsi1'] = 14 #default

    #df = fn.RSI(df, 'close', 9) #rsi2
    try:
        pmap['rsi2'] = request_data['rsi2']
    except Exception as e:
        pmap['rsi2'] = 9 #default

    #df = fn.EMA(df, 'close','ema5',5) #ema1
    try:
        pmap['ema1'] = request_data['ema1']
    except Exception as e:
        pmap['ema1'] = 5 #default

    #df = fn.RSI(df, 'ema5', 14,"greenline") #rsi3 
    try:
        pmap['rsi3'] = request_data['rsi3']
    except Exception as e:
        pmap['rsi3'] = 14 #default

    #df = fn.SMA(df, 'greenline','redline', 5) #sma1
    try:
        pmap['sma1'] = request_data['sma1']
    except Exception as e:
        pmap['sma1'] = 5 #default
   

    #df = fn.SMA(df, 'close','SMA200', 200) #sma2
    try:
        pmap['sma2'] = request_data['sma2']
    except Exception as e:
        pmap['sma2'] = 200 #default


    #df = fn.SMA(df, 'close','SMA50', 50) #sma3
    try:
        pmap['sma3'] = request_data['sma3']
    except Exception as e:
        pmap['sma3'] = 50 #default

    #df = fn.YEST(df, 'greenline','yestgreenline', 1) #yest1 
    try:
        pmap['yest1'] = request_data['yest1']
    except Exception as e:
        pmap['yest1'] = 1 #default
    
    return pmap

## ------------------------------- lambda_handler ------------------------------##


def lambda_handler(event=None, context=None):
    global cors_header
    
    try:
        param 	= map_param(event['queryStringParameters'])
        print('input_param - ',param)

        ## API connection
        response_data 	= r.get("https://j0ytn5kp4a.execute-api.ap-south-1.amazonaws.com/default/getapidetails")
        data 			= response_data.json()
        # print(f"api_response - {data}")

        api_k 			= data['api_key'] 		#api_key
        api_s 			= data['api_secret'] 	#api_secret
        session_key 	= data['session_key'] 	#session_key

        ## Kite API initialized
        kite, kws = None,None
        kite = KiteConnect(api_key=api_k)
        kite.set_access_token(session_key)

        ## get historical_data from kite
        hd 					= get_historical_data(kite=kite, instrument_token=param['instrument_token'], from_date=param['from_date'], to_date=param['to_date'], interval=param['interval'], param=param)
        print(f"historical_data - {hd}")
        cors_header['body'] = json.dumps(hd)
        # cors_header['body'] = json.dumps(historical_data)
    except Exception as e:
        raise e
        print('Exception : ',e)
    
    return cors_header

## ------- Test Conf -----------## 
# print(lambda_handler(event={'queryStringParameters':{'instrument_token':738561, 'from_date':'2020-12-02', 'to_date':'2020-12-02', 'interval':'minute', 'rsi1':14, 'rsi2':9, 'ema1':5, 'rsi3':14, 'sma1':5, 'sma2':200, 'sma3':50, 'yest1':1}}))
# lambda_handler(event={'queryStringParameters':{'symbol':100033, 'timeframe':'1W', 'rsi_period':14, 'range':2}})
# # lambda_handler(event={'queryStringParameters':{'symbol':100033, 'timeframe':'1D', 'rsi_period':21}})
