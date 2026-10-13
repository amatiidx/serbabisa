<?php
// Halaman bayar langganan bulanan: https://master.serbabisa.id/duitku/bulanan.php
require __DIR__ . '/lib.php';

function samarkan(string $nama): string
{
    return implode(' ', array_map(function ($k) {
        $n = mb_strlen($k);
        return $n <= 2 ? $k : mb_substr($k, 0, 1) . str_repeat('*', $n - 2) . mb_substr($k, -1);
    }, preg_split('/\s+/', trim($nama))));
}

$kode = preg_replace('/[^A-Za-z0-9_.@-]/', '', $_GET['kode'] ?? '');
$p = null; $sudah = false; $error = '';
if ($kode !== '') {
    try {
        $p = cari_pelanggan_bulanan(db(), $kode);
        if ($p) {
            $q = db()->prepare("SELECT 1 FROM duitku_bulanan WHERE pelanggan_id = ? AND periode = ?");
            $q->execute([$p['pelanggan_id'], date('Ym')]);
            $sudah = (bool) $q->fetchColumn();
        } else {
            $error = 'ID pelanggan tidak ditemukan.';
        }
    } catch (Throwable $e) {
        catat('bulanan.php: ' . $e->getMessage());
        $error = 'Sistem sedang gangguan, coba lagi nanti.';
    }
}
$h = fn($v) => htmlspecialchars((string) $v, ENT_QUOTES);
?>
<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bayar Internet Bulanan - Serbabisa</title>
<style>
body{font-family:sans-serif;max-width:440px;margin:40px auto;padding:0 16px;color:#222}
input,button,.btn{width:100%;box-sizing:border-box;padding:12px;font-size:16px;border-radius:8px}
input{border:1px solid #bbb}button,.btn{border:0;background:#0a7c3e;color:#fff;margin-top:12px;display:block;text-align:center;text-decoration:none}
.kartu{border:1px solid #ddd;border-radius:10px;padding:16px;margin-top:20px}
.kartu td{padding:4px 0}.kartu td:first-child{color:#666;width:40%}.err{color:#b00020}
</style></head><body>
<h2>Bayar Internet Bulanan</h2>
<form method="get">
  <input name="kode" placeholder="ID pelanggan / username PPPoE" value="<?= $h($kode) ?>" required>
  <button type="submit">Cek Tagihan</button>
</form>
<?php if ($error): ?><p class="err"><?= $h($error) ?></p><?php endif; ?>
<?php if ($p): ?>
<div class="kartu">
  <table>
    <tr><td>Nama</td><td><?= $h(samarkan($p['nama'])) ?></td></tr>
    <tr><td>Paket</td><td><?= $h($p['paket']) ?></td></tr>
    <tr><td>Periode</td><td><?= date('m/Y') ?></td></tr>
    <tr><td>Jumlah</td><td><b>Rp <?= number_format($p['jumlah'], 0, ',', '.') ?></b></td></tr>
  </table>
  <?php if ($sudah): ?>
    <p><b>Sudah lunas bulan ini.</b> Terima kasih.</p>
  <?php else: ?>
    <a class="btn" href="bayar.php?bulanan=<?= urlencode($kode) ?>">Bayar Sekarang (QRIS / VA / e-wallet)</a>
  <?php endif; ?>
</div>
<?php endif; ?>
</body></html>
