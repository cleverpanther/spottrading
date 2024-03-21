import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import time
import hashlib
import hmac
import uuid
import resend
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

httpClient=requests.Session()
recv_window=str(5000)
# url="https://api-testnet.bybit.com" # Testnet endpoint
url="https://api.bybit.com"
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
    print(Info + " Elapsed Time : " + str(response.elapsed))
    return response.text

def genSignature(payload):
    param_str= str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
    signature = hash.hexdigest()
    return signature

def gatherdata():
    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=option&symbol=BTC-29MAR24-48000-C&side=Sell'
    text1 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data1 = json.loads(text1)
    Call_BidPrice = float(data1['result']['list'][0]['bid1Price'])

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=option&symbol=BTC-29MAR24-48000-P&side=Buy'
    text2 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data2 = json.loads(text2)
    Put_AskPrice = float(data2['result']['list'][0]['ask1Price'])

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=linear&symbol=BTCUSDT'
    text3 = HTTP_Request(endpoint,method,params1,"UnFilled")
    data3 = json.loads(text3)
    Perp_AskPrice = float(data3['result']['list'][0]['ask1Price'])
    
    Profitability = (Call_BidPrice - Put_AskPrice) - (Perp_AskPrice - 48000)
    
    return Profitability

# # Email configuration
# sender_email = "titanrtx0714@outlook.com"
# # sender_password = "infinite0714"
# receiver_email = "titanrtx1010102@hotmail.com"
subject = "Bybit Data"
api_key='3GsEVrhzzOnMusaoSt'
secret_key ='y90nFfUgTEUFoDsXHpkduxw4cxrOQjvbfApI'

# Create a function to send email
def send_email(subject, body):
    resend.api_key = "re_enoinqaw_Dhxn8mSSK3wkD25SfaZV2jhK"

    if body > 500:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "titanrtx0714@gmail.com",
            "subject": subject,
            "html": "Good Situation: " + str(body)
            })
    else:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "titanrtx0714@gmail.com",
            "subject": subject,
            "html": "Bad Situation: " + str(body)
            })

    # # Create a multipart message
    # message = MIMEMultipart()
    # message["From"] = sender_email
    # message["To"] = receiver_email
    # message["Subject"] = subject

    # # Add body to email
    # message.attach(MIMEText(body, "plain"))

    # # Connect to SMTP server
    # with smtplib.SMTP("smtp-mail.outlook.com", port=587) as server:
    #     server.starttls()  # Secure the connection
    #     server.login(sender_email, sender_password)
    #     server.sendmail(sender_email, receiver_email, message.as_string())

# Loop to send email every 1 minute
while True:
    body = gatherdata()
    print(body)
    send_email(subject=subject, body=body)
    print("Email sent successfully.")
    time.sleep(10)  # Sleep for 60 seconds (1 minute)
