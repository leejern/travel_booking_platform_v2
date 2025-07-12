import json 
import requests
from decouple import config


# This function sends an SMS to a given phone number with a given message.
def send_message(phone_number, message): 
    # we send an sms get the response from the TextSMS server 
    # API endpoint
    url = "https://sms.textsms.co.ke/api/services/sendsms/"

    # Prepare the payload
    payload = {
        "apikey": config('TEXTSMS_API_KEY'),
        "partnerID": config('TEXTSMS_PERTNER_ID'),
        "message": message,
        "shortcode": config('TEXTSMS_SHORTCODE'),
        "mobile": phone_number,
    }

    # Convert payload to JSON
    json_payload = json.dumps(payload)

    # Set the headers
    headers = {
        "Content-Type": "application/json"
    }

    # Send the POST request 
    response = requests.post(url, data=json_payload, headers=headers)
    print(response) 

    return response