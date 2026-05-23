import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    if not api_key:
        await update.message.reply_text("❌ Key kosong di server!")
        return

    if not context.args:
        await update.message.reply_text("Ketik: /ai <pertanyaanmu>")
        return

    user_text = " ".join(context.args)
    await update.message.reply_text("🧠 Sedang merangkai kata...")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": user_text}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Mengambil jawaban asli dari AI
            reply = response.json()['choices'][0]['message']['content']
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text(f"❌ Error API: {response.text}")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
