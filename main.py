import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import edge_tts
import asyncio
import json
import os

# আপনার বটের টোকেন দিন
TOKEN = '8876597863:AAHyUfykCmx9B-URe_VEeFQNflBN3XT-4h0'
bot = telebot.TeleBot(TOKEN)

# টেম্প স্টোরেজ ডাটাবেস (ভয়েস সিলেকশন সেভ রাখার জন্য)
DB_FILE = 'users_data.json'

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# ১০ জন মেয়ে এবং ১০ জন ছেলের ভয়েস তালিকা
VOICES = {
    "Female": {
        "👧 Nabanita (Bengali-BD)": "bn-BD-NabanitaNeural",  # BengaliFairyTales Voice
        "👧 Tanishaa (Bengali-IN)": "bn-IN-TanishaaNeural",
        "👧 Swara (Hindi)": "hi-IN-SwaraNeural",
        "👧 Pallavi (Hindi)": "hi-IN-PallaviNeural",
        "👧 Aria (English)": "en-US-AriaNeural",
        "👧 Ana (English)": "en-US-AnaNeural",
        "👧 Jenny (English)": "en-US-JennyNeural",
        "👧 Sonia (English)": "en-GB-SoniaNeural",
        "👧 Mia (English)": "en-GB-MiaNeural",
        "👧 Natasha (English)": "en-AU-NatashaNeural"
    },
    "Male": {
        "👦 Pradeep (Bengali-BD)": "bn-BD-PradeepNeural",
        "👦 Bashkar (Bengali-IN)": "bn-IN-BashkarNeural",
        "👦 Madhur (Hindi)": "hi-IN-MadhurNeural",
        "👦 Puneet (Hindi)": "hi-IN-PuneetNeural",
        "👦 Guy (English)": "en-US-GuyNeural",
        "👦 Christopher (English)": "en-US-ChristopherNeural",
        "👦 Eric (English)": "en-US-EricNeural",
        "👦 Ryan (English)": "en-GB-RyanNeural",
        "👦 Thomas (English)": "en-GB-ThomasNeural",
        "👦 William (English)": "en-AU-WilliamNeural"
    }
}

@bot.message_handler(commands=['start'])
def start_message(message):
    text = (
        "স্বাগতম! 🎙\n\n"
        "আমাকে যেকোনো টেক্সট দিন, আমি সেটিকে রিয়েল ভয়েসে কনভার্ট করে দেব।\n\n"
        "আপনার পছন্দের ভয়েস (ছেলে/মেয়ে) সিলেক্ট করতে /voice কমান্ড দিন।"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['voice'])
def choose_voice(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("👧 মেয়েদের ভয়েস (১০টি)", callback_data="cat_Female"),
        InlineKeyboardButton("👦 ছেলেদের ভয়েস (১০টি)", callback_data="cat_Male")
    )
    bot.reply_to(message, "আপনি কোন ধরনের ভয়েস শুনতে চান তা সিলেক্ট করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def voice_category(call):
    category = call.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    
    # ওই ক্যাটাগরির সবগুলো ভয়েস বাটনে যুক্ত করা
    for name, code in VOICES[category].items():
        markup.add(InlineKeyboardButton(name, callback_data=f"set_{code}"))
        
    bot.edit_message_text(f"{category} ভয়েসগুলো নিচে দেওয়া হলো। আপনার পছন্দেরটি সিলেক্ট করুন:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def set_voice(call):
    voice_code = call.data.replace('set_', '')
    user_id = str(call.from_user.id)
    
    # ডাটাবেসে ইউজারের ভয়েস সেভ করা হচ্ছে
    data = load_data()
    data[user_id] = voice_code
    save_data(data)
    
    bot.answer_callback_query(call.id, "ভয়েস সেভ করা হয়েছে!")
    bot.edit_message_text(f"✅ আপনার ভয়েস সফলভাবে সেট করা হয়েছে!\n\nএখন আমাকে যেকোনো টেক্সট দিন।", 
                          call.message.chat.id, call.message.message_id)

async def generate_tts(text, voice, filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    # ইউজার ভয়েস সিলেক্ট না করলে ডিফল্ট হিসেবে Nabanita (Bengali Fairy Tales) থাকবে
    user_voice = data.get(user_id, "bn-BD-NabanitaNeural")
    
    msg = bot.reply_to(message, "অডিও তৈরি হচ্ছে, দয়া করে অপেক্ষা করুন... ⏳")
    
    filename = f"audio_{user_id}.mp3"
    try:
        # টেক্সট থেকে ভয়েস তৈরি
        asyncio.run(generate_tts(message.text, user_voice, filename))
        
        # অডিও পাঠানো
        with open(filename, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
            
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ অডিও তৈরি করতে সমস্যা হয়েছে। টেক্সটটি অন্যভাবে লিখে চেষ্টা করুন।", 
                              message.chat.id, msg.message_id)
    finally:
        # ফাইল স্টোরেজ ক্লিয়ার করা (যাতে সার্ভার ফুল না হয়)
        if os.path.exists(filename):
            os.remove(filename)

print("Bot is successfully running...")
bot.polling(none_stop=True)
