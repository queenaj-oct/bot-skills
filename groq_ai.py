import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# Mengambil API Key dari Railway Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /ai <pertanyaanmu>")
        return

    user_message = " ".join(context.args)
    await update.message.reply_text("🧠 Sedang berpikir...")

    if not GROQ_API_KEY:
        await update.message.reply_text("Error: GROQ_API_KEY belum disetting!")
        return

    try:
        # Menghubungi server Groq secara langsung tanpa SDK berat
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192", # Model teringan dan tercepat di Groq
            "messages": [{"role": "user", "content": user_message}]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan AI: {e}")

def setup(application):
    # Mendaftarkan perintah /ai ke dalam bot
    application.add_handler(CommandHandler("ai", ai_command))

