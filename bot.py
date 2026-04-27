from flask import Flask, request, jsonify
import telebot
import requests
import re
import time

BOT_TOKEN = "8636472190:AAGvZnKxU7klk4oP0z40mdTpldHv2CHu0e8"
PROXY = "15.235.131.237:8080"

# إعداد Proxy لطلبات جيزي
PROXY_DICT = {
    'http': f'http://{PROXY}',
    'https': f'http://{PROXY}'
}

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def is_valid_phone(phone):
    return bool(re.match(r'^07\d{8}$', phone))

def extract_phone(text):
    match = re.search(r'07\d{8}', text)
    return match.group() if match else None

def send_verification_request(phone):
    try:
        converted = "213" + phone[1:]
        url = f"https://apim.djezzy.dz/mobile-api/oauth2/registration?msisdn={converted}&client_id=87pIExRhxBb3_wGsA5eSEfyATloa&scope=smsotp"
        body = '{"consent-agreement":[{"marketing-notifications":false}],"is-consent":true}'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MobileApp/3.0.4"
        }
        response = requests.post(url, data=body, headers=headers, proxies=PROXY_DICT, timeout=30)
        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✨ بوت DZ Connect يعمل!\nأرسل رقمك مثل: 0799999999")

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.strip()
    if text.startswith('/'):
        return
    
    phone = extract_phone(text)
    if not phone:
        bot.reply_to(message, "❌ أرسل رقماً صحيحاً يبدأ بـ 07")
        return
    
    success, status = send_verification_request(phone)
    if success:
        bot.reply_to(message, f"✅ تم إرسال رمز التحقق إلى {phone}\n📲 سيصلك عبر SMS")
    else:
        bot.reply_to(message, f"❌ فشل الإرسال: {status}")

# Webhook endpoint
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == "__main__":
    # إزالة webhook القديم
    bot.remove_webhook()
    time.sleep(1)
    # تعيين webhook جديد (استخدم رابط التطبيق من Render)
    webhook_url = f"https://dzconnectebot.onrender.com/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")
    print("🤖 البوت يعمل...")
    app.run(host='0.0.0.0', port=10000)