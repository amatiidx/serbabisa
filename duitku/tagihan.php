<?php
// ============================================================
//  SATU-SATUNYA FILE YANG PERLU DISESUAIKAN DENGAN DATABASE PORTAL
//  Ganti nama tabel/kolom di bawah sesuai tabel tagihan Anda.
// ============================================================

/**
 * Ambil data tagihan dari database. Jumlah WAJIB dari database,
 * jangan pernah dari URL/form (bisa diubah pelanggan).
 * Kembalikan null kalau tagihan tidak ada / sudah lunas.
 */
function ambil_tagihan(PDO $db, string $tagihan_id): ?array
{
    $q = $db->prepare(
        "SELECT t.id, t.jumlah, p.nama, p.email, p.no_hp
           FROM tagihan t JOIN pelanggan p ON p.id = t.pelanggan_id
          WHERE t.id = ? AND t.status = 'BELUM'"
    );
    $q->execute([$tagihan_id]);
    $r = $q->fetch(PDO::FETCH_ASSOC);
    if (!$r) return null;

    return [
        'jumlah' => (int) $r['jumlah'],
        'nama'   => $r['nama'],
        'email'  => $r['email'] ?: 'billing@serbabisa.id',
        'no_hp'  => $r['no_hp'] ?: '',
        'produk' => 'Tagihan Internet Serbabisa #' . $r['id'],
    ];
}

/**
 * Dipanggil otomatis saat Duitku mengonfirmasi pembayaran berhasil.
 * Tandai tagihan lunas di sini (dan kalau perlu, buka isolir PPPoE).
 */
function tandai_lunas(PDO $db, string $tagihan_id, int $jumlah, string $reference): void
{
    $q = $db->prepare("UPDATE tagihan SET status = 'LUNAS', tgl_bayar = NOW(), ket_bayar = ? WHERE id = ?");
    $q->execute(['Duitku ' . $reference, $tagihan_id]);
}
