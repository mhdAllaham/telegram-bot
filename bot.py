import os
import telebot
from telebot.types import Message
from pdf2docx import Converter
import subprocess

API_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(API_TOKEN)

MAX_SIZE = 10 * 1024 * 1024  # 10 MB

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    welcome_text = (
        "Welcome to the File Converter Bot! 🔄\n\n"
        "I can convert files between PDF and DOCX formats.\n\n"
        "How to use:\n"
        "1. Send me a PDF file and I will convert it to DOCX (Word).\n"
        "2. Send me a DOCX file and I will convert it to PDF.\n\n"
        "⚠️ Note: The maximum file size supported is 10 MB."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['document'])
def handle_docs(message: Message):
    if message.document.file_size > MAX_SIZE:
        bot.reply_to(message, "Sorry, the file size exceeds 10 MB. ❌")
        return

    file_name = message.document.file_name
    base_name, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if ext not in ['.pdf', '.docx']:
        bot.reply_to(message, "Sorry, I only support PDF and DOCX files. ❌")
        return

    processing_msg = bot.reply_to(message, "Downloading file... ⏳")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if ext == '.pdf':
            bot.edit_message_text("Converting PDF to DOCX... ⏳", 
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
                
                bot.edit_message_text("Sending file... 📤", 
                                      chat_id=message.chat.id, 
                                      message_id=processing_msg.message_id)
                with open(docx_path, 'rb') as doc_file:
                    bot.send_document(message.chat.id, doc_file)
                
                bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            finally:
                if os.path.exists(pdf_path): os.remove(pdf_path)
                if os.path.exists(docx_path): os.remove(docx_path)
                
        elif ext == '.docx':
            bot.edit_message_text("Converting DOCX to PDF... ⏳", 
                                  chat_id=message.chat.id, 
                                  message_id=processing_msg.message_id)
            
            docx_path = f"{base_name}.docx"
            pdf_path = f"{base_name}.pdf"
            
            with open(docx_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            try:
                # Using libreoffice for conversion. Needs to be installed on system.
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path], check=True)
                
                bot.edit_message_text("Sending file... 📤", 
                                      chat_id=message.chat.id, 
                                      message_id=processing_msg.message_id)
                with open(pdf_path, 'rb') as pdf_file:
                    bot.send_document(message.chat.id, pdf_file)

                bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            finally:
                if os.path.exists(docx_path): os.remove(docx_path)
                if os.path.exists(pdf_path): os.remove(pdf_path)
            
    except Exception as e:
        bot.edit_message_text("An error occurred while processing the file. ❌", 
                              chat_id=message.chat.id, 
                              message_id=processing_msg.message_id)
        print(f"Error: {e}")

if __name__ == '__main__':
    print("Bot is starting...")
    bot.polling(none_stop=True)
