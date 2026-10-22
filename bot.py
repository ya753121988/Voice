import os
import sqlite3
import edge_tts
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ⚠️ আপনার বট টোকেনটি এখানে দিন অথবা Render-এর Environment Variable-এ সেট করুন
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# --- ১০ জন মেয়ে ও ১০ জন ছেলের ভয়েস লিস্ট ---
VOICES = {
    # Female Voices (Top Bengali Fairy Tales Voice সহ অন্যান্য ভয়েস)
    "f1": {"name": "👧 Nabanita (Bengali Fairy Tales Voice)", "voice": "bn-BD-NabanitaNeural"},
    "f2": {"name": "👧 Tanishaa (Bangla - India)", "voice": "bn-IN-TanishaaNeural"},
    "f3": {"name": "👩 Neerja (English - IN)", "voice": "en-IN-NeerjaNeural"},
    "f4": {"name": "👩 Jenny (English - US)", "voice": "en-US-JennyNeural"},
    "f5": {"name": "👩 Aria (English - US)", "voice": "en-US-AriaNeural"},
    "f6": {"name": "👩 Sonia (English - UK)", "voice": "en-GB-SoniaNeural"},
    "f7": {"name": "👩 Swara (Hindi - IN)", "voice": "hi-IN-SwaraNeural"},
    "f8": {"name": "👩 Ananya (Hindi - IN)", "voice": "hi-IN-AnanyaNeural"},
    "f9": {"name": "👩 Natasha (English - AU)", "voice": "en-AU-NatashaNeural"},
    "f10": {"name": "👩 Clara (English - CA)", "voice": "en-CA-ClaraNeural"},
    
    # Male Voices
    "m1": {"name": "👦 Pradeep (Bangla - Bangladesh)", "voice": "bn-BD-PradeepNeural"},
    "m2": {"name": "👦 Bashkar (Bangla - India)", "voice": "bn-IN-BashkarNeural"},
    "m3": {"name": "👨 Prabhat (English - IN)", "voice": "en-IN-PrabhatNeural"},
    "m4": {"name": "👨 Guy (English - US)", "voice": "en-US-GuyNeural"},
    "m5": {"name": "👨 Christopher (English - US)", "voice": "en-US-ChristopherNeural"},
    "m6": {"name": "👨 Ryan (English - UK)", "voice": "en-GB-RyanNeural"},
    "m7": {"name": "👨 Madhur (Hindi - IN)", "voice": "hi-IN-MadhurNeural"},
    "m8": {"name": "👨 William (English - AU)", "voice": "en-AU-WilliamNeural"},
    "m9": {"name": "👨 Liam (English - CA)", "voice": "en-CA-LiamNeural"},
    "m10": {"name": "👨 James (English - PH)", "voice": "en-PH-JamesNeural"}
}

# ডিফল্ট ভয়েস হিসেবে Fairy Tales এর ভয়েস সেট করা আছে
DEFAULT_VOICE = "bn-BD-NabanitaNeural"

# --- পার্মানেন্ট ডাটাবেজ সেটআপ (SQLite) ---
def init_db():
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            voice_code TEXT
        )
    """)
    conn.commit()
    conn.close()

def set_user_voice(user_id: int, voice_code: str):
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, voice_code)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET voice_code=excluded.voice_code
    """, (user_id, voice_code))
    conn.commit()
    conn.close()

def get_user_voice(user_id: int) -> str:
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT voice_code FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return DEFAULT_VOICE

# --- বট কমান্ড ও হ্যান্ডলার ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Text-to-Voice বটে আপনাকে স্বাগতম!**\n\n"
        "আপনার পছন্দের ভয়েস বা `@BengaliFairyTales` চ্যানেলের ভয়েস সিলেক্ট করতে `/voice` টাইপ করুন।\n"
        "তারপর যেকোনো টেক্সট পাঠালে সেটি ভয়েস মেসেজ হয়ে যাবে।"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def voice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ভয়েস সিলেক্ট করার ইনলাইন বাটন মেনু"""
    keyboard = []
    
    # Female Voices
    female_buttons = []
    for code, info in list(VOICES.items())[:10]:
        female_buttons.append(InlineKeyboardButton(info["name"], callback_data=f"set_{code}"))
        if len(female_buttons) == 1:
            keyboard.append(female_buttons)
            female_buttons = []
    if female_buttons:
        keyboard.append(female_buttons)

    # Separator
    keyboard.append([InlineKeyboardButton("➖➖➖➖ Male Voices ➖➖➖➖", callback_data="none")])

    # Male Voices
    male_buttons = []
    for code, info in list(VOICES.items())[10:]:
        male_buttons.append(InlineKeyboardButton(info["name"], callback_data=f"set_{code}"))
        if len(male_buttons) == 1:
            keyboard.append(male_buttons)
            male_buttons = []
    if male_buttons:
        keyboard.append(male_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🎙️ **আপনার পছন্দের ভয়েস বেছে নিন:**", reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text("🎙️ **আপনার পছন্দের ভয়েস বেছে নিন:**", reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("set_"):
        voice_key = query.data.replace("set_", "")
        selected_voice = VOICES[voice_key]["voice"]
        voice_name = VOICES[voice_key]["name"]
        
        # Save to Database
        set_user_voice(query.from_user.id, selected_voice)
        
        await query.edit_message_text(f"✅ আপনার ভয়েস নির্বাচন সফল হয়েছে!\nবর্তমান ভয়েস: **{voice_name}**", parse_mode="Markdown")

async def convert_text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.chat_id

    # সেভ থাকা ভয়েস লোড করা
    selected_voice = get_user_voice(user_id)

    status_msg = await update.message.reply_text("⏳ ভয়েস তৈরি করা হচ্ছে...")

    output_file = f"voice_{user_id}.mp3"

    try:
        communicate = edge_tts.Communicate(user_text, selected_voice)
        await communicate.save(output_file)

        with open(output_file, "rb") as audio:
            await context.bot.send_audio(
                chat_id=user_id,
                audio=audio,
                caption="✅ আপনার ভয়েস অডিও!",
                title="Voice Note",
                performer="TTS Bot"
            )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ ভয়েস তৈরি করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        print(f"Error: {e}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", voice_menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_text_to_speech))

    print("🤖 Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
