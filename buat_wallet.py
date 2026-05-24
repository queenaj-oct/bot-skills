import sqlite3
import requests
import json
import ast
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer

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
        f"✅ **Wallet Solana Berhasil Dibuat!**\n\n"
        f"🔗 **Public Key:** `{pub_key}`\n\n"
        f"⚠️ Private Key dikirim ke DM Anda.",
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 **PRIVATE KEY RAHASIA**\n\nAlamat: `{pub_key}`\nKey: `{priv_key}`",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text("❌ Gagal kirim DM. Klik /start di chat pribadi bot!")

# --- FUNGSI CEK SALDO ---
async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT public_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    alamat = context.args[0] if context.args else (row[0] if row else None)
    if not alamat:
        await update.message.reply_text("⚠️ Buat wallet dulu atau masukkan alamat.")
        return

    payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [alamat]}
    try:
        res = requests.post(RPC_URL, json=payload).json()
        bal = res['result']['value'] / 1_000_000_000
        await update.message.reply_text(f"💰 **Saldo:** `{bal:.4f} SOL`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Gagal cek saldo.")

# --- FITUR BARU: WITHDRAW (KIRIM SALDO) ---
async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Validasi input: /withdraw <alamat_tujuan> <jumlah>
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format: `/withdraw <alamat_tujuan> <jumlah>`\nContoh: `/withdraw AddressAura... 0.1`", parse_mode="Markdown")
        return

    dest_address = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("❌ Jumlah harus angka.")
        return

    # 1. Ambil Private Key dari Database
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT private_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Anda belum punya wallet di bot ini.")
        return

    try:
        await update.message.reply_text(f"⏳ Memproses pengiriman {amount} SOL...")

        # 2. Siapkan Akun Pengirim
        secret_list = ast.literal_eval(row[0]) # Mengubah string list kembali ke list asli
        sender_keypair = Keypair.from_bytes(bytes(secret_list))
        
        # 3. Buat Instruksi Transfer
        receiver_pubkey = Pubkey.from_string(dest_address)
        lamports = int(amount * 1_000_000_000)
        
        # Ambil blockhash terbaru
        recent_blockhash = solana_client.get_latest_blockhash().value.blockhash
        
        # Buat transaksi
        txn = Transaction(
            instructions=[
                transfer(TransferParams(from_pubkey=sender_keypair.pubkey(), to_pubkey=receiver_pubkey, lamports=lamports))
            ],
            recent_blockhash=recent_blockhash,
            fee_payer=sender_keypair.pubkey()
        )
        
        # 4. Kirim & Konfirmasi
        result = solana_client.send_transaction(txn, sender_keypair)
        signature = result.value
        
        await update.message.reply_text(
            f"🚀 **Transaksi Berhasil Dikirim!**\n\n"
            f"✅ **Jumlah:** {amount} SOL\n"
            f"📍 **Ke:** `{dest_address}`\n"
            f"🔗 [Lihat di Solscan](https://solscan.io/tx/{signature})",
            parse_mode="Markdown", disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Transaksi Gagal: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
    application.add_handler(CommandHandler("withdraw", withdraw_cmd))
