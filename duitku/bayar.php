<?php
// Pemakaian:
//   Tagihan  : /duitku/bayar.php?tagihan=123
//   Bulanan  : /duitku/bayar.php?bulanan=KODE_PELANGGAN   (dari halaman bulanan.php)
require __DIR__ . '/lib.php';

$bersih = fn($v) => preg_replace('/[^A-Za-z0-9_.@-]/', '', (string) $v);
$tagihan_id = $bersih($_GET['tagihan'] ?? '');
$kode       = $bersih($_GET['bulanan'] ?? '');
if ($tagihan_id === '' && $kode === '') { http_response_code(400); exit('Data tidak valid.'); }

try {
    $db = db();

    if ($kode !== '') {
        $p = cari_pelanggan_bulanan($db, $kode);
        if (!$p) exit('Pelanggan tidak ditemukan.');
        $periode = date('Ym');
        $q = $db->prepare("SELECT 1 FROM duitku_bulanan WHERE pelanggan_id = ? AND periode = ?");
        $q->execute([$p['pelanggan_id'], $periode]);
        if ($q->fetchColumn()) exit('Langganan bulan ini sudah lunas. Terima kasih.');

        $jenis = 'BULANAN';
        $ref   = $p['pelanggan_id'];
        $t     = $p + ['produk' => 'Internet Serbabisa ' . $p['paket'] . ' ' . date('m/Y')];
        $prefix = 'BL';
    } else {
        $t = ambil_tagihan($db, $tagihan_id);
        if (!$t) exit('Tagihan tidak ditemukan atau sudah lunas.');
        $jenis   = 'TAGIHAN';
        $ref     = $tagihan_id;
        $periode = null;
        $prefix  = 'SB';
    }
    if ($t['jumlah'] <= 0) exit('Jumlah tagihan tidak valid.');

    // Pakai lagi link bayar yang masih berlaku untuk data & jumlah yang sama
    $q = $db->prepare("SELECT payment_url FROM duitku_transaksi
                        WHERE jenis = ? AND tagihan_id = ? AND jumlah = ? AND status = 'PENDING'
                          AND (periode <=> ?) AND dibuat > NOW() - INTERVAL ? MINUTE
                        ORDER BY id DESC LIMIT 1");
    $q->execute([$jenis, $ref, $t['jumlah'], $periode, (int) $cfg['expiry_menit'] - 10]);
    if ($url = $q->fetchColumn()) { header('Location: ' . $url); exit; }

    $order_id = $prefix . preg_replace('/[^A-Za-z0-9]/', '', $ref) . '-' . time();
    $res = duitku_buat_invoice([
        'paymentAmount'   => $t['jumlah'],
        'merchantOrderId' => $order_id,
        'productDetails'  => $t['produk'],
        'email'           => $t['email'],
        'phoneNumber'     => $t['no_hp'],
        'customerVaName'  => mb_substr($t['nama'], 0, 20),
        'callbackUrl'     => $cfg['callback_url'],
        'returnUrl'       => $cfg['return_url'],
        'expiryPeriod'    => (int) $cfg['expiry_menit'],
    ]);

    $db->prepare("INSERT INTO duitku_transaksi (order_id, jenis, tagihan_id, periode, jumlah, reference, payment_url) VALUES (?,?,?,?,?,?,?)")
       ->execute([$order_id, $jenis, $ref, $periode, $t['jumlah'], $res['reference'] ?? null, $res['paymentUrl']]);

    header('Location: ' . $res['paymentUrl']);
} catch (Throwable $e) {
    catat('bayar.php: ' . $e->getMessage());
    http_response_code(500);
    echo 'Maaf, pembayaran sedang tidak bisa diproses. Silakan coba lagi.';
}
