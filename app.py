import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from twilio.rest import Client
import pywhatkit as pwk
import time
import logging
import requests
import base64
import openai
import pythoncom
from gtts import gTTS
import os
from bs4 import BeautifulSoup
import geocoder
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import urllib.parse

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define your Twilio account credentials
account_sid = "ACf09b33625b03d3213941c2090effebb3"
auth_token = "9f5111317550bf6ab98f2e6701d86c58"
client = Client(account_sid, auth_token)

# Define the sender phone number
sender_no = "+12086035252"
twiml_url = "http://demo.twilio.com/docs/voice.xml"

# Define your SerpApi API key
API_KEY = "7711d6a8f06fc249b8749a2aafba99055da276a106b197cab3784d204e00a53a"

openai.api_key = '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'

@app.route('/')
def index():
    return app.send_static_file('projects.html')

@app.route('/send_whatsapp_message', methods=['POST'])
def send_whatsapp_message():
    data = request.json
    phone_num = data.get('phone_num')
    message = data.get('message')
    
    try:
        time.sleep(3)
        pwk.sendwhatmsg_instantly(phone_num, message)
        logging.info(f"Message sent to {phone_num}")
        return jsonify({"status": "success", "message": "Message sent successfully!"})
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/send_twilio_message', methods=['POST'])
def send_twilio_message():
    data = request.json
    recipient_no = data.get('phone_num')
    message_body = data.get('message')

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    encoded_auth_token = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "From": sender_no,
        "To": recipient_no,
        "Body": message_body
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 201:
        return jsonify({"status": "success", "message": "Message sent successfully!"})
    else:
        return jsonify({"status": "error", "message": response.text}), response.status_code

@app.route('/make_twilio_call', methods=['POST'])
def make_twilio_call():
    data = request.json
    to_phone_number = data.get('phone_num')
    
    try:
        call = client.calls.create(
            from_=sender_no,
            to=to_phone_number,
            url=twiml_url
        )
        logging.info(f"Call initiated with SID: {call.sid}")
        return jsonify({"status": "success", "message": "Call initiated successfully!", "call_sid": call.sid})
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    sender_email = "deepikaakanwar@gmail.com"
    receiver_email = data.get('receiver_email')
    password = "agptblpkvsaxpnuu"
    subject = data.get('subject')
    body = data.get('body')

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        logging.info(f"Email sent to {receiver_email}")
        return jsonify({"status": "success", "message": "Email sent successfully!"})
    except Exception as e:
        logging.error(f"Failed to send email. Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        server.quit()

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({"status": "error", "message": "Text is required"}), 400
    
    try:
        # Create a speech object
        speech = gTTS(text=text, lang='en', slow=False)
        file_path = "text.mp3"
        
        # Save the speech to an MP3 file
        speech.save(file_path)
        
        # Return the file as a response
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Failed to generate speech. Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_location', methods=['POST'])
def get_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()
        data = response.json()

        location = data.get('loc').split(',')
        address = f"{data.get('city')}, {data.get('region')}, {data.get('country')}"

        return jsonify({"status": "success", "coordinates": location, "address": address})
    except Exception as e:
        logging.error(f"Failed to get location. Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_volume', methods=['POST'])
def set_volume():
    try:
        data = request.json
        volume_level = data.get('volume_level')

        if volume_level is None:
            return jsonify({'status': 'error', 'message': 'Volume level is required'}), 400

        try:
            volume_level = int(volume_level)
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Volume level must be an integer'}), 400

        if not (0 <= volume_level <= 100):
            return jsonify({'status': 'error', 'message': 'Volume level must be between 0 and 100'}), 400

        pythoncom.CoInitialize()

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(volume_level / 100.0, None)

        pythoncom.CoUninitialize()

        return jsonify({'status': 'success', 'message': f'Volume set to {volume_level}'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/scrape_google', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = scrape_google(query)
    
    if 'error' in results:
        return jsonify({"error": results['error']}), 500
    else:
        return jsonify(results)

def scrape_google(query):
    query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for result in soup.find_all('div', class_='g')[:5]:
            title = result.find('h3').text if result.find('h3') else 'No title'
            link = result.find('a')['href'] if result.find('a') else 'No link'
            results.append({"title": title, "link": link})
    
        return results
    
    except Exception as e:
        return {"error": str(e)}
    
@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"status": "error", "message": "Message is required"}), 400

    try:
        # Send user input to OpenAI's GPT-3 API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            user=session_id,
        )

        # Extract the reply from the response
        chatgpt_reply = response['choices'][0]['message']['content']

        # Log the interaction
        logging.info(f"User: {user_message}")
        logging.info(f"ChatGPT: {chatgpt_reply}")

        return jsonify({"status": "success", "reply": chatgpt_reply})
    except Exception as e:
        logging.error(f"Error in ChatGPT API call: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == '__main__':
    app.run(port=5002)
