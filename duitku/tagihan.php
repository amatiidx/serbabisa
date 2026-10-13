<?php
// ============================================================
//  SATU-SATUNYA FILE YANG PERLU DISESUAIKAN DENGAN DATABASE PORTAL
//  Ganti nama tabel/kolom di bawah sesuai database Anda.
//  Jumlah bayar WAJIB dari database, jangan dari URL/form.
// ============================================================


// ---------- A. TAGIHAN (invoice yang sudah dibuat di portal) ----------

/** Kembalikan null kalau tagihan tidak ada / sudah lunas. */
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

/** Dipanggil otomatis saat pembayaran tagihan berhasil. */
function tandai_lunas(PDO $db, string $tagihan_id, int $jumlah, string $reference): void
{
    $q = $db->prepare("UPDATE tagihan SET status = 'LUNAS', tgl_bayar = NOW(), ket_bayar = ? WHERE id = ?");
    $q->execute(['Duitku ' . $reference, $tagihan_id]);
}


// ---------- B. PELANGGAN BULANAN (bayar langganan per bulan) ----------

/**
 * Cari pelanggan bulanan dari kode yang diketik pelanggan
 * (ID pelanggan atau username PPPoE). Kembalikan null kalau tidak ada.
 */
function cari_pelanggan_bulanan(PDO $db, string $kode): ?array
{
    $q = $db->prepare(
        "SELECT p.id, p.nama, p.email, p.no_hp, k.nama AS paket, k.harga
           FROM pelanggan p JOIN paket k ON k.id = p.paket_id
          WHERE (p.id = ? OR p.username_pppoe = ?) AND p.jenis = 'BULANAN'"
    );
    $q->execute([$kode, $kode]);
    $r = $q->fetch(PDO::FETCH_ASSOC);
    if (!$r) return null;

    return [
        'pelanggan_id' => (string) $r['id'],
        'nama'         => $r['nama'],
        'paket'        => $r['paket'],
        'jumlah'       => (int) $r['harga'],
        'email'        => $r['email'] ?: 'billing@serbabisa.id',
        'no_hp'        => $r['no_hp'] ?: '',
    ];
}

/**
 * Dipanggil otomatis saat pembayaran bulanan berhasil.
 * $periode = 'YYYYMM'. Perpanjang masa aktif / buka isolir di sini.
 */
function lunas_bulanan(PDO $db, string $pelanggan_id, string $periode, int $jumlah, string $reference): void
{
    $q = $db->prepare(
        "UPDATE pelanggan
            SET status = 'AKTIF',
                jatuh_tempo = DATE_ADD(GREATEST(COALESCE(jatuh_tempo, CURDATE()), CURDATE()), INTERVAL 1 MONTH)
          WHERE id = ?"
    );
    $q->execute([$pelanggan_id]);
}
