import sqlite3
import requests
import ast
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Library Solana
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

# --- CONFIG ---
RPC_URL = "https://api.mainnet-beta.solana.com"
solana_client = Client(RPC_URL)

# --- DATABASE INIT ---
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

# --- FUNGSI UTAMA ---
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

    await update.message.reply_text(f"✅ **Wallet Berhasil Dibuat!**\n🔗 `{pub_key}`\n⚠️ Cek Private Key di DM.", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=user_id, text=f"🔐 **PRIVATE KEY RAHASIA**\nKey: `{priv_key}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Klik /start di DM bot untuk terima Key!")

async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT public_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    alamat = row[0] if row else None
    if not alamat:
        await update.message.reply_text("⚠️ Buat wallet dulu.")
        return

    res = solana_client.get_balance(Pubkey.from_string(alamat))
    bal = res.value / 1_000_000_000
    await update.message.reply_text(f"💰 **Saldo:** `{bal:.4f} SOL`", parse_mode="Markdown")

# --- LOGIKA AUTO-BUY (SNIPER) ---
async def handle_ca_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Deteksi format Contract Address Solana (biasanya 32-44 karakter alfanumerik)
    ca_match = re.search(r'[1-9A-HJ-NP-Za-km-z]{32,44}', text)
    
    if ca_match:
        ca = ca_match.group(0)
        await update.message.reply_text(f"🔍 Mendeteksi CA: `{ca}`\nSedang mengambil data token...", parse_mode="Markdown")
        
        # Ambil data dari DexScreener
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={ca}"
            data = requests.get(url).json()
            
            if not data.get("pairs"):
                return # Bukan token valid atau belum ada pair

            pair = data["pairs"][0]
            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "TOKEN")
            price = pair.get("priceUsd", "0")
            liquidity = pair.get("liquidity", {}).get("usd", 0)

            msg = (
                f"💎 **Token Ditemukan: {name} ({symbol})**\n"
                f"💵 Harga: `${price}`\n"
                f"💧 Liquidity: `${liquidity:,.0f}`\n\n"
                f"Pilih jumlah SOL untuk membeli:"
            )

            # Tombol Beli Instan
            keyboard = [
                [
                    InlineKeyboardButton("Buy 0.1 SOL", callback_data=f"buy|0.1|{ca}"),
                    InlineKeyboardButton("Buy 0.5 SOL", callback_data=f"buy|0.5|{ca}")
                ],
                [
                    InlineKeyboardButton("Buy 1.0 SOL", callback_data=f"buy|1.0|{ca}"),
                    InlineKeyboardButton("Buy X SOL", callback_data=f"buy|X|{ca}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            print(f"Error Dex: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    action = data[0]
    amount = data[1]
    ca = data[2]

    if action == "buy":
        await query.edit_message_text(f"⏳ Memulai pembelian {amount} SOL untuk token `{ca}`...\n(Fitur eksekusi transaksi memerlukan saldo SOL).", parse_mode="Markdown")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
    # Handler untuk mendeteksi Contract Address otomatis
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_detection))
    # Handler untuk tombol beli
    application.add_handler(CallbackQueryHandler(handle_callback))

