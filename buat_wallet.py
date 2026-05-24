import sqlite3
import requests
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# --- INISIALISASI DATABASE ---
def init_db():
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_wallets (
            user_id INTEGER PRIMARY KEY,
            public_key TEXT,
            private_key TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

async def buat_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Simulasi pembuatan wallet (Ganti dengan fungsi keypair asli Anda)
    pub_key = "AwLRfaR3wjgm7wdv7JFSkdxY45ymvpcQxS4zqVbBQXHt"
    priv_key = "5K...PRIVATE_KEY_RAHASIA_ANDA...8J" # Jangan disebar!

    # 1. SIMPAN KE DATABASE
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_wallets VALUES (?, ?, ?)', (user_id, pub_key, priv_key))
    conn.commit()
    conn.close()

    # 2. KIRIM PUBLIC KEY KE CHAT SEKARANG (GRUP/PRIVATE)
    await update.message.reply_text(
        f"✅ **Wallet Berhasil Dibuat!**\n\n"
        f"🔗 **Public Key:** `{pub_key}`\n"
        f"⚠️ *Private Key telah dikirim ke pesan pribadi (DM) Anda demi keamanan.*",
        parse_mode="Markdown"
    )

    # 3. KIRIM PRIVATE KEY KE DM (PESAN RAHASIA)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 **PRIVATE KEY ANDA (RAHASIA)**\n\n"
                 f"Alamat: `{pub_key}`\n"
                 f"Key: `{priv_key}`\n\n"
                 f"❗ **JANGAN PERNAH** memberikan key ini kepada siapapun!",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text("❌ Gagal mengirim DM. Pastikan Anda sudah menekan /start di chat pribadi dengan bot ini!")

async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # AMBIL DARI DATABASE
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT public_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        target_address = row[0]
        await update.message.reply_text(f"🔍 Mengecek saldo otomatis untuk: `{target_address}`...")
        # Lanjut logika API Solana...
    else:
        await update.message.reply_text("⚠️ Anda belum memiliki wallet. Ketik /buat_wallet dulu.")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
