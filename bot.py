import os
import telebot
from telebot.types import Message, Update, InlineKeyboardMarkup, InlineKeyboardButton
from pdf2docx import Converter
import subprocess
from flask import Flask, request
import json

API_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(API_TOKEN)

# Flask application for Webhook support
app = Flask(__name__)

MAX_SIZE = 10 * 1024 * 1024  # 10 MB
DB_FILE = 'users_db.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
        
def get_user(user_id):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {'conversions_left': 1, 'referred_by': None, 'referrals': 0}
        save_db(db)
    return db[user_id_str]

def decrease_conversion(user_id):
    db = load_db()
    user_id_str = str(user_id)
    if db[user_id_str]['conversions_left'] > 0:
        db[user_id_str]['conversions_left'] -= 1
        save_db(db)
        return True
    return False

def add_referral(new_user_id, referrer_id):
    db = load_db()
    new_user_id_str = str(new_user_id)
    referrer_id_str = str(referrer_id)
    
    if new_user_id_str not in db:
        db[new_user_id_str] = {'conversions_left': 1, 'referred_by': None, 'referrals': 0}
    
    if referrer_id_str in db and db[new_user_id_str]['referred_by'] is None and new_user_id_str != referrer_id_str:
        db[new_user_id_str]['referred_by'] = referrer_id_str
        db[referrer_id_str]['referrals'] += 1
        db[referrer_id_str]['conversions_left'] += 1
        save_db(db)
        return True
    save_db(db)
    return False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    user_id = message.from_user.id
    
    # Check if started with a referral parameter (e.g. /start 123456789)
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        try:
            if add_referral(user_id, int(referrer_id)):
                bot.send_message(int(referrer_id), "🎉 قام شخص جديد باستخدام البوت عن طريق رابطك! لقد حصلت على **تحويل إضافي مجاني** 🎁", parse_mode="Markdown")
        except ValueError:
            pass # Ignore invalid referrer ID
            
    user_data = get_user(user_id)
    bot_info = bot.get_me()
    bot_username = bot_info.username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"

    welcome_text = (
        f"مرحباً بك في بوت تحويل الملفات! 🔄\n\n"
        f"يمكنني تحويل الملفات بين صيغتي PDF و DOCX.\n\n"
        f"🎁 **رصيدك الحالي:** {user_data['conversions_left']} عملية تحويل مجانية.\n\n"
        f"طريقة الاستخدام:\n"
        f"أرسل لي ملف بصيغة PDF أو DOCX لبدء التحويل.\n\n"
        f"💡 **كيف تحصل على تحويلات إضافية مجاناً؟**\n"
        f"شارك الرابط الخاص بك أدناه مع أصدقائك. كل شخص يستخدم الرابط الخاص بك، ستحصل أنت وهو على **تحويل إضافي مجاني!**\n\n"
        f"🔗 رابط الدعوة الخاص بك:\n{invite_link}"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['document'])
def handle_docs(message: Message):
    if message.document.file_size > MAX_SIZE:
        bot.reply_to(message, "عذراً، حجم الملف يتجاوز 10 ميجابايت. ❌")
        return

    file_name = message.document.file_name
    base_name, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if ext not in ['.pdf', '.docx']:
        bot.reply_to(message, "عذراً، أنا أدعم فقط ملفات PDF و DOCX. ❌")
        return
        
    user_id = message.from_user.id
    user_data = get_user(user_id)
    if user_data['conversions_left'] <= 0:
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.reply_to(message, f"❌ رصيدك من التحويلات المجانية قد نفد.\n\nللحصول على المزيد من التحويلات، شارك رابط الدعوة الخاص بك مع أصدقائك:\n{invite_link}")
        return

    markup = InlineKeyboardMarkup()
    if ext == '.pdf':
        btn = InlineKeyboardButton("تحويل إلى Word (DOCX) 📝", callback_data="convertDOCX")
        markup.add(btn)
    elif ext == '.docx':
        btn = InlineKeyboardButton("تحويل إلى PDF 📄", callback_data="convertPDF")
        markup.add(btn)
        
    bot.reply_to(message, f"تم استلام الملف: {file_name}\nالرجاء الضغط على الزر أدناه لبدء التحويل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['convertDOCX', 'convertPDF'])
def callback_conversion(call):
    bot.answer_callback_query(call.id)
    
    original_msg = call.message.reply_to_message
    if not original_msg or not original_msg.document:
        bot.edit_message_text("تعذر العثور على الملف الأصلي. الرجاء إرساله مرة أخرى.", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id)
        return
        
    user_id = call.from_user.id
    if not decrease_conversion(user_id):
        bot.edit_message_text("❌ رصيدك مجاني قد نفد. أرسل /start لمعرفة كيفية الحصول على المزيد.", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id)
        return
        
    doc = original_msg.document
    file_name = doc.file_name
    base_name, ext = os.path.splitext(file_name)
    ext = ext.lower()

    bot.edit_message_text("جاري تنزيل الملف... ⏳", 
                          chat_id=call.message.chat.id, 
                          message_id=call.message.message_id)

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if ext == '.pdf' and call.data == 'convertDOCX':
            bot.edit_message_text("جاري تحويل الملف من PDF إلى DOCX... ⏳\n*(قد يستغرق بعض الوقت للملفات الكبيرة)*", 
                                  chat_id=call.message.chat.id, 
                                  message_id=call.message.message_id,
                                  parse_mode="Markdown")
            
            pdf_path = f"{base_name}.pdf"
            docx_path = f"{base_name}.docx"
            
            with open(pdf_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            try:
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()
                
                bot.edit_message_text("جاري إرسال الملف... 📤", 
                                      chat_id=call.message.chat.id, 
                                      message_id=call.message.message_id)
                with open(docx_path, 'rb') as doc_file:
                    bot.send_document(call.message.chat.id, doc_file, reply_to_message_id=original_msg.message_id)
                
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception as conv_err:
                print(f"PDF2DOCX Conversion Error: {conv_err}")
                bot.edit_message_text(f"حدث خطأ داخلي أثناء تحويل هذا الـ PDF المعقد. ❌", 
                                      chat_id=call.message.chat.id, 
                                      message_id=call.message.message_id)
            finally:
                if os.path.exists(pdf_path): os.remove(pdf_path)
                if os.path.exists(docx_path): os.remove(docx_path)
                
        elif ext == '.docx' and call.data == 'convertPDF':
            bot.edit_message_text("جاري تحويل الملف من DOCX إلى PDF... ⏳", 
                                  chat_id=call.message.chat.id, 
                                  message_id=call.message.message_id)
            
            docx_path = f"{base_name}.docx"
            pdf_path = f"{base_name}.pdf"
            
            with open(docx_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            try:
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path], check=True)
                
                bot.edit_message_text("جاري إرسال الملف... 📤", 
                                      chat_id=call.message.chat.id, 
                                      message_id=call.message.message_id)
                with open(pdf_path, 'rb') as pdf_file:
                    bot.send_document(call.message.chat.id, pdf_file, reply_to_message_id=original_msg.message_id)

                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception as e:
                 bot.edit_message_text("حدث خطأ في LibreOffice. ❌", 
                                      chat_id=call.message.chat.id, 
                                      message_id=call.message.message_id)
                 print(f"Libreoffice Error: {e}")
            finally:
                if os.path.exists(docx_path): os.remove(docx_path)
                if os.path.exists(pdf_path): os.remove(pdf_path)
            
    except Exception as e:
        bot.edit_message_text("حدث خطأ أثناء معالجة الملف. ❌", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id)
        print(f"Error: {e}")

# Webhook routes
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Replace the URL with your actual Koyeb App URL later, passed via environment variable
    APP_URL = os.environ.get('APP_URL')
    if APP_URL:
        # Construct full webhook URL
        webhook_url = f"{APP_URL.rstrip('/')}/{API_TOKEN}"
        bot.set_webhook(url=webhook_url)
        return f"Webhook configured beautifully! URL: {webhook_url}", 200
    else:
        return "Bot is running, but APP_URL environment variable is missing for precise Webhook setting.", 200

if __name__ == '__main__':
    # When deployed, it runs via Gunicorn using standard Web Service ports
    # For local test, run a local Flask server or polling
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
