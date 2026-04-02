import telebot
import os
import requests
from telebot import types
import threading
import time
from flask import Flask
from threading import Thread

# --- نظام الحفاظ على النشاط (Flask) لـ Koyeb ---
app = Flask('')
@app.route('/')
def home(): 
    return "StudyHero is Alive and Running! 🚀"

def run():
    # Koyeb بيستخدم بورت 8080 تلقائياً
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات البوت والمفاتيح المخفية ---
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في الإعدادات!")

# جلب الـ 12 مفتاح من البيئة
GROQ_KEYS = []
for i in range(1, 13):
    key = os.environ.get(f'GROQ_KEY_{i}')
    if key:
        GROQ_KEYS.append(key)

if not GROQ_KEYS:
    print("⚠️ تحذير: لم يتم العثور على أي مفاتيح GROQ_KEY!")

bot = telebot.TeleBot(TOKEN)
key_lock = threading.Lock()
current_key_index = 0

# --- وظيفة جلب الرد من الذكاء الاصطناعي ---
def get_ai_response(prompt):
    global current_key_index
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # محاولة لفة كاملة على كل المفاتيح لو حصل ضغط
    for _ in range(len(GROQ_KEYS) * 2):
        with key_lock:
            if not GROQ_KEYS: return "❌ لا توجد مفاتيح متوفرة."
            key = GROQ_KEYS[current_key_index]
            
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            elif response.status_code in [401, 429]: # مفتاح خلص أو باظ
                with key_lock:
                    current_key_index = (current_key_index + 1) % len(GROQ_KEYS)
                    print(f"🔄 التبديل للمفتاح رقم: {current_key_index + 1}")
        except Exception as e:
            time.sleep(1)
            
    return "❌ المحركات مشغولة حالياً، جرب كمان شوية."

# --- مثال لأمر بسيط (تقدر تضيف باقي أوامرك هنا) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في StudyHero AI! 🎓\nأنا جاهز لمساعدتك في المذاكرة.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    response = get_ai_response(message.text)
    bot.reply_to(message, response)

# --- تشغيل البوت ---
if __name__ == "__main__":
    keep_alive() # تشغيل السيرفر الوهمي
    print("🚀 البوت بدأ العمل بنظام الحماية...")
    bot.infinity_polling()
