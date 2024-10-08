from flask import Flask, request
import threading
import RPi.GPIO as GPIO
import time
import requests
import sqlite3
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

LED_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/receive', methods=['POST'])
def receive():
    data = request.json
    if data and data.get("message"):
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED_PIN, GPIO.LOW)

        message_id = str(uuid.uuid4())
        message = data.get("message")
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (id, message) VALUES (?, ?)', (message_id, message))
        conn.commit()
        conn.close()

        print("\n===========================")
        print("📥 Data Received")
        print(f"ID: {message_id}")
        print(f"Message: {message}")
        print("Timestamp: Saved in Database")
        print("===========================\n")

        return "Data received and stored!", 200
    return "Invalid data", 400

def run_server():
    app.run(host='0.0.0.0', port=5000)

def sender(target_ip):
    while True:
        try:
            url = f'http://{target_ip}:5000/receive'
            message = {"message": "Hello from sender!"}
            response = requests.post(url, json=message)
            print("\n===========================")
            print("📤 Data Sent")
            print(f"Message: {message['message']}")
            print(f"Response Status Code: {response.status_code}")
            print("===========================\n")
        except Exception as e:
            print(f"Error sending data: {e}")
        time.sleep(5)

TARGET_IP = os.getenv("TARGET_IP")

server_thread = threading.Thread(target=run_server)
sender_thread = threading.Thread(target=sender, args=(TARGET_IP,))

server_thread.start()
sender_thread.start()

server_thread.join()
sender_thread.join()

GPIO.cleanup()