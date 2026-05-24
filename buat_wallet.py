import sqlite3
import requests
import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from solders.keypair import Keypair

# --- INISIALISASI DATABASE ---
# Fungsi ini memastikan tabel tersedia untuk menyimpan wallet secara permanen
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

# Jalankan inisialisasi saat modul dimuat
init_db()

async def buat_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # --- GENERATOR ASLI SOLANA ---
    # Membuat keypair baru yang valid di jaringan Solana
    account = Keypair()
    pub_key = str(account.pubkey())
    # Private key disimpan dalam format list angka agar mudah dibaca/disimpan
    priv_key = str(list(account.secret())) 

    # 1. SIMPAN KE DATABASE SQLITE
    try:
        conn = sqlite3.connect('wallets.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO user_wallets VALUES (?, ?, ?)', (user_id, pub_key, priv_key))
        conn.commit()
        conn.close()
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal menyimpan ke database: {str(e)}")
        return

    # 2. KIRIM KONFIRMASI KE CHAT (GRUP/PRIVATE)
    # Hanya menampilkan Public Key demi keamanan
    await update.message.reply_text(
        f"✅ **Wallet Solana Berhasil Dibuat!**\n\n"
        f"🔗 **Public Key:** `{pub_key}`\n\n"
        f"⚠️ **PENTING:** Private Key telah dikirim secara rahasia ke DM (Pesan Pribadi) Anda. "
        f"Segera cek dan simpan di tempat aman!",
        parse_mode="Markdown"
    )

    # 3. KIRIM PRIVATE KEY KE DM (PESAN RAHASIA)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 **PRIVATE KEY RAHASIA ANDA**\n\n"
                 f"Alamat: `{pub_key}`\n"
                 f"Key (Array): `{priv_key}`\n\n"
                 f"❗ **PERINGATAN:** Jangan pernah membagikan kunci ini kepada siapa pun. "
                 f"Jika bot ini di-restart di Railway, data di database mungkin hilang jika Anda tidak menggunakan Volume. "
                 f"Harap catat kunci ini secara manual!",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(
            "❌ **Gagal mengirim Private Key via DM!**\n"
            "Bot tidak bisa mengirim pesan pribadi jika Anda belum pernah mengaktifkannya. "
            "Silakan cari bot ini di Telegram, klik **START**, lalu coba buat wallet lagi."
        )

async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. CEK DATABASE UNTUK ALAMAT TERSIMPAN
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT public_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    # Tentukan alamat mana yang akan dicek
    if context.args:
        # Jika user ketik manual: /saldo <alamat>
        target_address = context.args[0]
    elif row:
        # Jika user tidak ketik alamat, ambil dari database
        target_address = row[0]
    else:
        await update.message.reply_text("⚠️ Anda belum membuat wallet. Ketik /buat_wallet dulu.")
        return

    await update.message.reply_text(f"🔍 Mengecek saldo untuk: `{target_address}`...")

    # 2. AMBIL SALDO DARI BLOCKCHAIN SOLANA
    url = "https://api.mainnet-beta.solana.com"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getBalance", "params": [target_address]
    }
    
    try:
        response = requests.post(url, json=payload).json()
        if 'result' in response:
            lamports = response['result']['value']
            sol_balance = lamports / 1_000_000_000
            await update.message.reply_text(
                f"💰 **Saldo Wallet Anda**\n"
                f"Alamat: `{target_address}`\n"
                f"Jumlah: `{sol_balance:.4f} SOL`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Gagal mendapatkan saldo dari jaringan.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error koneksi: {str(e)}")

def setup(application):
    # Daftarkan handler ke aplikasi utama
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
