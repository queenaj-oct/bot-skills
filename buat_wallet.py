from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from solders.keypair import Keypair
import base58

async def buat_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    private_key_b58 = base58.b58encode(bytes(keypair)).decode('utf-8')

    # MENYIMPAN KE MEMORI BOT
    context.user_data['my_wallet'] = public_key
    
    pesan = (
        f"🆕 **Wallet Solana Baru Berhasil Dibuat!**\n\n"
        f"🔑 **Public Key:** `{public_key}`\n"
        f"✅ *Alamat ini telah disimpan di memori bot.*"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # MENGECEK APAKAH ADA ALAMAT DISIMPAN
    wallet_tersimpan = context.user_data.get('my_wallet')
    
    # Jika user mengetik /saldo, cek jika ada alamat yang diketik, jika tidak pakai yang tersimpan
    alamat = context.args[0] if context.args else wallet_tersimpan
    
    if not alamat:
        await update.message.reply_text("⚠️ Harap masukkan alamat wallet atau buat wallet baru dengan /buat_wallet")
        return

    # Lanjutkan dengan kode cek saldo Anda...
    await update.message.reply_text(f"🔍 Mengecek saldo untuk: `{alamat}`...", parse_mode="Markdown")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_command))
    application.add_handler(CommandHandler("saldo", saldo_command))
