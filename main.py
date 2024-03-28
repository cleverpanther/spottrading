import requests
import time
import hashlib
import hmac
import resend
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import re
import sys

load_dotenv()

url=os.getenv('url')
api_key=os.getenv('api_key')
secret_key = os.getenv('secret_key')
symbol = os.getenv('symbol')
from_email = os.getenv('from')
to_email = os.getenv('to')
resend_api_key = os.getenv('resend_api_key')
subject = "Bybit Auto-Bot"
threshold = int(os.getenv('threshold'))

print("Initialized Server")

expdates = []
httpClient=requests.Session()
recv_window=str(5000)

def HTTP_Request(endPoint,method,payload,Info):
    global time_stamp
    time_stamp=str(int(time.time() * 10 ** 3))
    signature=genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if(method=="POST"):
        response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)
    return response.text

def genSignature(payload):
    param_str= str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
    signature = hash.hexdigest()
    return signature

def parse_symbol(symbol):
    match = re.search(r'(\d+)(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d+)-(\d+)', symbol)
    if match:
        day, month, year, strike_price = match.groups()
        date = datetime.strptime(f"{day} {month} {year}", "%d %b %y")
        return date, int(strike_price)
    else:
        return None

def firststep(now):
    endpoint="/v5/market/tickers"
    method="GET"
    params='category=option&baseCoin=BTC'
    text = HTTP_Request(endpoint,method,params,"UnFilled")
    json_data = json.loads(text)
    option_list = json_data['result']['list']
    sorted_list = sorted(option_list, key=lambda x: parse_symbol(x['symbol']))
    alldate = sorted(set([parse_symbol(item['symbol'])[0] for item in sorted_list]))
    upperdate = now + timedelta(days=20)
    canddate = []
    for date in alldate:
        if date >= now and date < upperdate:
            canddate.append(date)
        else:
            continue
    return canddate

def secondstep(expdate):
    endpoint="/v5/market/tickers"
    method="GET"
    params='category=option&baseCoin=BTC&expDate=' + expdate
    text = HTTP_Request(endpoint,method,params,"UnFilled")
    # print(text)
    json_data = json.loads(text)
    option_list = json_data['result']['list']
    sorted_list = sorted(option_list, key=lambda x: parse_symbol(x['symbol']))
    strikeprice = sorted(set([parse_symbol(item['symbol'])[1] for item in sorted_list]))
    candprice = []
    num = 0
    for price in strikeprice:
        candprice.append(price)
        num = num + 1
        if num == 4:
            break
    return candprice

def thirdstep(expdate, strike_price):
    strike_price = str(strike_price)
    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=option&symbol=' + symbol + '-' + expdate + '-' + strike_price + '-C&side=Sell'
    text1 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data1 = json.loads(text1)
    Call_BidPrice = float(data1['result']['list'][0]['bid1Price'])

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=option&symbol=' +  symbol + '-' + expdate + '-' + strike_price + '-P&side=Buy'
    text2 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data2 = json.loads(text2)
    Put_AskPrice = float(data2['result']['list'][0]['ask1Price'])

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=linear&symbol=' + symbol + 'USDT'
    text3 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data3 = json.loads(text3)
    Perp_AskPrice = float(data3['result']['list'][0]['ask1Price'])
    
    Profitability = (Call_BidPrice - Put_AskPrice) - (Perp_AskPrice - int(strike_price))
    result = expdate + '-' + strike_price + '=>' + str(Profitability)

    return [result, Profitability]

# Create a function to send email
def send_email(subject, result, body):
    resend.api_key = resend_api_key
    r = resend.Emails.send({
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "html": "Positive P&L: " + result
        })
    print('Positive P$L: ' + str(result))
    print("Email Already Sent.")

def progress_bar(current, total):
    steps = 50
    progress = int(current / total * steps)
    percentage = float(progress * 100 / steps)
    bar_str = '[' + '=' * progress + ' ' * (steps - progress) + ']'
    sys.stdout.write(f'\r{bar_str} {percentage}% completed')
    sys.stdout.flush()

# Loop to send email every 1 minute
while True:
    now = datetime.now()
    current_output = 'Now is ' + str(now) + '.'
    print(current_output)
    canddate = firststep(now)
    datenum = canddate.__len__()
    outputbody = ""
    total_iterations = len(canddate) * 4
    current_iteration = 0
    profitability_this_period = []
    for date in canddate:
        expdate = date.strftime("%d%b%y").upper().lstrip("0")
        candstrikeprice = secondstep(expdate=expdate)
        for strikeprice in candstrikeprice:
            [result, profitability] = thirdstep(expdate, strikeprice)
            profitability_this_period.append(profitability)
            current_iteration += 1
            progress_bar(current_iteration, total_iterations)
            if profitability > threshold:
                outputbody = outputbody + result + '\n'
            time.sleep(1)
    progress_bar(total_iterations, total_iterations)
    print()
    if outputbody == "":
        print("There is no appropriate ticker.")
    else:
        send_email(subject=subject, result = result, body=outputbody)
        print("Email Already Sent!")
    print(profitability_this_period, "Process Finished.")
    time.sleep(5)  # Sleep for 60 seconds (1 minute)