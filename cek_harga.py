import requests
from telegram.ext import CommandHandler, ContextTypes

# Fungsi utama untuk mengecek harga
async def harga_command(update, context):
    if not context.args:
        await update.message.reply_text("⚠️ Format salah! Ketik: /harga <nama_token>")
        return

    query = context.args[0].strip()
    await update.message.reply_text(f"📊 Mencari data harga untuk {query}...")

    # Menambahkan headers agar request tidak dianggap sebagai bot asing/jahat
    url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if not data.get("pairs"):
            await update.message.reply_text("❌ Token tidak ditemukan atau data kosong.")
            return

        # Prioritas mencari pasangan di jaringan Solana
        solana_pairs = [p for p in data["pairs"] if p.get("chainId") == "solana"]
        
        if solana_pairs:
            pair = solana_pairs[0] # Ambil hasil pertama dari Solana
        else:
            pair = data["pairs"][0] # Jika tidak ada Solana, ambil yang pertama tersedia

        simbol = pair.get('baseToken', {}).get('symbol', 'Token')
        harga_usd = pair.get('priceUsd', '0')
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        fdv = pair.get('fdv', 0)
        dex = pair.get('dexId', 'Unknown').capitalize()
        chain = pair.get('chainId', 'Unknown')

        pesan = (
            f"✅ **Info Harga {simbol} ({chain})**\n\n"
            f"💵 **Harga:** ${harga_usd}\n"
            f"💧 **Liquidity:** ${liquidity:,.0f}\n"
            f"📈 **Vol 24h:** ${volume_24h:,.0f}\n"
            f"🏦 **FDV:** ${fdv:,.0f}\n"
            f"🏢 **DEX:** {dex}\n"
            f"🔗 [Lihat Chart DexScreener]({pair.get('url')})"
        )
        await update.message.reply_text(pesan, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal terhubung ke server harga: {str(e)}")

# Fungsi setup agar bisa didaftarkan ke main.py
def setup(application):
    application.add_handler(CommandHandler("harga", harga_command))
