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
    print(response.text)
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
    params1='category=option&symbol=BTC-29MAR24-22000-C&side=Buy'
    text1 = HTTP_Request(endpoint,method,params1,"UnFilled")

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=option&symbol=BTC-29MAR24-26000-P&side=Sell'
    text2 = HTTP_Request(endpoint,method,params1,"UnFilled")

    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=linear&symbol=BTCUSDT'
    text3 = HTTP_Request(endpoint,method,params1,"UnFilled")
    
    endpoint="/v5/market/tickers"
    method="GET"
    params1='category=linear&symbol=BTCPERP'
    text4 = HTTP_Request(endpoint,method,params1,"UnFilled")
    
    totaltext = '<p>' + text1 + '</p><p>' + text2 + '</p><p>' + text3 + '</p><p>' + text4 + '</p>'
    
    return totaltext

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

    r = resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": "titanrtx0714@gmail.com",
    "subject": subject,
    "html": body
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
    send_email(subject=subject, body=body)
    print("Email sent successfully.")
    time.sleep(60)  # Sleep for 60 seconds (1 minute)
