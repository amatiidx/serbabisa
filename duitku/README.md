# Modul Pembayaran Duitku - Serbabisa

Pelanggan klik **Bayar** di portal -> diarahkan ke halaman Duitku (QRIS, VA bank,
e-wallet, minimarket) -> setelah bayar, `callback.php` menandai tagihan **LUNAS** otomatis.

## Pasang di VPS (CloudPanel)
1. Upload folder `duitku/` dan `webhook/` ke root situs `master.serbabisa.id` (sejajar `portal.php`).
2. Salin `config.example.php` jadi `config.php`, isi Merchant Code, API Key, dan data database.
3. Jalankan `tabel.sql` sekali di database (phpMyAdmin).
4. Sesuaikan `tagihan.php` dengan nama tabel/kolom tagihan & pelanggan di portal.
5. Dashboard Duitku > My Projects > proyek Anda, isi:
   - Callback URL: `https://master.serbabisa.id/webhook/duitku.php` (sudah terdaftar, file `webhook/duitku.php` meneruskan ke modul ini)
   - Return URL:   `https://master.serbabisa.id/duitku/selesai.php`
6. Di `portal.php`, tambahkan tombol per tagihan:
   `<a href="/duitku/bayar.php?tagihan=<?= $tagihan['id'] ?>">Bayar Online</a>`

## Uji coba
Set `'mode' => 'sandbox'` dan pakai Merchant Code/API Key sandbox dulu.
Kalau tagihan berubah LUNAS setelah bayar simulasi, ganti ke `production`.

## Keamanan
- `config.php` berisi API Key: jangan diupload ke GitHub, jangan dikirim lewat chat.
- Jumlah tagihan selalu diambil dari database, bukan dari URL.
- Callback dicek signature, jumlah, dan status ulang ke Duitku sebelum ditandai lunas.
- Log ada di `duitku/log/`. Blok akses web ke folder itu (CloudPanel > Vhost: `location /duitku/log { deny all; }`).
