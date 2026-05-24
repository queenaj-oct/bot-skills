import sqlite3
import requests
import ast
import re
import base64

# Import Telegram Modules (Fixed: Update & ContextTypes included)
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
        f"⚠️ <b>PENTING:</b> Private Key telah dikirim ke DM Anda.",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(chat_id=user_id, text=f"🔐 <b>KEY RAHASIA:</b>\n<code>{priv_key}</code>", parse_mode="HTML")
    except: pass

# --- DETEKSI CA & MENU SWAP ---
async def handle_ca_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ca_match = re.search(r'[1-9A-HJ-NP-Za-km-z]{32,44}', text)
    
    if ca_match:
        ca = ca_match.group(0)
        await update.message.reply_text(f"🔍 Mencari data token: <code>{ca}</code>", parse_mode="HTML")
        
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={ca}"
            data = requests.get(url).json()
            pair = data["pairs"][0]
            symbol = pair.get("baseToken", {}).get("symbol", "TOKEN")
            price = pair.get("priceUsd", "0")
            
            msg = f"💎 <b>Token: {symbol}</b>\n💵 Harga: <code>${price}</code>\n\nPilih jumlah SOL untuk Swap:"
            keyboard = [
                [InlineKeyboardButton("0.1 SOL", callback_data=f"buy|0.1|{ca}"),
                 InlineKeyboardButton("0.5 SOL", callback_data=f"buy|0.5|{ca}")],
                [InlineKeyboardButton("1.0 SOL", callback_data=f"buy|1.0|{ca}")]
            ]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        except: pass

# --- CALLBACK EXECUTE SWAP ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] != "buy": return

    amount_sol, ca = data[1], data[2]
    await query.edit_message_text(f"⏳ Sedang melakukan swap {amount_sol} SOL ke token...")
    
    # Logika Jupiter API akan dijalankan di sini menggunakan wallet dari DB
    # (Pastikan saldo SOL mencukupi di wallet bot Anda)

# --- FUNGSI SETUP UNTUK INSTALLER ---
def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_detection))
    application.add_handler(CallbackQueryHandler(handle_callback))
