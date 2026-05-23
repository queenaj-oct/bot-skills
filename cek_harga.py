import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def harga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Format salah!\nKetik: /harga <simbol_token_atau_alamat_kontrak>")
        return

    query = context.args[0].strip()
    await update.message.reply_text(f"📊 Mencari data harga untuk `{query}`...", parse_mode="Markdown")

    # Menggunakan endpoint SEARCH agar bisa mencari pakai nama (misal: SOL) atau Alamat
    url = f"https://api.dexscreener.com/latest/dex/search?q={query}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("pairs"):
            await update.message.reply_text("❌ Token tidak ditemukan atau belum memiliki Liquidity Pool di DEX.")
            return

        # Memprioritaskan pencarian di jaringan Solana agar lebih akurat
        solana_pairs = [p for p in data["pairs"] if p.get("chainId") == "solana"]
        
        # Jika ada di Solana, ambil yang volumenya paling tinggi (biasanya index 0 dari hasil pencarian)
        if solana_pairs:
            pair = solana_pairs[0]
        else:
            # Jika bukan koin Solana, ambil koin jaringan lain yang pertama muncul
            pair = data["pairs"][0]

        simbol = pair.get("baseToken", {}).get("symbol", "Token")
        harga_usd = pair.get("priceUsd", "0")
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        volume_24h = pair.get("volume", {}).get("h24", 0)
        fdv = pair.get("fdv", 0)
        dex = pair.get("dexId", "Unknown").capitalize()
        chain = pair.get("chainId", "Unknown").capitalize()

        pesan = (
            f"📈 **Info Harga {simbol} ({chain})**\n\n"
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
