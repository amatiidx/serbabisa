import sys
import requests

# Ganti URL ini sesuai dengan endpoint go-stock-api yang aktif di VPS Anda
API_URL = "http://localhost:8080/api/stocks" 

def send_telegram_message(message):
    # Sesuaikan fungsi pengiriman Telegram yang sudah ada di proyek Anda
    # Contoh menggunakan token bot dan chat ID langsung atau memanggil fungsi modul lain
    import os
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Gagal mengirim ke Telegram: {e}")

def scan_market_dynamically(kategori):
    try:
        print(f"Menjalankan pemindaian untuk kategori: {kategori}...")
        response = requests.get(API_URL)
        
        if response.status_code != 200:
            print(f"Gagal mengambil data dari API, status code: {response.status_code}")
            return
            
        stocks_data = response.json()
        hasil_filter = []
        
        for stock in stocks_data:
            ticker = stock.get('ticker') or stock.get('symbol')
            price_now = stock.get('close', 0)
            volume = stock.get('volume', 0)
            change_pct = stock.get('change_percentage', 0)
            
            # --- KRITERIA PENYARINGAN OTOMATIS ---
            # Contoh: Menyaring saham yang mengalami lonjakan volume (> 500.000) 
            # dan sedang mengalami kenaikan harga (change > 0)
            if volume > 500000 and change_pct > 0:
                hasil_filter.append(
                    f"• *{ticker}*: Rp {price_now} "
                    f"(+{change_pct}%) | Vol: {format(volume, ',')}"
                )
                
        # Kirim hasil ke Telegram jika ada emiten yang lolos kriteria
        if hasil_filter:
            pesan = f"🔥 *[SERBABISA.ID] SCANNER OTOMATIS: {kategori.upper()}* 🔥\n\n"
            pesan += "\n".join(hasil_filter)
            send_telegram_message(pesan)
            print("Hasil scanner berhasil dikirim ke Telegram.")
        else:
            print("Tidak ada saham yang memenuhi kriteria pada sesi ini.")
            
    except Exception as e:
        print(f"Terjadi kesalahan saat memproses data pasar: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        kategori_arg = sys.argv[1]
        scan_market_dynamically(kategori_arg)
    else:
        print("Mohon sertakan argumen kategori (contoh: python auto_scanner.py rekomendasi)")
