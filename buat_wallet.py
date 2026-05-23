import requests
from telegram.ext import CommandHandler

# Memori untuk menyimpan alamat wallet (Reset jika bot restart)
user_db = {}

async def buat_wallet_cmd(update, context):
    # Logika pembuatan wallet (Public Key)
    # Ganti string di bawah dengan fungsi generator wallet Anda jika ada
    public_key = "AwLRfaR3wjgm7wdv7JFSkdxY45ymvpcQxS4zqVbBQXHt"
    user_id = update.effective_user.id
    
    # Simpan ke memori bot
    user_db[user_id] = public_key
    
    msg = (
        f"✅ **Wallet Solana Berhasil Dibuat!**\n\n"
        f"🔑 **Alamat:** `{public_key}`\n\n"
        f"Sekarang Anda bisa langsung ketik `/saldo` tanpa memasukkan alamat lagi."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def saldo_cmd(update, context):
    user_id = update.effective_user.id
    
    # 1. Cek apakah user input manual: /saldo <alamat>
    if context.args:
        alamat = context.args[0]
    # 2. Cek apakah user punya wallet tersimpan di memori
    elif user_id in user_db:
        alamat = user_db[user_id]
    else:
        await update.message.reply_text("⚠️ Wallet tidak ditemukan. Buat dulu dengan `/buat_wallet` atau masukkan manual: `/saldo <alamat>`")
        return

    await update.message.reply_text(f"🔍 Mengecek saldo untuk: `{alamat}`...")

    # Memanggil API Solana Public
    url = "https://api.mainnet-beta.solana.com"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getBalance", "params": [alamat]
    }
    
    try:
        response = requests.post(url, json=payload).json()
        # Konversi Lamports ke SOL
        balance = response['result']['value'] / 1_000_000_000
        await update.message.reply_text(f"💰 **Saldo:** {balance:.4f} SOL", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengambil data: {str(e)}")

def setup(application):
    # Daftarkan kedua perintah sekaligus agar saling terhubung
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
