import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ⚙️ PENGATURAN BOT & AKUN (GANTI DI SINI)
# ==========================================
TOKEN = "8775208436:AAGjPD9l-Q6ka8u_LqN5xHVNArDy0SWQMeE"

ADMIN_CHAT_ID = "7866687191" 

# Kontak Admin jika ada kendala
USERNAME_ADMIN = "@ndroffisialcenterr"

# ==========================================
# 📋 DAFTAR HARGA (DAPAT DIEDIT KAPAN SAJA)
# ==========================================
TEKS_DAFTAR_HARGA = (
    "📊 **DAFTAR HARGA SUNTIK SOSMED NDR STORE**\n"
    "────────────────────────────\n\n"
    "📸 **INSTAGRAM**\n"
    "• 1.000 Followers: Rp 10.000\n"
    "• 1.000 Likes: Rp 5.000\n\n"
    "🎵 **TIKTOK**\n"
    "• 1.000 Followers: Rp 15.000\n"
    "• 1.000 Views: Rp 2.000\n\n"
    "▶️ **YOUTUBE**\n"
    "• 1.000 Subscribers: Rp 50.000\n"
    "────────────────────────────\n"
    "💡 *Harga dapat berubah sewaktu-waktu.*"
)

# Format Order yang akan ditampilkan ke pembeli
TEKS_FORMAT_ORDER = (
    "📝 **FORMAT ORDER NDR STORE**\n\n"
    "Silakan salin dan isi format berikut, lalu kirim ke chat ini:\n\n"
    "```text\n"
    "Layanan: (Contoh: Instagram Followers)\n"
    "Jumlah: (Contoh: 1000)\n"
    "Target/Link: (Link akun/postingan kamu)\n"
    "Total Tagihan: (Contoh: 10000)\n"
    "```\n\n"
    "⚠️ *Pastikan mengisi angka pada Total Tagihan agar bot dapat menghitung otomatis.*"
)

# ==========================================
# 🤖 LOGIKA PEMROGRAMAN BOT
# ==========================================

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks_sapaan = (
        "👋 **Selamat datang di NDR Store!**\n\n"
        "Pusat layanan suntik sosmed murah, cepat, dan terpercaya. "
        "Klik tombol di bawah untuk melihat daftar harga dan melakukan pemesanan."
    )
    keyboard = [[InlineKeyboardButton("🛒 Menu Utama", callback_data="menu_utama")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(teks_sapaan, reply_markup=reply_markup, parse_mode="Markdown")

# Penanganan Tombol Klik (Inline Keyboard)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_utama":
        keyboard = [[InlineKeyboardButton("📝 Format Order", callback_data="format_order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=TEKS_DAFTAR_HARGA, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data == "format_order":
        await query.message.reply_text(TEKS_FORMAT_ORDER, parse_mode="Markdown")

# Memproses pesan teks (Penerimaan Format Order & Deteksi Nominal)
async def proses_pesanan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = update.message.text
    user = update.message.from_user

    # Deteksi nominal harga dari teks menggunakan Regex
    angka_ditemukan = re.findall(r'\d+', teks.replace('.', '').replace(',', ''))
    
    nominal_str = "Sesuai Orderan"
    if angka_ditemukan:
        nominal = max([int(a) for a in angka_ditemukan if int(a) >= 1000], default=None)
        if nominal:
            nominal_str = f"Rp {nominal:,}".replace(',', '.')

    # 1. Kirim pesan pembayaran & foto QRIS
    caption_bayar = (
        f"💳 **INFORMASI PEMBAYARAN**\n\n"
        f"Silakan lakukan pembayaran sebesar **{nominal_str}** melalui QRIS di atas.\n\n"
        f"📸 **Petunjuk Kirim Bukti:**\n"
        f"Setelah berhasil transfer, harap kirimkan foto **bukti pembayaran/resi** ke chat ini."
    )

    try:
        with open('qris.jpg', 'rb') as qris_file:
            pesan_qris = await update.message.reply_photo(photo=qris_file, caption=caption_bayar, parse_mode="Markdown")
            context.user_data['pesan_qris_id'] = pesan_qris.message_id
    except FileNotFoundError:
        pesan_qris = await update.message.reply_text(f"⚠️ QRIS Pembayaran:\n\n{caption_bayar}", parse_mode="Markdown")
        context.user_data['pesan_qris_id'] = pesan_qris.message_id

    # 2. Kirim Contoh Gambar Bukti Transfer (jika file tersedia)
    try:
        with open('contoh_bukti.jpg', 'rb') as contoh_file:
            pesan_contoh = await update.message.reply_photo(
                photo=contoh_file, 
                caption="📌 **Contoh Bukti Transfer yang Benar:**\nKirimkan resi/struk transfer seperti contoh gambar di atas ya."
            )
            context.user_data['pesan_contoh_id'] = pesan_contoh.message_id
    except FileNotFoundError:
        pass 

    # Teruskan format pemesanan ke Admin
    pesan_admin = (
        f"📥 **PESANAN MASUK BARU!**\n\n"
        f"👤 Pembeli: {user.full_name} (@{user.username})\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"📝 Detail:\n{teks}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=pesan_admin, parse_mode="Markdown")

# Memproses foto bukti transfer
async def proses_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # 1. Hapus pesan QRIS & Contoh Bukti sebelumnya
    if 'pesan_qris_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['pesan_qris_id'])
        except Exception:
            pass 

    if 'pesan_contoh_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['pesan_contoh_id'])
        except Exception:
            pass 

    # 2. Teruskan Bukti Transfer ke Admin
    caption_admin = f"🧾 **BUKTI PEMBAYARAN** dari {user.full_name} (@{user.username})\nID: `{user.id}`"
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=caption_admin, parse_mode="Markdown")

    # 3. Balasan ke Pembeli
    pesan_konfirmasi = (
        "✅ **Bukti Pembayaran Diterima!**\n\n"
        "Orderan dan pembayaran kamu sudah masuk. Saat ini orderan sedang **diproses oleh admin**.\n"
        "⏱ **Estimasi Selesai:** 5 - 10 menit setelah orderan & pembayaran masuk.\n\n"
        "Mohon ditunggu ya! Jika ada kendala, kamu bisa langsung hubungi admin "
        f"di {USERNAME_ADMIN}.\n\n"
        "🙏 *Terima kasih telah order di NDR Store!*"
    )
    await update.message.reply_text(pesan_konfirmasi, parse_mode="Markdown")

# Main Function
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), proses_pesanan))
    app.add_handler(MessageHandler(filters.PHOTO, proses_bukti))

    print("🤖 Bot NDR Store sedang berjalan...")
    app.run_polling()