import sqlite3
import requests
import ast
import re
import base64

# Import Telegram Modules
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import Solana Modules
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

# Konfigurasi RPC
RPC_URL = "https://api.mainnet-beta.solana.com"
solana_client = Client(RPC_URL)

# --- DATABASE SETUP ---
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

# --- FUNGSI BUAT WALLET ---
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
        f"⚠️ <b>PENTING:</b> Private Key telah dikirim ke DM Anda.",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 <b>PRIVATE KEY RAHASIA ANDA</b>\n\nAlamat: <code>{pub_key}</code>\nKey: <code>{priv_key}</code>",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text("❌ Gagal kirim DM. Silakan /start di chat pribadi bot!")

# --- FUNGSI CEK SALDO ---
async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT public_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("⚠️ Anda belum memiliki wallet. Ketik /buat_wallet")
        return

    try:
        res = solana_client.get_balance(Pubkey.from_string(row[0]))
        bal = res.value / 1_000_000_000
        await update.message.reply_text(f"💰 <b>Saldo:</b> <code>{bal:.4f} SOL</code>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {e}")

# --- DETEKSI CA TOKEN ---
async def handle_ca_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ca_match = re.search(r'[1-9A-HJ-NP-Za-km-z]{32,44}', text)
    
    if ca_match:
        ca = ca_match.group(0)
        await update.message.reply_text(f"🔍 Mendeteksi CA: <code>{ca}</code>\nSedang mengambil data...", parse_mode="HTML")
        
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
        except: pass

# --- CALLBACK BUY ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    if data[0] == "buy":
        await query.edit_message_text(f"⏳ Memulai proses beli {data[1]} SOL untuk token `{data[2]}`...")

# --- FUNGSI SETUP (FIXED) ---
def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_detection))
    application.add_handler(CallbackQueryHandler(handle_callback))
