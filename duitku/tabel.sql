-- Jalankan sekali di database billing (phpMyAdmin / CloudPanel > Databases)
CREATE TABLE IF NOT EXISTS duitku_transaksi (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  order_id      VARCHAR(64)  NOT NULL UNIQUE,
  tagihan_id    VARCHAR(64)  NOT NULL,
  jumlah        INT          NOT NULL,
  reference     VARCHAR(64)  NULL,
  payment_url   VARCHAR(255) NULL,
  status        ENUM('PENDING','LUNAS','GAGAL') NOT NULL DEFAULT 'PENDING',
  metode        VARCHAR(16)  NULL,
  dibuat        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  dibayar       DATETIME     NULL,
  INDEX (tagihan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
