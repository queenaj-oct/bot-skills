import base64
from solders.transaction import VersionedTransaction

# --- TAMBAHKAN DI DALAM FUNGSI handle_callback ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    data = query.data.split("|")
    if data[0] != "buy": return

    amount_sol = data[1]
    token_ca = data[2]

    if amount_sol == "X":
        await query.edit_message_text("📝 Silakan ketik jumlah SOL yang ingin dibeli (Contoh: 0.2)")
        return

    await query.edit_message_text(f"⏳ Menyiapkan pembelian {amount_sol} SOL...")

    # 1. Ambil Private Key User
    conn = sqlite3.connect('wallets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT private_key FROM user_wallets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await query.edit_message_text("❌ Wallet tidak ditemukan.")
        return

    try:
        # Konversi Key
        secret_list = ast.literal_eval(row[0])
        keypair = Keypair.from_bytes(bytes(secret_list))
        user_pubkey = str(keypair.pubkey())

        # 2. Ambil Quote dari Jupiter API
        lamports = int(float(amount_sol) * 1_000_000_000)
        quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={token_ca}&amount={lamports}&slippageBps=100"
        quote = requests.get(quote_url).json()

        # 3. Buat Transaksi Swap
        swap_payload = {
            "quoteResponse": quote,
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": True
        }
        swap_res = requests.post("https://quote-api.jup.ag/v6/swap", json=swap_payload).json()
        swap_transaction_base64 = swap_res['swapTransaction']

        # 4. Sign & Kirim Transaksi
        raw_transaction = base64.b64decode(swap_transaction_base64)
        signature = keypair.sign_message(raw_transaction) # Simplified logic for VersionedTx
        
        # Kirim ke RPC
        result = solana_client.send_raw_transaction(raw_transaction)
        
        await query.edit_message_text(
            f"🚀 **Pembelian Berhasil Dikirim!**\n"
            f"💰 Jumlah: {amount_sol} SOL\n"
            f"🔗 [Cek Transaksi](https://solscan.io/tx/{str(result.value)})",
            parse_mode="Markdown", disable_web_page_preview=True
        )

    except Exception as e:
        await query.edit_message_text(f"❌ Gagal Swap: {str(e)}\n(Pastikan saldo SOL cukup untuk gas fee)")
