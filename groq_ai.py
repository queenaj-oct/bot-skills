import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        await update.message.reply_text("Error: Key tidak ditemukan di server!")
        return
    
    # Cek panjang karakter (seharusnya API Key cukup panjang)
    await update.message.reply_text(f"Key terdeteksi! Panjang karakter: {len(key)}. Mencoba koneksi...")
    
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {key.strip()}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            await update.message.reply_text("Koneksi ke Groq berhasil! API Key valid.")
        else:
            await update.message.reply_text(f"Koneksi gagal! Status: {response.status_code}. Pesan: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"Error sistem: {e}")

def setup(application):
    application.add_handler(CommandHandler("ai", ai_command))
