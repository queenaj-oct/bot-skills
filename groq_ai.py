import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    # 1. Cek apakah key kosong
    if not api_key:
        await update.message.reply_text("❌ Key kosong di Railway!")
        return

    # 2. Cek apakah key terbaca (hanya tampilkan 4 karakter pertama)
    await update.message.reply_text(f"🔑 Key terdeteksi (mulai dengan: {api_key[:4]}...)")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Hai"}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # 3. Tampilkan status code dan respon asli dari server
        if response.status_code == 200:
            await update.message.reply_text("✅ Berhasil! Groq merespons.")
        else:
            await update.message.reply_text(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
