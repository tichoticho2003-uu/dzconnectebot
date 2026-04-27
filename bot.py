# ==========================================
# بوت DZ Connect - إرسال طلب رمز التحقق من جيزي
# ==========================================

import telebot
import requests
import time
import re
import logging
from telebot import apihelper

# ==========================================
# إعدادات البوت
# ==========================================

BOT_TOKEN = "8636472190:AAEc2lyFoClia1fUjLh7RzTMtYMeffXzYVE"
PROXY = "15.235.131.237:8080"  # Proxy واحد

# إعداد الـ Proxy لاتصالات البوت مع تلغرام
if PROXY:
    apihelper.proxy = {'http': f'http://{PROXY}', 'https': f'http://{PROXY}'}

# إعداد الـ Proxy لطلبات requests إلى API جيزي
PROXY_DICT = {
    'http': f'http://{PROXY}',
    'https': f'http://{PROXY}'
} if PROXY else None

# إعداد التسجيل (log) لمراقبة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# دوال مساعدة
# ==========================================

def is_valid_phone(phone):
    """التحقق من صحة رقم هاتف جزائري (10 أرقام تبدأ بـ 07)"""
    return bool(re.match(r'^07\d{8}$', phone))

def extract_phone(text):
    """استخراج أول رقم هاتف من النص"""
    match = re.search(r'07\d{8}', text)
    return match.group() if match else None

def send_verification_request(phone):
    """
    إرسال طلب إلى API جيزي لإرسال رمز التحقق عبر SMS.
    تعيد الدالة (نجاح, رمز_الحالة_أو_الخطأ, نص_الاستجابة)
    """
    try:
        # تحويل الرقم إلى صيغة دولية
        converted = "213" + phone[1:]  # 213xxxxxxxxx
        url = f"https://apim.djezzy.dz/mobile-api/oauth2/registration?msisdn={converted}&client_id=87pIExRhxBb3_wGsA5eSEfyATloa&scope=smsotp"
        body = '{"consent-agreement":[{"marketing-notifications":false}],"is-consent":true}'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MobileApp/3.0.4"
        }
        
        # إرسال الطلب عبر الـ Proxy إن وُجد
        if PROXY_DICT:
            response = requests.post(url, data=body, headers=headers, proxies=PROXY_DICT, timeout=30)
        else:
            response = requests.post(url, data=body, headers=headers, timeout=30)
        
        # تسجيل الاستجابة للتصحيح
        logger.info(f"API response for {phone}: status {response.status_code}, body: {response.text[:200]}")
        
        # النجاح إذا كان الرد 200 (أحياناً 201 أو 204)
        success = response.status_code in [200, 201, 204]
        return success, response.status_code, response.text
    except Exception as e:
        logger.error(f"Request error for {phone}: {str(e)}")
        return False, str(e), ""

# ==========================================
# أوامر البوت
# ==========================================

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(message,
        "✨ *مرحباً بك في بوت DZ Connect* ✨\n\n"
        "📱 *لطلب إرسال رمز التحقق:*\n"
        "🔹 أرسل رقمك مباشرة مثل: `0799999999`\n"
        "🔹 أو استخدم الأمر: `/send 0799999999`\n\n"
        "🔹 *بعد وصول الرمز عبر SMS* لا يحتاج البوت للتحقق منه، يمكنك استخدامه في التطبيق الأصلي.\n\n"
        "📌 *الأوامر المتاحة:*\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/ping - اختبار الاتصال\n"
        "/proxy - عرض الـ Proxy المستخدم\n"
        "/testproxy - اختبار صلاحية الـ Proxy\n"
        "/status - حالة البوت",
        parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.reply_to(message,
        "📖 *قائمة الأوامر:*\n\n"
        "/start - بدء البوت\n"
        "/send `0799999999` - طلب إرسال رمز التحقق لهذا الرقم\n"
        "/ping - قياس زمن استجابة البوت\n"
        "/proxy - عرض الـ Proxy الحالي\n"
        "/testproxy - اختبار إذا كان الـ Proxy يعمل\n"
        "/status - عرض إحصائيات البوت\n\n"
        "⚠️ *ملاحظة:* هذا البوت يطلب فقط إرسال الرمز إلى هاتفك. الرمز يصل عبر SMS من جيزي، والبوت لا يستطيع رؤيته ولا التحقق منه.",
        parse_mode='Markdown')

@bot.message_handler(commands=['send'])
def cmd_send(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message,
            "❌ يرجى إدخال الرقم\nمثال: `/send 0799999999`",
            parse_mode='Markdown')
        return
    
    phone = parts[1].strip()
    # معالجة الطلب (نفس دالة معالجة الأرقام)
    process_send_code(message, phone)

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    start = time.time()
    msg = bot.reply_to(message, "🏓 Pong!")
    end = time.time()
    latency = (end - start) * 1000
    bot.edit_message_text(f"🏓 Pong! ⏱️ {latency:.0f}ms",
                          chat_id=message.chat.id,
                          message_id=msg.message_id)

@bot.message_handler(commands=['proxy'])
def cmd_proxy(message):
    if PROXY:
        bot.reply_to(message, f"🌐 *الـ Proxy المستخدم:*\n`{PROXY}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "🌐 *لا يتم استخدام Proxy*", parse_mode='Markdown')

@bot.message_handler(commands=['testproxy'])
def cmd_testproxy(message):
    """اختبار ما إذا كان الـ Proxy يسمح بالاتصال بالإنترنت"""
    if not PROXY_DICT:
        bot.reply_to(message, "❌ لا يوجد Proxy مُحدد.", parse_mode='Markdown')
        return
    
    msg = bot.reply_to(message, "🔄 *جارٍ اختبار الـ Proxy ...*", parse_mode='Markdown')
    try:
        # محاولة الاتصال بـ ipify عبر الـ Proxy
        response = requests.get('https://api.ipify.org?format=json', proxies=PROXY_DICT, timeout=15)
        if response.status_code == 200:
            ip = response.json().get('ip', 'unknown')
            bot.edit_message_text(f"✅ *الـ Proxy يعمل*\n🌐 عنوان IP الظاهر: `{ip}`",
                                  chat_id=message.chat.id,
                                  message_id=msg.message_id,
                                  parse_mode='Markdown')
        else:
            bot.edit_message_text(f"❌ *الـ Proxy لا يعمل*\nرمز الخطأ: {response.status_code}",
                                  chat_id=message.chat.id,
                                  message_id=msg.message_id,
                                  parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ *فشل الاتصال عبر Proxy*\nالخطأ: `{str(e)[:100]}`",
                              chat_id=message.chat.id,
                              message_id=msg.message_id,
                              parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def cmd_status(message):
    bot.reply_to(message,
        f"📊 *حالة البوت*\n\n"
        f"✅ يعمل بشكل طبيعي\n"
        f"🌐 Proxy: `{PROXY if PROXY else 'لا يوجد'}`\n"
        f"🤖 البوت: DZ Connect\n"
        f"📅 آخر تشغيل: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode='Markdown')

# ==========================================
# معالجة طلب إرسال الرمز
# ==========================================

def process_send_code(message, phone):
    """إرسال طلب رمز التحقق إلى API جيزي وإعلام المستخدم"""
    
    # التحقق من صحة الرقم
    if not is_valid_phone(phone):
        bot.reply_to(message,
            "❌ *رقم غير صحيح*\n"
            "الرقم يجب أن يكون 10 أرقام ويبدأ بـ 07 (مثال: `0799999999`).",
            parse_mode='Markdown')
        return
    
    # رسالة انتظار
    msg = bot.reply_to(message, "🔄 *جاري إرسال طلب رمز التحقق ...*", parse_mode='Markdown')
    
    # محاولة إرسال الطلب
    success, status_code_or_error, response_text = send_verification_request(phone)
    
    if success:
        bot.edit_message_text(
            f"✅ *تم إرسال رمز التحقق بنجاح إلى هاتفك* 📱\n\n"
            f"📞 الرقم: `{phone}`\n"
            f"🔐 سيصلك رمز عبر **SMS** خلال دقائق قليلة.\n\n"
            f"⚠️ *ملاحظة:* هذا البوت لا يستطيع قراءة الرمز، استخدمه مباشرة في تطبيق My DZ Connect.\n\n"
            f"📌 إذا لم يصلك الرمز، حاول مرة أخرى بعد 5 دقائق.",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='Markdown'
        )
        logger.info(f"رمز التحقق طلب بنجاح للرقم {phone}")
    else:
        # فشل الطلب
        error_msg = f"❌ *فشل إرسال الرمز*\n\n"
        if isinstance(status_code_or_error, int):
            error_msg += f"🔴 رمز الخطأ من الخادم: `{status_code_or_error}`\n"
            if status_code_or_error == 400:
                error_msg += "الطلب غير صحيح (قد يكون الرقم غير مسجل في جيزي؟)\n"
            elif status_code_or_error == 403:
                error_msg += "حظر أو رفض من الخادم (قد يكون الـ Proxy محظوراً).\n"
            elif status_code_or_error == 429:
                error_msg += "تم إرسال العديد من الطلبات. انتظر قليلاً.\n"
            else:
                error_msg += f"تفاصيل الاستجابة: `{response_text[:100]}`\n"
        else:
            error_msg += f"⚠️ خطأ في الاتصال: `{status_code_or_error}`\n"
        
        error_msg += f"\n💡 *اقتراحات:*\n"
        error_msg += f"- تأكد من صحة الرقم.\n"
        error_msg += f"- جرب الأمر `/testproxy` لاختبار الـ Proxy.\n"
        error_msg += f"- إذا استمرت المشكلة، قد يكون الـ Proxy غير صالح أو API جيزي لا يستجيب."
        
        bot.edit_message_text(error_msg,
                              chat_id=message.chat.id,
                              message_id=msg.message_id,
                              parse_mode='Markdown')
        logger.warning(f"فشل طلب الرمز للرقم {phone}: {status_code_or_error}")

# ==========================================
# معالجة الرسائل النصية (الأرقام مباشرة)
# ==========================================

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.strip()
    
    # تجاهل الأوامر المبدوءة بـ /
    if text.startswith('/'):
        return
    
    # محاولة استخراج رقم هاتف
    phone = extract_phone(text)
    if phone:
        process_send_code(message, phone)
    else:
        bot.reply_to(message,
            "❌ *لم يتم التعرف على رقم صحيح*\n\n"
            "📱 أرسل رقماً مكوناً من 10 أرقام يبدأ بـ `07`\n"
            "📌 *مثال:* `0799999999`\n\n"
            "🔹 أو استخدم الأمر: `/send 0799999999`\n"
            "🔹 وللمساعدة: `/help`",
            parse_mode='Markdown')

# ==========================================
# تشغيل البوت
# ==========================================

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 بوت DZ Connect يعمل...")
    print(f"🌐 Proxy المستخدم: {PROXY if PROXY else 'بدون Proxy'}")
    print("📱 أرسل رقمك مثل: 0799999999")
    print("=" * 60)
    
    # إزالة الويب هوك (للتأكد من عمل polling)
    bot.remove_webhook()
    
    # بدء الاستماع للمستخدمين
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")
        print(f"خطأ فادح: {e}")