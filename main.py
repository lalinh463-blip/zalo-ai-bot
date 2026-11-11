import os
import threading
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from google import genai
import anthropic

app = Flask(__name__)

# Tự động nhận diện các mã kết nối từ cài đặt máy chủ Render
ZALO_TOKEN = os.environ.get("ZALO_BOT_TOKEN", "").strip()
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

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
    payload = {"chat_id": str(chat_id), "text": text[:4000]}
    try:
        res = requests.post(url, json=payload, timeout=15)
        print("Kết quả gửi Zalo:", res.status_code, res.text, flush=True)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}", flush=True)

def handle_message(chat_id, text):
    t_lower = text.lower().strip()

    if "/all" in t_lower:
        q = text[t_lower.find("/all") + 4:].strip() or "Xin chào"
        send_zalo_message(chat_id, f"🤖 ChatGPT:\n{ask_chatgpt(q)}")
        send_zalo_message(chat_id, f"💎 Gemini:\n{ask_gemini(q)}")
        send_zalo_message(chat_id, f"🟣 Claude:\n{ask_claude(q)}")
    elif "/gpt" in t_lower:
        q = text[t_lower.find("/gpt") + 4:].strip() or "Xin chào"
        send_zalo_message(chat_id, f"🤖 ChatGPT:\n{ask_chatgpt(q)}")
    elif "/gemini" in t_lower:
        q = text[t_lower.find("/gemini") + 7:].strip() or "Xin chào"
        send_zalo_message(chat_id, f"💎 Gemini:\n{ask_gemini(q)}")
    elif "/claude" in t_lower:
        q = text[t_lower.find("/claude") + 7:].strip() or "Xin chào"
        send_zalo_message(chat_id, f"🟣 Claude:\n{ask_claude(q)}")

@app.route("/webhook", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        print("Dữ liệu từ Zalo:", data, flush=True)

        msg = data.get("message") or data.get("edited_message") or {}
        if not msg and isinstance(data.get("result"), dict):
            msg = data["result"].get("message") or data["result"]
        if not msg:
            msg = data

        chat_id = (
            msg.get("chat", {}).get("id")
            or msg.get("from", {}).get("id")
            or msg.get("chat_id")
            or data.get("chat_id")
        )
        text = msg.get("text") or data.get("text") or ""

        if chat_id and text:
            threading.Thread(
                target=handle_message,
                args=(str(chat_id), str(text)),
                daemon=True
            ).start()

        return jsonify({"ok": True}), 200
    return "Bot Zalo AI đang hoạt động 24/7!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
