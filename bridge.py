import os
import json
import time
import requests
import re
from bs4 import BeautifulSoup

# --- تنظیمات ---
CHANNEL_URL = "https://eitaa.com/basij_iasbs"
STATE_FILE = "state.json"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHANNEL")

if not BOT_TOKEN or not TG_CHAT_ID:
    print("ERROR: Secrets not found.")
    exit(1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def get_last_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_id", 0)
    return None

def save_state(last_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_id": last_id}, f)

def send_to_telegram(text, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": TG_CHAT_ID, "caption": text[:1024], "parse_mode": "HTML"}
        try:
            img_data = requests.get(image_url, headers=HEADERS, timeout=30).content
            files = {"photo": ("image.jpg", img_data)}
            r = requests.post(url, data=payload, files=files, timeout=30)
            if r.status_code == 200:
                print(f"Photo sent successfully.")
                return
            else:
                print(f"Failed to send photo: {r.text}")
        except Exception as e:
            print(f"Error sending photo: {e}")
    
    # Fallback to text message
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            print(f"Message sent successfully.")
        else:
            print(f"Failed to send message: {r.text}")
    except Exception as e:
        print(f"Error sending message: {e}")

def process_channel():
    print(f"Fetching {CHANNEL_URL}...")
    try:
        r = requests.get(CHANNEL_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch channel: {e}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    
    # پیدا کردن پست‌ها با استفاده از data-post
    posts = soup.find_all(attrs={"data-post": True})
    print(f"Found {len(posts)} posts on the page.")
    
    if not posts:
        print("WARNING: No posts found.")
        return

    last_saved_id = get_last_state()
    new_last_id = last_saved_id if last_saved_id is not None else 0
    all_posts = []

    for post in posts:
        post_id_attr = post.get("data-post")
        if not post_id_attr: continue
        try:
            post_id = int(post_id_attr.split("/")[-1])
            all_posts.append((post_id, post))
        except ValueError:
            continue

    if not all_posts:
        print("No valid post IDs found.")
        return

    # اگر اولین بار است
    if last_saved_id is None:
        max_id = max(p[0] for p in all_posts)
        save_state(max_id)
        print(f"FIRST RUN: Saved max post ID {max_id}. No posts sent.")
        return

    all_posts.sort(key=lambda x: x[0])
    print(f"Last saved ID: {last_saved_id}")

    for post_id, post in all_posts:
        if post_id <= last_saved_id:
            continue

        print(f"Processing new post {post_id}...")

        # استخراج متن
        text_div = post.find("div", class_="etme_widget_message_text")
        text = text_div.get_text(separator="\n", strip=True) if text_div else ""

        # بررسی فایل ضمیمه
        doc_div = post.find("div", class_="etme_widget_message_document_title")
        if doc_div:
            doc_name = doc_div.get_text(strip=True)
            text += f"\n\n📎 <i>این پست در ایتا دارای فایل ضمیمه ({doc_name}) است که منتقل نشده.</i>"

        # استخراج عکس
        image_url = None
        photo_div = post.find("a", class_="etme_widget_message_photo_wrap")
        if photo_div and photo_div.get("style"):
            match = re.search(r"url\('(.+?)'\)", photo_div["style"])
            if match:
                image_url = match.group(1)

        if not text and not image_url:
            print(f"Post {post_id} empty, skipping.")
            new_last_id = post_id
            continue

        if not text:
            text = "📷 [عکس]"
        
        send_to_telegram(text, image_url)
        new_last_id = post_id
        time.sleep(2)

    if new_last_id > (last_saved_id or 0):
        save_state(new_last_id)
        print(f"State updated to {new_last_id}")

if __name__ == "__main__":
    process_channel()
