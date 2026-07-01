import os
import telebot
import subprocess
import shutil
import zipfile
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8877502937:AAGRGZ-dCEQw9IPZ3UCzDkDzcda6WOHgwhA"
ADMIN_ID = 8632939616  # Your Telegram User ID
BOT_DISPLAY_NAME = "APK Cracker Injector Bot"
ZIP_OUTPUT_NAME = "payload.zip"

# ==========================================
# DATABASE STORAGE
# ==========================================
active_keys = {}
user_profiles = {}
known_users = set()
user_states = {}

bot = telebot.TeleBot(BOT_TOKEN)


def process_apk(input_path, output_path, chat_id):
    decode_dir = f"decompile_{chat_id}"
    
    if not os.path.exists("apktool.jar"):
        bot.send_message(chat_id, "❌ Critical Server Error: `apktool.jar` is missing from the host directory.")
        return False
        
    try:
        bot.send_message(chat_id, "🔧 Unpacking APK layout with Apktool...")
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
            bot.send_message(chat_id, "ℹ️ Original main.lua was not found; skipping rename step.")

        if os.path.exists(ZIP_OUTPUT_NAME):
            bot.send_message(chat_id, "📦 Extracting payload.zip contents into /assets...")
            with zipfile.ZipFile(ZIP_OUTPUT_NAME, 'r') as zip_ref:
                zip_ref.extractall(assets_path)
        else:
            bot.send_message(chat_id, f"❌ Error: `{ZIP_OUTPUT_NAME}` is missing from the server root directory.")
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


# ==========================================
# ADMIN COMMANDS
# ==========================================

@bot.message_handler(commands=['generate', 'gen'])
def admin_generate_key(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access Denied: Admin command only.")
        return

    try:
        args = message.text.split()
        max_users = int(args[1]) if len(args) > 1 else 1
        apk_uses = int(args[2]) if len(args) > 2 else 1
        
        if max_users <= 0 or apk_uses <= 0:
            bot.reply_to(message, "❌ Arguments must be greater than 0.")
            return

        new_key = f"KEY-{str(uuid.uuid4())[:8].upper()}"
        active_keys[new_key] = {
            "max_users": max_users,
            "apk_uses_per_user": apk_uses,
            "redeemed_by": []
        }

        response = (
            f"🔑 **New Key Generated**\n\n"
            f"Code: `{new_key}`\n"
            f"Max Users Allowed: {max_users}\n"
            f"APK Limit Per User: {apk_uses}"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
    except (ValueError, IndexError):
        bot.reply_to(message, "⚠️ Usage error. Syntax: `/generate <max_users> <apk_uses_per_user>`\nExample: `/generate 10 1`")


@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access Denied: Admin command only.")
        return

    broadcast_text = message.text.replace("/broadcast", "").strip()
    if not broadcast_text:
        bot.reply_to(message, "⚠️ Usage syntax error. Use: `/broadcast <your message>`")
        return

    bot.reply_to(message, f"📢 Starting global broadcast to {len(known_users)} users...")
    success_count = 0
    for user_id in list(known_users):
        try:
            bot.send_message(user_id, f"📢 **ADMIN ANNOUNCEMENT**\n\n{broadcast_text}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            pass

    bot.send_message(ADMIN_ID, f"✅ Broadcast finished. Delivered to {success_count} users successfully.")


# ==========================================
# USER ROUTINES & VALIDATION
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    known_users.add(chat_id)

    # Admin bypass check
    if message.from_user.id == ADMIN_ID:
        show_main_menu(chat_id)
        return

    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})
    
    if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
        welcome_text = f"Welcome to **{BOT_DISPLAY_NAME}**.\n\n⚠️ You do not have active access. Please enter your subscription code below to gain access."
        user_states[chat_id] = "AWAITING_REDEEM_CODE"
        bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
        return

    show_main_menu(chat_id)


def show_main_menu(chat_id):
    if chat_id == ADMIN_ID:
        welcome_text = f"Welcome back Admin to **{BOT_DISPLAY_NAME}**.\n\n👑 You have unlimited lifetime administrator access."
    else:
        profile = user_profiles.get(chat_id, {"remaining_apk_uses": 0})
        welcome_text = f"Welcome back to **{BOT_DISPLAY_NAME}**.\n\n✅ Your access token is valid.\n📊 Remaining APK uses left: `{profile['remaining_apk_uses']}`"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🚀 Crack Apks", callback_data="await_apk"))
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "await_apk")
def handle_inline_click(call):
    chat_id = call.message.chat.id
    
    # Admin bypass check
    if chat_id == ADMIN_ID:
        user_states[chat_id] = "EXPECTING_APK"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📥 Send the **.apk** file you want to edit now.")
        return

    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})
    if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
        bot.answer_callback_query(call.id, "❌ Access expired! Please obtain a new code.", show_alert=True)
        return
        
    user_states[chat_id] = "EXPECTING_APK"
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📥 Send the **.apk** file you want to edit now.")


@bot.message_handler(content_types=['document', 'text'])
def handle_incoming_messages(message):
    chat_id = message.chat.id
    known_users.add(chat_id)
    current_state = user_states.get(chat_id)
    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})

    # 1. Handle Access Key Redemption
    if current_state == "AWAITING_REDEEM_CODE" and message.content_type == 'text':
        input_code = message.text.strip()
        
        if input_code in active_keys:
            key_data = active_keys[input_code]
            
            if chat_id in key_data["redeemed_by"]:
                bot.send_message(chat_id, "❌ You have already redeemed this code once before.")
                return

            if len(key_data["redeemed_by"]) < key_data["max_users"]:
                key_data["redeemed_by"].append(chat_id)
                
                user_profiles[chat_id] = {
                    "authorized": True,
                    "remaining_apk_uses": key_data["apk_uses_per_user"]
                }
                user_states[chat_id] = None
                
                if len(key_data["redeemed_by"]) >= key_data["max_users"]:
                    del active_keys[input_code]
                    
                bot.send_message(chat_id, "✅ Activation Successful!")
                show_main_menu(chat_id)
            else:
                bot.send_message(chat_id, "❌ This code has reached its maximum allowed user limit.")
                del active_keys[input_code]
        else:
            bot.send_message(chat_id, "❌ Invalid access key code. Please check spelling or request a new key.")
        return

    # 2. Handle Document/APK Injection Process
    if current_state == "EXPECTING_APK" and message.content_type == 'document':
        # Admin bypass check
        if chat_id != ADMIN_ID:
            if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
                bot.send_message(chat_id, "❌ Access expired. Use a new token.")
                user_states[chat_id] = None
                return

        file_name = message.document.file_name
        if not file_name.lower().endswith('.apk'):
            bot.send_message(chat_id, "❌ Invalid file type. Please upload a file ending with `.apk`.")
            return
            
        bot.send_message(chat_id, "⏳ Downloading your APK To Crack It...")
        
        input_file = f"raw_{chat_id}.apk"
        output_file = f"mod_{chat_id}.apk"
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            with open(input_file, 'wb') as f:
                f.write(downloaded)
                
            success = process_apk(input_file, output_file, chat_id)
            
            if success and os.path.exists(output_file):
                # Deduct only if the user is NOT the admin
                if chat_id != ADMIN_ID:
                    user_profiles[chat_id]["remaining_apk_uses"] -= 1
                
                bot.send_message(chat_id, "📤 Uploading finished APK back to you...")
                with open(output_file, 'rb') as final_apk:
                    bot.send_document(chat_id, final_apk, visible_file_name=f"modified_{file_name}")
                
                if chat_id != ADMIN_ID:
                    bot.send_message(chat_id, f"📉 Remaining compilation balances: `{user_profiles[chat_id]['remaining_apk_uses']}` left.")
                else:
                    bot.send_message(chat_id, "👑 Admin compilation completed without using quotas.")
            else:
                bot.send_message(chat_id, "❌ Process failed. Could not build output archive.")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error handling file: {str(e)}")
            
        finally:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)
            user_states[chat_id] = None
    else:
        if chat_id == ADMIN_ID:
            bot.send_message(chat_id, "Please use the menu buttons to start processing a file.")
        elif not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
            bot.send_message(chat_id, "⚠️ Access validation required. Send your valid key.")
        else:
            bot.send_message(chat_id, "Please use the menu buttons to start processing a file.")


if __name__ == "__main__":
    print(f"Starting {BOT_DISPLAY_NAME} engine loop...")
    bot.infinity_polling()            f"APK Limit Per User: {apk_uses}"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
    except (ValueError, IndexError):
        bot.reply_to(message, "⚠️ Usage error. Syntax: `/generate <max_users> <apk_uses_per_user>`\nExample: `/generate 10 1`")


@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access Denied: Admin command only.")
        return

    broadcast_text = message.text.replace("/broadcast", "").strip()
    if not broadcast_text:
        bot.reply_to(message, "⚠️ Usage syntax error. Use: `/broadcast <your message>`")
        return

    bot.reply_to(message, f"📢 Starting global broadcast to {len(known_users)} users...")
    success_count = 0
    for user_id in list(known_users):
        try:
            bot.send_message(user_id, f"📢 **ADMIN ANNOUNCEMENT**\n\n{broadcast_text}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            pass

    bot.send_message(ADMIN_ID, f"✅ Broadcast finished. Delivered to {success_count} users successfully.")


# ==========================================
# USER ROUTINES & VALIDATION
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    known_users.add(chat_id)

    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})
    
    if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
        welcome_text = f"Welcome to **{BOT_DISPLAY_NAME}**.\n\n⚠️ You do not have active access. Please enter your subscription code below to gain access."
        user_states[chat_id] = "AWAITING_REDEEM_CODE"
        bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
        return

    show_main_menu(chat_id)


def show_main_menu(chat_id):
    profile = user_profiles.get(chat_id, {"remaining_apk_uses": 0})
    welcome_text = f"Welcome back to **{BOT_DISPLAY_NAME}**.\n\n✅ Your access token is valid.\n📊 Remaining APK uses left: `{profile['remaining_apk_uses']}`"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🚀 Crack Apks", callback_data="await_apk"))
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "await_apk")
def handle_inline_click(call):
    chat_id = call.message.chat.id
    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})
    
    if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
        bot.answer_callback_query(call.id, "❌ Access expired! Please obtain a new code.", show_alert=True)
        return
        
    user_states[chat_id] = "EXPECTING_APK"
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📥 Send the **.apk** file you want to edit now.")


@bot.message_handler(content_types=['document', 'text'])
def handle_incoming_messages(message):
    chat_id = message.chat.id
    known_users.add(chat_id)
    current_state = user_states.get(chat_id)
    profile = user_profiles.get(chat_id, {"authorized": False, "remaining_apk_uses": 0})

    # 1. Handle Access Key Redemption
    if current_state == "AWAITING_REDEEM_CODE" and message.content_type == 'text':
        input_code = message.text.strip()
        
        if input_code in active_keys:
            key_data = active_keys[input_code]
            
            if chat_id in key_data["redeemed_by"]:
                bot.send_message(chat_id, "❌ You have already redeemed this code once before.")
                return

            if len(key_data["redeemed_by"]) < key_data["max_users"]:
                key_data["redeemed_by"].append(chat_id)
                
                user_profiles[chat_id] = {
                    "authorized": True,
                    "remaining_apk_uses": key_data["apk_uses_per_user"]
                }
                user_states[chat_id] = None
                
                if len(key_data["redeemed_by"]) >= key_data["max_users"]:
                    del active_keys[input_code]
                    
                bot.send_message(chat_id, "✅ Activation Successful!")
                show_main_menu(chat_id)
            else:
                bot.send_message(chat_id, "❌ This code has reached its maximum allowed user limit.")
                del active_keys[input_code]
        else:
            bot.send_message(chat_id, "❌ Invalid access key code. Please check spelling or request a new key.")
        return

    # 2. Handle Document/APK Injection Process
    if current_state == "EXPECTING_APK" and message.content_type == 'document':
        if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
            bot.send_message(chat_id, "❌ Access expired. Use a new token.")
            user_states[chat_id] = None
            return

        file_name = message.document.file_name
        if not file_name.lower().endswith('.apk'):
            bot.send_message(chat_id, "❌ Invalid file type. Please upload a file ending with `.apk`.")
            return
            
        bot.send_message(chat_id, "⏳ Downloading your APK To Crack It...")
        
        input_file = f"raw_{chat_id}.apk"
        output_file = f"mod_{chat_id}.apk"
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            with open(input_file, 'wb') as f:
                f.write(downloaded)
                
            success = process_apk(input_file, output_file, chat_id)
            
            if success and os.path.exists(output_file):
                user_profiles[chat_id]["remaining_apk_uses"] -= 1
                
                bot.send_message(chat_id, "📤 Uploading finished APK back to you...")
                with open(output_file, 'rb') as final_apk:
                    bot.send_document(chat_id, final_apk, visible_file_name=f"modified_{file_name}")
                
                bot.send_message(chat_id, f"📉 Remaining compilation balances: `{user_profiles[chat_id]['remaining_apk_uses']}` left.")
            else:
                bot.send_message(chat_id, "❌ Process failed. Could not build output archive.")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error handling file: {str(e)}")
            
        finally:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)
            user_states[chat_id] = None
    else:
        if not profile["authorized"] or profile["remaining_apk_uses"] <= 0:
            bot.send_message(chat_id, "⚠️ Access validation required. Send your valid key.")
        else:
            bot.send_message(chat_id, "Please use the menu buttons to start processing a file.")


if __name__ == "__main__":
    print(f"Starting {BOT_DISPLAY_NAME} engine loop...")
    bot.infinity_polling()
