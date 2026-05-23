import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mengecek apakah user memasukkan alamat wallet setelah command
    if not context.args:
        await update.message.reply_text("⚠️ Format salah!\nKetik: /saldo <alamat_wallet_solana>")
        return

    wallet_address = context.args[0].strip()
    
    # Mengambil RPC dari Railway, jika kosong gunakan public RPC default
    rpc_url = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com").strip()

    await update.message.reply_text(f"🔍 Mengecek saldo di blockchain...\nWallet: `{wallet_address}`", parse_mode="Markdown")

    # Format standar komunikasi RPC ke Solana
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(rpc_url, headers=headers, json=payload, timeout=10)
        data = response.json()

        # Menangani jika alamat wallet tidak valid menurut server Solana
        if "error" in data:
            error_msg = data['error'].get('message', 'Alamat wallet tidak valid.')
            await update.message.reply_text(f"❌ Gagal: {error_msg}")
            return

        # Solana merespons dalam satuan terkecil (Lamports). 1 SOL = 1.000.000.000 Lamports
        lamports = data.get("result", {}).get("value", 0)
        sol_balance = lamports / 1_000_000_000

        # Mengirimkan hasil akhir ke Telegram
        pesan_balasan = (
            f"🏦 **Informasi Saldo**\n"
            f"Address: `{wallet_address[:6]}...{wallet_address[-4:]}`\n"
            f"Saldo: **{sol_balance:.5f} SOL**"
        )
        await update.message.reply_text(pesan_balasan, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Koneksi RPC gagal: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("saldo", saldo_command))

