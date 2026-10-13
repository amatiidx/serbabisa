-- Jalankan sekali di database billing (phpMyAdmin / CloudPanel > Databases)
CREATE TABLE IF NOT EXISTS duitku_transaksi (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  order_id      VARCHAR(64)  NOT NULL UNIQUE,
  jenis         ENUM('TAGIHAN','BULANAN') NOT NULL DEFAULT 'TAGIHAN',
  tagihan_id    VARCHAR(64)  NOT NULL,          -- id tagihan, atau id pelanggan untuk BULANAN
  periode       CHAR(6)      NULL,              -- YYYYMM, khusus BULANAN
  jumlah        INT          NOT NULL,
  reference     VARCHAR(64)  NULL,
  payment_url   VARCHAR(255) NULL,
  status        ENUM('PENDING','LUNAS','GAGAL') NOT NULL DEFAULT 'PENDING',
  metode        VARCHAR(16)  NULL,
  dibuat        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  dibayar       DATETIME     NULL,
  INDEX (tagihan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Catatan pelanggan bulanan yang sudah bayar per periode (cegah bayar dobel)
CREATE TABLE IF NOT EXISTS duitku_bulanan (
  pelanggan_id  VARCHAR(64)  NOT NULL,
  periode       CHAR(6)      NOT NULL,
  jumlah        INT          NOT NULL,
  order_id      VARCHAR(64)  NOT NULL,
  dibayar       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (pelanggan_id, periode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Kalau tabel duitku_transaksi sudah terlanjur dibuat versi lama, jalankan juga:
-- ALTER TABLE duitku_transaksi
--   ADD COLUMN jenis ENUM('TAGIHAN','BULANAN') NOT NULL DEFAULT 'TAGIHAN' AFTER order_id,
--   ADD COLUMN periode CHAR(6) NULL AFTER tagihan_id;
