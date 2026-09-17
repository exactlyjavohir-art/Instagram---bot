import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Tokeningizni qo'shtirnoq ichiga yozing (masalan: "123456:ABC-DEF...")
TOKEN = "8562156715:AAEnhSYonAKelXlzQtKsHtyVjUhH10A3awk"
bot = telebot.TeleBot(TOKEN)

# Botning user nomini avtomatik aniqlab olamiz
try:
    BOT_USERNAME = bot.get_me().username
except Exception:
    BOT_USERNAME = "bot_ingiz"

# 1. Start buyrug'i (Asosiy menyu va ko'rsatmalar)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        f"🔥 Assalomu alaykum.\n"
        f"@{BOT_USERNAME} ga xush kelibsiz.\n\n"
        "Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
        "• **Instagram** - post, reels va IGTV\n"
        "• **TikTok** - suv belgisiz video\n"
        "• **YouTube** - videolar va shorts\n"
        "• **Snapchat** - suv belgisiz video\n"
        "• **Likee** - suv belgisiz video\n"
        "• **Pinterest** - video va rasmlar\n"
        "• **Threads** - video va rasmlar\n\n"
        "📥 Yuklab olmoqchi bo'lgan media havolasini yuboring!\n\n"
        f"🤖 Bot: @{BOT_USERNAME}",
        parse_mode="Markdown"
    )

# 2. Qo'llab-quvvatlanadigan platformalar havolalarini tutib olish
SUPPORTED_DOMAINS = [
    "instagram.com", "tiktok.com", "youtu.be", "youtube.com", 
    "snapchat.com", "likee.video", "pinterest.com", "pin.it", "threads.net"
]

@bot.message_handler(func=lambda message: any(domain in message.text for domain in SUPPORTED_DOMAINS))
def handle_media(message):
    url = message.text.strip()
    sent_msg = bot.reply_to(message, "⚡️ Ma'lumotlar tahlil qilinmoqda, biroz kuting...")
    
    try:
        # yt-dlp orqali tezkor tahlil qilish
        ydl_opts = {'quiet': True, 'format': 'best[ext=mp4]/best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]
                
            media_url = info.get('url')
            is_video = info.get('ext') in ['mp4', 'webm'] or info.get('duration')
            
            # Agar bu rasm bo'lsa (Pinterest / Instagram / Threads rasmlari)
            if not is_video and info.get('thumbnail'):
                photo_url = media_url or info.get('thumbnail')
                bot.send_photo(
                    message.chat.id, 
                    photo_url, 
                    caption=f"📸 Rasm muvaffaqiyatli topildi!\n\n@{BOT_USERNAME}"
                )
                bot.delete_message(message.chat.id, sent_msg.message_id)
                return

        # Agar video bo'lsa, foydalanuvchiga tugmalar chiqaramiz
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📥 Videoni yuklash", callback_data=f"vid_{message.id}"),
            InlineKeyboardButton("🎵 Musiqasini olish", callback_data=f"aud_{message.id}")
        )
        
        bot.edit_message_text(
            "✅ Media tayyor! Kerakli amalni tanlang:", 
            message.chat.id, 
            sent_msg.message_id, 
            reply_markup=markup
        )
        
        # Havolani vaqtinchalik xotirada saqlaymiz
        global_media_cache[message.chat.id] = media_url

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: Havola noto'g'ri yoki yopiq profil bo'lishi mumkin.", message.chat.id, sent_msg.message_id)

# Vaqtinchalik xotira lug'ati
global_media_cache = {}

# 3. Tugmalar bosilgandagi amallar (Video yoki Audio jo'natish)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    media_url = global_media_cache.get(chat_id)
    
    if not media_url:
        bot.answer_callback_query(call.id, "Ma'lumot eskirgan, iltimos havolani qaytadan yuboring.")
        return

    if call.data.startswith("vid_"):
        bot.answer_callback_query(call.id, "Video yuborilmoqda...")
        bot.send_video(
            chat_id, 
            media_url, 
            caption=f"🎬 @{BOT_USERNAME} orqali yuklab olindi"
        )

    elif call.data.startswith("aud_"):
        bot.answer_callback_query(call.id, "Musiqasi ajratib olinmoqda...")
        try:
            # yt-dlp va ffmpeg yordamida audioni mp3 qilish
            audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'temp_audio.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
            }
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([media_url])
            
            with open('temp_audio.mp3', 'rb') as audio:
                bot.send_audio(
                    chat_id, 
                    audio, 
                    title="Audio Track", 
                    caption=f"🎵 @{BOT_USERNAME}"
                )
            os.remove('temp_audio.mp3')
        except Exception as e:
            bot.send_message(chat_id, f"Musiqani olishda xatolik yuz berdi: {e}")

bot.polling(none_stop=True)




