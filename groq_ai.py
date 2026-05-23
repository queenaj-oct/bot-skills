import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /ai <pertanyaanmu>")
        return

    user_message = " ".join(context.args)
    await update.message.reply_text("🧠 Sedang berpikir...")

    if not GROQ_API_KEY:
        await update.message.reply_text("Error: GROQ_API_KEY belum disetting di Railway!")
        return

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            # Tambahkan .strip() untuk mencegah spasi tidak sengaja di API Key
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        data = {
            # Menggunakan model Llama 3.1 terbaru yang didukung Groq
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": user_message}]
        }

        response = requests.post(url, headers=headers, json=data)
        
        # Jika masih error, bot akan menampilkan alasan asli dari server Groq
        if response.status_code != 200:
            await update.message.reply_text(f"Error API Groq: {response.text}")
            return
            
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan sistem: {e}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
