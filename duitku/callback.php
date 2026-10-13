<?php
// Dipanggil server Duitku (POST) setiap ada pembayaran. Daftarkan URL ini di dashboard Duitku.
require __DIR__ . '/lib.php';

$merchantCode = $_POST['merchantCode']    ?? '';
$amount       = $_POST['amount']          ?? '';
$orderId      = $_POST['merchantOrderId'] ?? '';
$resultCode   = $_POST['resultCode']      ?? '';
$reference    = $_POST['reference']       ?? '';
$paymentCode  = $_POST['paymentCode']     ?? '';
$signature    = $_POST['signature']       ?? '';

catat("callback order=$orderId amount=$amount result=$resultCode ref=$reference");

// 1. Pastikan benar-benar dari Duitku
$cek = md5($merchantCode . $amount . $orderId . $cfg['api_key']);
if ($merchantCode !== $cfg['merchant_code'] || !hash_equals($cek, $signature)) {
    catat("callback DITOLAK: signature salah order=$orderId");
    http_response_code(400);
    exit('Bad Signature');
}

try {
    $db = db();
    $db->beginTransaction();
    $q = $db->prepare("SELECT * FROM duitku_transaksi WHERE order_id = ? FOR UPDATE");
    $q->execute([$orderId]);
    $trx = $q->fetch(PDO::FETCH_ASSOC);

    if (!$trx) {
        $db->rollBack();
        catat("callback: order tidak dikenal $orderId");
        http_response_code(404);
        exit('Order not found');
    }
    if ($trx['status'] === 'LUNAS') {       // callback dobel, sudah diproses
        $db->commit();
        exit('OK');
    }

    if ($resultCode === '00') {
        // 2. Jumlah harus sama & verifikasi ulang ke Duitku
        if ((int) $amount !== (int) $trx['jumlah'] || duitku_cek_status($orderId) !== '00') {
            $db->rollBack();
            catat("callback: jumlah/status tidak cocok order=$orderId");
            http_response_code(400);
            exit('Mismatch');
        }
        $db->prepare("UPDATE duitku_transaksi SET status='LUNAS', reference=?, metode=?, dibayar=NOW() WHERE id=?")
           ->execute([$reference, $paymentCode, $trx['id']]);
        tandai_lunas($db, $trx['tagihan_id'], (int) $amount, $reference);
        catat("LUNAS tagihan={$trx['tagihan_id']} order=$orderId metode=$paymentCode");
    } else {
        $db->prepare("UPDATE duitku_transaksi SET status='GAGAL' WHERE id=? AND status='PENDING'")
           ->execute([$trx['id']]);
    }
    $db->commit();
    echo 'OK';
} catch (Throwable $e) {
    if (isset($db) && $db->inTransaction()) $db->rollBack();
    catat('callback error: ' . $e->getMessage());
    http_response_code(500);
    echo 'Error';
}
