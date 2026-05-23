from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from solana.rpc.api import Client
from solders.keypair import Keypair # Pustaka untuk generate wallet

async def buat_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Membuat keypair baru
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    private_key = str(keypair.secret()) # Ini adalah raw bytes yang perlu di-encode jika ingin ditampilkan
    
    # Mengonversi secret key ke format base58 (format yang biasa di-import ke Phantom/Solflare)
    import base58
    private_key_b58 = base58.b58encode(bytes(keypair)).decode('utf-8')

    pesan = (
        f"🆕 **Wallet Solana Baru Berhasil Dibuat!**\n\n"
        f"🔑 **Public Key (Address):**\n`{public_key}`\n\n"
        f"🔐 **Private Key:**\n`{private_key_b58}`\n\n"
        f"⚠️ **PERINGATAN:** Simpan Private Key Anda dengan aman! "
        f"Siapa pun yang memegang kunci ini bisa mengakses dana Anda."
    )
    
    await update.message.reply_text(pesan, parse_mode="Markdown")

def setup(application):
    application.add_handler(CommandHandler("buat_wallet", buat_wallet_command))
