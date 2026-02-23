import os
import telebot
from telebot.types import Message, Update
from pdf2docx import Converter
import subprocess
from flask import Flask, request

API_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(API_TOKEN)

# Flask application for Webhook support
app = Flask(__name__)

MAX_SIZE = 10 * 1024 * 1024  # 10 MB

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    welcome_text = (
        "مرحباً بك في بوت تحويل الملفات! 🔄\n\n"
        "يمكنني تحويل الملفات بين صيغتي PDF و DOCX.\n\n"
        "طريقة الاستخدام:\n"
        "1. أرسل لي ملف بصيغة PDF وسأقوم بتحويله إلى DOCX (Word).\n"
        "2. أرسل لي ملف بصيغة DOCX وسأقوم بتحويله إلى PDF.\n\n"
        "⚠️ ملاحظة: الحد الأقصى لحجم الملف هو 10 ميجابايت."
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

    processing_msg = bot.reply_to(message, "جاري تنزيل الملف... ⏳")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if ext == '.pdf':
            bot.edit_message_text("جاري تحويل الملف من PDF إلى DOCX... ⏳", 
                                  chat_id=message.chat.id, 
                                  message_id=processing_msg.message_id)
            
            pdf_path = f"{base_name}.pdf"
            docx_path = f"{base_name}.docx"
            
            with open(pdf_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            try:
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()
                
                bot.edit_message_text("جاري إرسال الملف... 📤", 
                                      chat_id=message.chat.id, 
                                      message_id=processing_msg.message_id)
                with open(docx_path, 'rb') as doc_file:
                    bot.send_document(message.chat.id, doc_file)
                
                bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            except Exception as conv_err:
                print(f"PDF2DOCX Conversion Error: {conv_err}")
                bot.edit_message_text(f"حدث خطأ داخلي أثناء تحويل هذا الـ PDF المعقد. ❌", 
                                      chat_id=message.chat.id, 
                                      message_id=processing_msg.message_id)
            finally:
                if os.path.exists(pdf_path): os.remove(pdf_path)
                if os.path.exists(docx_path): os.remove(docx_path)
                
        elif ext == '.docx':
            bot.edit_message_text("جاري تحويل الملف من DOCX إلى PDF... ⏳", 
                                  chat_id=message.chat.id, 
                                  message_id=processing_msg.message_id)
            
            docx_path = f"{base_name}.docx"
            pdf_path = f"{base_name}.pdf"
            
            with open(docx_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            try:
                # Using libreoffice for conversion. Needs to be installed on system.
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path], check=True)
                
                bot.edit_message_text("جاري إرسال الملف... 📤", 
                                      chat_id=message.chat.id, 
                                      message_id=processing_msg.message_id)
                with open(pdf_path, 'rb') as pdf_file:
                    bot.send_document(message.chat.id, pdf_file)

                bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            finally:
                if os.path.exists(docx_path): os.remove(docx_path)
                if os.path.exists(pdf_path): os.remove(pdf_path)
            
    except Exception as e:
        bot.edit_message_text("حدث خطأ أثناء معالجة الملف. ❌", 
                              chat_id=message.chat.id, 
                              message_id=processing_msg.message_id)
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
