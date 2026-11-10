import os
import time
import threading
import requests
from flask import Flask
from openai import OpenAI
from google import genai
import anthropic

app = Flask(__name__)

# Tự động nhận diện các mã kết nối từ cài đặt máy chủ Render
ZALO_TOKEN = os.environ.get("ZALO_BOT_TOKEN", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

ZALO_API_URL = f"https://bot-api.zapps.me/bot{ZALO_TOKEN}"

def ask_chatgpt(prompt):
    if not OPENAI_KEY:
        return "⚠️ Chưa kết nối API ChatGPT."
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Lỗi ChatGPT: {e}"

def ask_gemini(prompt):
    if not GEMINI_KEY:
        return "⚠️ Chưa kết nối API Gemini."
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"Lỗi Gemini: {e}"

def ask_claude(prompt):
    if not CLAUDE_KEY:
        return "⚠️ Chưa kết nối API Claude."
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_KEY)
        res = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text
    except Exception as e:
        return f"Lỗi Claude: {e}"

def send_zalo_message(chat_id, text):
    url = f"{ZALO_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text[:4000]}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

def handle_message(chat_id, text):
    t_lower = text.lower().strip()
    
    # Gõ "/all câu hỏi" để cả 3 AI cùng trả lời
    if t_lower.startswith("/all "):
        q = text[5:].strip()
        send_zalo_message(chat_id, f"🤖 ChatGPT:\n{ask_chatgpt(q)}")
        send_zalo_message(chat_id, f"💎 Gemini:\n{ask_gemini(q)}")
        send_zalo_message(chat_id, f"🟣 Claude:\n{ask_claude(q)}")
    # Gõ "/gpt câu hỏi" để gọi riêng ChatGPT
    elif t_lower.startswith("/gpt "):
        send_zalo_message(chat_id, f"🤖 ChatGPT:\n{ask_chatgpt(text[5:].strip())}")
    # Gõ "/gemini câu hỏi" để gọi riêng Gemini
    elif t_lower.startswith("/gemini "):
        send_zalo_message(chat_id, f"💎 Gemini:\n{ask_gemini(text[8:].strip())}")
    # Gõ "/claude câu hỏi" để gọi riêng Claude
    elif t_lower.startswith("/claude "):
        send_zalo_message(chat_id, f"🟣 Claude:\n{ask_claude(text[8:].strip())}")

def polling_loop():
    offset = 0
    while True:
        if not ZALO_TOKEN:
            time.sleep(10)
            continue
        try:
            url = f"{ZALO_API_URL}/getUpdates"
            resp = requests.get(url, params={"offset": offset, "timeout": 25}, timeout=30).json()
            if resp.get("ok"):
                for item in resp.get("result", []):
                    offset = item["update_id"] + 1
                    msg = item.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "")
                    if chat_id and text:
                        handle_message(chat_id, text)
        except Exception:
            time.sleep(5)
        time.sleep(1)

@app.route("/")
def home():
    return "Bot Zalo AI đang hoạt động 24/7!"

if __name__ == "__main__":
    threading.Thread(target=polling_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
