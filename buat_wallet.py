import sqlite3
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

# RPC Solana
solana_client = Client("https://api.mainnet-beta.solana.com")

# Inisialisasi Database
def init_db():
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS user_wallets (user_id INTEGER PRIMARY KEY, public_key TEXT, private_key TEXT)')
    conn.commit()
    conn.close()

init_db()

# Fitur Buat Wallet
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

    await update.message.reply_text(f"✅ Wallet Dibuat!\nPubkey: <code>{pub_key}</code>", parse_mode="HTML")
    try:
        await context.bot.send_message(chat_id=user_id, text=f"🔐 Private Key: <code>{priv_key}</code>", parse_mode="HTML")
    except: pass

# Deteksi CA Otomatis & Menu Swap
async def handle_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ca = re.search(r'[1-9A-HJ-NP-Za-km-z]{32,44}', update.message.text)
    if ca:
        token_address = ca.group(0)
        # Ambil data dari DexScreener
        res = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_address}").json()
        pair = res["pairs"][0]
        
        msg = (f"🔍 Token: {pair['baseToken']['symbol']}\n"
               f"💵 Harga: ${pair['priceUsd']}\n\n"
               "Pilih jumlah SOL untuk Swap:")
        
        keyboard = [[
            InlineKeyboardButton("0.1 SOL", callback_data=f"buy|0.1|{token_address}"),
            InlineKeyboardButton("0.5 SOL", callback_data=f"buy|0.5|{token_address}")
        ]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# Fungsi Wajib untuk Installer
def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca))
