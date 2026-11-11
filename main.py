import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Lấy các biến môi trường cấu hình trên Render
ZALO_TOKEN = os.environ.get("ZALO_BOT_TOKEN", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

def ask_gemini(prompt):
    if not GEMINI_KEY:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY trên Render."
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"⚠️ Lỗi xử lý Gemini: {str(e)}"

def send_zalo_message(chat_id, text):
    if not ZALO_TOKEN:
        print("Chưa có ZALO_BOT_TOKEN!")
        return
    url = f"https://bot.zaloplatforms.com/v1/bot{ZALO_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        print("Zalo response:", res.status_code, res.text)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn Zalo: {e}")

@app.route("/", methods=["GET"])
def home():
    return "Bot Zalo AI đang hoạt động 24/7!"

@app.route("/webhook", methods=["POST", "GET"])
@app.route("/", methods=["POST"])
def webhook():
    if request.method == "GET":
        return "Webhook endpoint sẵn sàng nhận dữ liệu từ Zalo!"
    
    data = request.get_json(silent=True) or {}
    print("Dữ liệu nhận từ Zalo:", data)
    
    # Bóc tách thông tin tin nhắn từ cấu trúc Webhook của Zalo
    message = data.get("message") or data.get("event", {}) or data
    chat_info = message.get("chat", {})
    chat_id = chat_info.get("id") or message.get("chat_id") or data.get("chat_id")
    text = (message.get("text") or "").strip()
    
    if chat_id and text:
        t_lower = text.lower()
        if t_lower.startswith("/gemini"):
            user_prompt = text[7:].strip()
            if not user_prompt:
                reply = "💎 Gemini: Bạn vui lòng nhập câu hỏi sau lệnh /gemini nhé!"
            else:
                reply = f"💎 Gemini:\n{ask_gemini(user_prompt)}"
            send_zalo_message(chat_id, reply)
            
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
