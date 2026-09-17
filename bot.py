import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from moviepy.editor import VideoFileClip

TOKEN = "8562156715:AAFLtwEHNodfkEsOFhQG0ACBjdEDHtOI_Hw"
bot = telebot.TeleBot(TOKEN)

# Botning user nomini avtomatik aniqlab olamiz
try:
    BOT_USERNAME = bot.get_me().username
except Exception:
    BOT_USERNAME = "bot_ingiz"

# 1. Start buyrug'i
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Salom! 👋\n"
        "Menga Instagram'dan **video** yoki **rasm** havolasini yuboring.\n"
        "Men uni tezda topib, quyidagi imkoniyatlarni taqdim etaman:\n"
        "• Videoni yuklab olish 📥\n"
        "• Musiqasini ajratib olish 🎵\n"
        "• Yumaloq videoga aylantirish 🟢\n\n"
        f"🤖 Bot: @{BOT_USERNAME}"
    )

# 2. Instagram havolalarini tutib olish
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    url = message.text.strip()
    sent_msg = bot.reply_to(message, "⚡️ Ma'lumotlar tahlil qilinmoqda...")
    
    try:
        ydl_opts = {'quiet': True, 'format': 'best[ext=mp4]/best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]
                
            media_url = info.get('url')
            is_video = info.get('ext') in ['mp4', 'webm'] or info.get('duration')
            
            if not is_video:
                # Agar rasm bo'lsa, tagiga username yozamiz
                bot.send_photo(
                    message.chat.id, 
                    media_url, 
                    caption=f"📸 Instagram'dan rasm topildi!\n\n@{BOT_USERNAME}"
                )
                bot.delete_message(message.chat.id, sent_msg.message_id)
                return

        # Agar video bo'lsa, tugmalar chiqaramiz
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📥 Videoni yuklash", callback_data=f"vid_{message.id}"),
            InlineKeyboardButton("🎵 Musiqasini olish", callback_data=f"aud_{message.id}"),
            InlineKeyboardButton("🟢 Yumaloq video", callback_data=f"round_{message.id}")
        )
        
        bot.edit_message_text(
            "✅ Video tayyor! Kerakli amalni tanlang:", 
            message.chat.id, 
            sent_msg.message_id, 
            reply_markup=markup
        )
        
        global_media_cache[message.chat.id] = media_url

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {e}", message.chat.id, sent_msg.message_id)

global_media_cache = {}

# 3. Tugmalar bosilgandagi amallar
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    media_url = global_media_cache.get(chat_id)
    
    if not media_url:
        bot.answer_callback_query(call.id, "Ma'lumot eskirgan, iltimos havolani qaytadan yuboring.")
        return

    if call.data.startswith("vid_"):
        bot.answer_callback_query(call.id, "Video yuborilmoqda...")
        # Videoning tagiga bot username'i yoziladi
        bot.send_video(
            chat_id, 
            media_url, 
            caption=f"🎬 @{BOT_USERNAME} orqali yuklab olindi"
        )

    elif call.data.startswith("aud_"):
        bot.answer_callback_query(call.id, "Musiqasi ajratib olinmoqda...")
        try:
            audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'temp_audio.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
            }
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([media_url])
            
            with open('temp_audio.mp3', 'rb') as audio:
                # Audioning tagiga ham username yoziladi
                bot.send_audio(
                    chat_id, 
                    audio, 
                    title="Instagram Audio", 
                    caption=f"🎵 @{BOT_USERNAME}"
                )
            os.remove('temp_audio.mp3')
        except Exception as e:
            bot.send_message(chat_id, f"Musiqani olishda xatolik: {e}")

    elif call.data.startswith("round_"):
        bot.answer_callback_query(call.id, "Yumaloq videoga aylantirilmoqda...")
        try:
            input_file = 'temp_input.mp4'
            output_file = 'temp_round.mp4'
            
            import urllib.request
            urllib.request.urlretrieve(media_url, input_file)
            
            clip = VideoFileClip(input_file)
            w, h = clip.size
            min_dim = min(w, h)
            clip_cropped = clip.crop(x_center=w/2, y_center=h/2, width=min_dim, height=min_dim)
            clip_cropped.write_videofile(output_file, codec='libx264', audio_codec='aac', fps=24)
            
            with open(output_file, 'rb') as video_note:
                bot.send_video_note(chat_id, video_note)
            
            # Telegram talabiga ko'ra krujkalarga matn yozib bo'lmaydi, shuning uchun pastiga username yuboramiz
            bot.send_message(chat_id, f"🟢 @{BOT_USERNAME}")
            
            clip.close()
            clip_cropped.close()
            os.remove(input_file)
            os.remove(output_file)
        except Exception as e:
            bot.send_message(chat_id, f"Yumaloq video qilishda xatolik: {e}")

bot.polling(none_stop=True)


