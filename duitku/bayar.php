<?php
// Pemakaian dari portal:  <a href="/duitku/bayar.php?tagihan=123">Bayar</a>
require __DIR__ . '/lib.php';

$tagihan_id = preg_replace('/[^A-Za-z0-9_-]/', '', $_GET['tagihan'] ?? '');
if ($tagihan_id === '') { http_response_code(400); exit('Tagihan tidak valid.'); }

try {
    $db = db();
    $t  = ambil_tagihan($db, $tagihan_id);
    if (!$t) { exit('Tagihan tidak ditemukan atau sudah lunas.'); }

    // Pakai lagi link bayar yang masih berlaku untuk tagihan & jumlah yang sama
    $q = $db->prepare("SELECT payment_url FROM duitku_transaksi
                        WHERE tagihan_id = ? AND jumlah = ? AND status = 'PENDING'
                          AND dibuat > NOW() - INTERVAL ? MINUTE
                        ORDER BY id DESC LIMIT 1");
    $q->execute([$tagihan_id, $t['jumlah'], (int) $cfg['expiry_menit'] - 10]);
    if ($url = $q->fetchColumn()) { header('Location: ' . $url); exit; }

    $order_id = 'SB' . $tagihan_id . '-' . time();
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

    $db->prepare("INSERT INTO duitku_transaksi (order_id, tagihan_id, jumlah, reference, payment_url) VALUES (?,?,?,?,?)")
       ->execute([$order_id, $tagihan_id, $t['jumlah'], $res['reference'] ?? null, $res['paymentUrl']]);

    header('Location: ' . $res['paymentUrl']);
} catch (Throwable $e) {
    catat('bayar.php: ' . $e->getMessage());
    http_response_code(500);
    echo 'Maaf, pembayaran sedang tidak bisa diproses. Silakan coba lagi.';
}
