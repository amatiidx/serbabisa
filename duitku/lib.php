<?php
$cfg = require __DIR__ . '/config.php';
require __DIR__ . '/tagihan.php';

function db(): PDO
{
    global $cfg;
    static $db = null;
    if ($db === null) {
        $db = new PDO($cfg['db_dsn'], $cfg['db_user'], $cfg['db_pass'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        ]);
    }
    return $db;
}

function duitku_base(): string
{
    global $cfg;
    return $cfg['mode'] === 'production'
        ? 'https://api-prod.duitku.com/api/merchant'
        : 'https://api-sandbox.duitku.com/api/merchant';
}

function catat(string $pesan): void
{
    $dir = __DIR__ . '/log';
    if (!is_dir($dir)) mkdir($dir, 0750);
    file_put_contents($dir . '/duitku-' . date('Y-m') . '.log', date('c') . ' ' . $pesan . "\n", FILE_APPEND);
}

/** Buat invoice Duitku POP (pelanggan pilih QRIS/VA/e-wallet di halaman Duitku). */
function duitku_buat_invoice(array $data): array
{
    global $cfg;
    $ts  = (string) round(microtime(true) * 1000);
    $sig = hash('sha256', $cfg['merchant_code'] . $ts . $cfg['api_key']);

    $ch = curl_init(duitku_base() . '/createInvoice');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Accept: application/json',
            'x-duitku-signature: ' . $sig,
            'x-duitku-timestamp: ' . $ts,
            'x-duitku-merchantcode: ' . $cfg['merchant_code'],
        ],
        CURLOPT_POSTFIELDS => json_encode($data),
    ]);
    $body = curl_exec($ch);
    $http = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    $res = json_decode((string) $body, true);
    if ($http !== 200 || !is_array($res) || empty($res['paymentUrl'])) {
        catat("createInvoice gagal http=$http err=$err body=$body");
        throw new RuntimeException('Gagal membuat pembayaran, coba lagi beberapa saat.');
    }
    return $res;
}

/** Cek status transaksi langsung ke Duitku (dipakai sebagai verifikasi ganda). */
function duitku_cek_status(string $order_id): ?string
{
    global $cfg;
    $base = $cfg['mode'] === 'production' ? 'https://passport.duitku.com' : 'https://sandbox.duitku.com';
    $ch = curl_init($base . '/webapi/api/merchant/transactionStatus');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS     => json_encode([
            'merchantCode'    => $cfg['merchant_code'],
            'merchantOrderId' => $order_id,
            'signature'       => md5($cfg['merchant_code'] . $order_id . $cfg['api_key']),
        ]),
    ]);
    $res = json_decode((string) curl_exec($ch), true);
    curl_close($ch);
    return $res['statusCode'] ?? null; // "00" = sukses, "01" = pending, "02" = batal
}
