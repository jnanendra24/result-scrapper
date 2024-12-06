from twilio.rest import Client
import os

account_sid = os.environ.get('ACCOUNT_SID')
auth_token = os.environ.get('AUTH_TOKEN')
fromPhone = os.environ.get('FROMPHONE')
toPhone = os.environ.get('TOPHONE')

def sendSMS(body):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    from_=fromPhone,
    body=body,
    to=toPhone
    )
    print(message.sid)