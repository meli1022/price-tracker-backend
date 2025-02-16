from flask import Flask, request, jsonify
import time
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
import smtplib

app = Flask(__name__)

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

@app.route("/track-price", methods=["POST"])
def track_price():
    data = request.get_json()
    url = data["url"]
    target_price = float(data["targetPrice"])
    email = data["email"]

    screenshot = take_screenshot(url)
    detected_price = extract_price(screenshot)

    if detected_price != "Price not found" and float(detected_price.replace("$", "")) <= target_price:
        send_email(detected_price, url, email)
        return jsonify({"message": "🔔 Price Drop Alert! Check your email.", "price": detected_price})
    
    return jsonify({"message": "Tracking started! We'll notify you when the price drops.", "price": detected_price})

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get port from Render, default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)

