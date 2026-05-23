import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        await update.message.reply_text("Error: API Key tidak ditemukan!")
        return

    if not context.args:
        await update.message.reply_text("Masukkan pertanyaan setelah /ai")
        return

    user_text = " ".join(context.args)
    await update.message.reply_text("🧠 Berpikir...")

    try:
        # Menggunakan endpoint dan model yang lebih standar
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        }
        # Struktur data minimalis agar tidak ditolak server
        payload = {
            "model": "llama3-8b-8192", 
            "messages": [{"role": "user", "content": user_text}]
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            await update.message.reply_text(reply)
        else:
            # Ini akan menunjukkan alasan error sebenarnya
            await update.message.reply_text(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        await update.message.reply_text(f"Error sistem: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))

