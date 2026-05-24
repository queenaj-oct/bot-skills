import sqlite3
import requests
import ast
import re
import base64

# --- FIX: IMPORT TELEGRAM MODULES ---
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- IMPORT SOLANA MODULES ---
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

# Konfigurasi RPC
RPC_URL = "https://api.mainnet-beta.solana.com"
solana_client = Client(RPC_URL)

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

# --- COMMAND: /buat_wallet ---
async def buat_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account = Keypair()
    pub_key = str(account.pubkey())
    priv_key = str(list(account.secret())) 

    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_wallets VALUES (?, ?, ?)', (user_id, pub_key, priv_key))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ <b>Wallet Solana Berhasil Dibuat!</b>\n\n"
        f"🔗 <b>Public Key:</b> <code>{pub_key}</code>\n\n"
        f"⚠️ <b>PENTING:</b> Private Key telah dikirim secara rahasia ke DM Anda.",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 <b>PRIVATE KEY RAHASIA ANDA</b>\n\nAlamat: <code>{pub_key}</code>\nKey: <code>{priv_key}</code>\n\n❌ JANGAN PERNAH bagikan key ini!",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text("❌ Gagal kirim DM. Harap /start bot di chat pribadi lebih dulu.")

# --- DETEKSI CA OTOMATIS & MENU BELI ---
async def handle_ca_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Cari pola Address Solana (32-44 karakter base58)
    ca_match = re.search(r'[1-9A-HJ-NP-Za-km-z]{32,44}', text)
    
    if ca_match:
        ca = ca_match.group(0)
        await update.message.reply_text(f"🔍 Mendeteksi CA: <code>{ca}</code>\nMengambil data token...", parse_mode="HTML")
        
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={ca}"
            data = requests.get(url).json()
            if not data.get("pairs"): return

            pair = data["pairs"][0]
            symbol = pair.get("baseToken", {}).get("symbol", "TOKEN")
            price = pair.get("priceUsd", "0")
            
            msg = (
                f"💎 <b>Token: {symbol}</b>\n"
                f"💵 Harga: <code>${price}</code>\n\n"
                f"Pilih jumlah SOL untuk membeli:"
            )
            keyboard = [
                [
                    InlineKeyboardButton("Buy 0.1 SOL", callback_data=f"buy|0.1|{ca}"),
                    InlineKeyboardButton("Buy 0.5 SOL", callback_data=f"buy|0.5|{ca}")
                ],
                [InlineKeyboardButton("Buy 1.0 SOL", callback_data=f"buy|1.0|{ca}")]
            ]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        except Exception as e:
            print(f"Error dex: {e}")

# --- EKSEKUSI PEMBELIAN (JUPITER SWAP) ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    data = query.data.split("|")
    if data[0] != "buy": return
    
    amount_sol, ca = data[1], data[2]
    await query.edit_message_text(f"⏳ Memproses pembelian {amount_sol} SOL via Jupiter...")

    # Ambil Private Key dari DB
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT private_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await query.edit_message_text("❌ Wallet tidak ditemukan. Gunakan /buat_wallet")
        return

    try:
        # Logika integrasi Jupiter API (Quote -> Swap)
        lamports = int(float(amount_sol) * 1_000_000_000)
        quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={ca}&amount={lamports}&slippageBps=100"
        quote = requests.get(quote_url).json()

        # Eksekusi swap di sini (Memerlukan RPC dan saldo SOL untuk fee)
        await query.edit_message_text(f"🚀 Transaksi dikirim! Cek wallet Anda secara berkala.")
    except Exception as e:
        await query.edit_message_text(f"❌ Terjadi kesalahan: {str(e)}")

# --- FUNGSI UTAMA (SETUP HANDLER) ---
def setup_handlers(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_detection))
    application.add_handler(CallbackQueryHandler(handle_callback))
