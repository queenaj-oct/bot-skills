import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def harga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Cek apakah user memasukkan alamat token
    if not context.args:
        await update.message.reply_text("⚠️ Format salah!\nKetik: /harga <alamat_kontrak_token>")
        return

    token_address = context.args[0].strip()
    await update.message.reply_text(f"📊 Mengambil data harga untuk `{token_address[:4]}...{token_address[-4:]}`...", parse_mode="Markdown")

    # Menggunakan API gratis dari DexScreener
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        # Cek apakah token ada di database DexScreener
        if not data.get("pairs"):
            await update.message.reply_text("❌ Token tidak ditemukan atau belum memiliki Liquidity Pool di DEX.")
            return

        # Mengambil data dari pair pertama (biasanya yang paling liquid)
        pair = data["pairs"][0]
        simbol = pair.get("baseToken", {}).get("symbol", "Token")
        harga_usd = pair.get("priceUsd", "0")
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        volume_24h = pair.get("volume", {}).get("h24", 0)
        fdv = pair.get("fdv", 0)
        dex = pair.get("dexId", "Unknown").capitalize()

        pesan = (
            f"📈 **Info Harga {simbol}**\n\n"
            f"💲 **Harga:** ${harga_usd}\n"
            f"💧 **Liquidity:** ${liquidity:,.0f}\n"
            f"📊 **Vol 24h:** ${volume_24h:,.0f}\n"
            f"💰 **FDV:** ${fdv:,.0f}\n"
            f"🏦 **DEX:** {dex}\n\n"
            f"🔗 [Lihat Chart DexScreener]({pair.get('url')})"
        )
        await update.message.reply_text(pesan, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal terhubung ke server harga: {str(e)}")

def setup(application):
    application.add_handler(CommandHandler("harga", harga_command))

