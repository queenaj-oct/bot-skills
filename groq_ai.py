import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ambil key tanpa embel-embel
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    user_text = " ".join(context.args)

    if not api_key:
        await update.message.reply_text("Key tidak ditemukan di Railway!")
        return

    # Endpoint Groq resmi yang paling stabil saat ini
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Body payload standar
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": user_text}]
    }

    try:
        # Mengirim request dengan timeout
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            await update.message.reply_text(reply)
        else:
            # Ini akan menunjukkan pesan error teknis dari Groq
            error_msg = response.json().get('error', {}).get('message', 'Unknown Error')
            await update.message.reply_text(f"Groq Error ({response.status_code}): {error_msg}")
            
    except Exception as e:
        await update.message.reply_text(f"Koneksi gagal: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
