import os
import requests
import json
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mengambil key dan memastikan tidak ada spasi atau karakter newline
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    if not api_key:
        await update.message.reply_text("Error: GROQ_API_KEY kosong!")
        return

    user_text = " ".join(context.args)
    if not user_text:
        await update.message.reply_text("Ketik /ai <pertanyaan>")
        return

    await update.message.reply_text("🧠 Berpikir...")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": user_text}]
    }

    try:
        # Menggunakan POST request (WAJIB untuk chat completions)
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            await update.message.reply_text(reply)
        else:
            # Mengirimkan detail error untuk diagnosa
            await update.message.reply_text(f"Groq Error ({response.status_code}): {response.text[:100]}")
            
    except Exception as e:
        await update.message.reply_text(f"System Error: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
