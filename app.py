import os
import time
import json
import requests
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
import smtplib
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS for all routes and ensure OPTIONS requests are handled
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.before_request
def handle_preflight():
    """Handles CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        return response, 200

GOOGLE_SHEETS_API_URL = "https://script.google.com/macros/s/AKfycbzFjfh8kZNdrJWVRKLRV4SYhim_3qgod_jtcich3VmT0bcz9D5c92DBRcAaba5UKf6E/exec"

def get_products_from_sheets():
    response = requests.post(GOOGLE_SHEETS_API_URL, json={"action": "get_products"})
    return response.json()

def add_product_to_sheets(url, target_price, email):
    data = {"action": "add_product", "url": url, "targetPrice": target_price, "email": email}
    requests.post(GOOGLE_SHEETS_API_URL, json=data)

def take_screenshot(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    driver.get(url)
    time.sleep(5)
    screenshot_path = "screenshot.png"
    driver.save_screenshot(screenshot_path)
    driver.quit()
    return screenshot_path

def extract_price(image_path):
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image)

    import re
    price_matches = re.findall(r'\$\d+(?:\.\d{1,2})?', extracted_text)

    return price_matches[0] if price_matches else "Price not found"

def send_email(price, url, email):
    sender_email = "your-email@gmail.com"
    sender_password = "your-app-password"

    subject = "Price Drop Alert!"
    body = f"Good news! The product price is now {price}.\nCheck it here: {url}"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, email, f"Subject: {subject}\n\n{body}")
    server.quit()

@app.route("/", methods=["GET"])
def home():
    return "Backend is working!", 200

@app.route("/track-price", methods=["POST"])
def track_price():
    data = request.get_json()
    return jsonify({"message": "API is working!", "data": data})


def check_all_prices():
    products = get_products_from_sheets()

    for product in products:
        url = product["url"]
        target_price = float(product["targetPrice"])
        email = product["email"]

        screenshot = take_screenshot(url)
        detected_price = extract_price(screenshot)

        print(f"Checked {url} - Detected Price: {detected_price}")

        if detected_price != "Price not found" and float(detected_price.replace("$", "")) <= target_price:
            send_email(detected_price, url, email)
            print(f"🔔 Price Drop Alert Sent to {email} for {url}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get port from Render, default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
