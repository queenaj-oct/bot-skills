import sqlite3
import requests
import ast
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# Library Solana versi terbaru (Solders)
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
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

    try:
        res = solana_client.get_balance(Pubkey.from_string(alamat))
        bal = res.value / 1_000_000_000
        await update.message.reply_text(f"💰 **Saldo:** `{bal:.4f} SOL`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal cek saldo: {str(e)}")

# --- FITUR WITHDRAW (VERSI FIXED) ---
async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format: `/withdraw <alamat_tujuan> <jumlah>`", parse_mode="Markdown")
        return

    dest_address = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("❌ Jumlah harus angka.")
        return

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

        # Persiapkan Keypair
        secret_list = ast.literal_eval(row[0])
        sender = Keypair.from_bytes(bytes(secret_list))
        receiver = Pubkey.from_string(dest_address)
        
        # Ambil blockhash
        recent_blockhash = solana_client.get_latest_blockhash().value.blockhash
        
        # Buat Instruksi Transfer
        ix = transfer(TransferParams(
            from_pubkey=sender.pubkey(), 
            to_pubkey=receiver, 
            lamports=int(amount * 1_000_000_000)
        ))
        
        # Buat Pesan Transaksi V0 (Standar Terbaru)
        msg = MessageV0.try_compile(
            payer=sender.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash,
        )
        
        # Sign dan Kirim
        tx = VersionedTransaction(msg, [sender])
        result = solana_client.send_transaction(tx)
        
        await update.message.reply_text(
            f"🚀 **Berhasil!**\n✅ **Jumlah:** {amount} SOL\n🔗 [Lihat di Solscan](https://solscan.io/tx/{str(result.value)})",
            parse_mode="Markdown", disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_cmd))
    application.add_handler(CommandHandler("saldo", saldo_cmd))
    application.add_handler(CommandHandler("withdraw", withdraw_cmd))
