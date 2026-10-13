<?php
// Halaman tujuan setelah pelanggan selesai di halaman Duitku.
// Status final tetap dari callback.php, halaman ini hanya informasi.
require __DIR__ . '/lib.php';

$orderId = $_GET['merchantOrderId'] ?? '';
$status  = 'PENDING';
if ($orderId !== '') {
    $q = db()->prepare("SELECT status FROM duitku_transaksi WHERE order_id = ?");
    $q->execute([$orderId]);
    $status = $q->fetchColumn() ?: 'PENDING';
}
$pesan = [
    'LUNAS'   => 'Pembayaran berhasil. Terima kasih, layanan internet Anda aktif.',
    'GAGAL'   => 'Pembayaran gagal atau dibatalkan. Silakan coba lagi.',
    'PENDING' => 'Pembayaran sedang diproses. Status akan diperbarui otomatis dalam beberapa menit.',
][$status];
?>
<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Status Pembayaran - Serbabisa</title>
<style>body{font-family:sans-serif;max-width:480px;margin:60px auto;padding:0 16px;text-align:center}a{display:inline-block;margin-top:24px}</style>
</head><body>
<h2>Status Pembayaran</h2>
<p><?= htmlspecialchars($pesan) ?></p>
<a href="/portal.php">Kembali ke portal</a>
</body></html>
