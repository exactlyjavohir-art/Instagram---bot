import os
import telebot
import yt_dlp

# Bot tokenini shu yerga yozasiz (yoki Render'dagi Environment Variables'dan o'qitisiz)
TOKEN = "TOKENINGIZNI_SHU_YERGA_YOZING"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga Instagram'dan video havolasini (linkini) yuboring, men uni yuklab beraman.")

@bot.message_handler(func=lambda message: True)
def handle_instagram_link(message):
    url = message.text
    
    if "instagram.com" not in url:
        bot.reply_to(message, "Iltimos, to'g'ri Instagram havolasini yuboring!")
        return

    msg = bot.reply_to(message, "⏳ Video yuklab olinmoqda, biroz kuting...")
    
    output_file = "video.mp4"
    
    ydl_opts = {
        'outtmpl': output_file,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Videoni Telegram'ga yuborish
        with open(output_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="Mana, siz so'ragan video! 🚀")
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        # Yuklangandan keyin faylni o'chirib tashlash
        if os.path.exists(output_file):
            os.remove(output_file)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Videoni yuklashda xatolik yuz berdi: {e}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()

