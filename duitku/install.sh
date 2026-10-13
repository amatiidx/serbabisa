#!/bin/bash
# Pasang modul Duitku ke master.serbabisa.id lewat terminal VPS.
# Jalankan sebagai root:
#   bash <(curl -fsSL https://raw.githubusercontent.com/amatiidx/serbabisa/claude/merah-ready-xg5pnv/duitku/install.sh)
set -e

RAW="https://raw.githubusercontent.com/amatiidx/serbabisa/claude/merah-ready-xg5pnv/duitku"
FILES="lib.php bayar.php callback.php selesai.php bulanan.php tagihan.php config.example.php tabel.sql .gitignore README.md"

echo "== 1. Cari folder situs =="
SITE=$(ls -d /home/*/htdocs/master.serbabisa.id 2>/dev/null | head -1)
if [ -z "$SITE" ] || [ ! -f "$SITE/portal.php" ]; then
  echo "Folder situs dengan portal.php tidak ketemu otomatis."
  read -rp "Ketik path folder yang berisi portal.php: " SITE
fi
[ -f "$SITE/portal.php" ] || { echo "portal.php tidak ada di $SITE. Berhenti."; exit 1; }
OWNER=$(stat -c '%U:%G' "$SITE/portal.php")
echo "Situs: $SITE (pemilik $OWNER)"

echo "== 2. Download modul =="
mkdir -p "$SITE/duitku"
for f in $FILES; do
  curl -fsSL "$RAW/$f" -o "$SITE/duitku/$f" || { echo "Gagal download $f"; exit 1; }
done
echo "OK"

echo "== 3. Isi config.php =="
if [ -f "$SITE/duitku/config.php" ]; then
  echo "config.php sudah ada, dilewati."
else
  read -rp  "Merchant Code [D25220]: " MC; MC=${MC:-D25220}
  read -rsp "API Key Duitku (tidak tampil saat diketik): " AK; echo
  read -rp  "Mode production/sandbox [production]: " MODE; MODE=${MODE:-production}
  read -rp  "Nama database portal: " DBN
  read -rp  "User database: " DBU
  read -rsp "Password database (tidak tampil): " DBP; echo
  MC="$MC" AK="$AK" MODE="$MODE" DBN="$DBN" DBU="$DBU" DBP="$DBP" php -r '
    $c = [
      "mode" => getenv("MODE"),
      "merchant_code" => getenv("MC"),
      "api_key" => getenv("AK"),
      "callback_url" => "https://master.serbabisa.id/portal.php",
      "return_url" => "https://master.serbabisa.id/portal.php",
      "expiry_menit" => 1440,
      "db_dsn" => "mysql:host=localhost;dbname=" . getenv("DBN") . ";charset=utf8mb4",
      "db_user" => getenv("DBU"),
      "db_pass" => getenv("DBP"),
    ];
    file_put_contents($argv[1], "<?php\nreturn " . var_export($c, true) . ";\n");
  ' "$SITE/duitku/config.php"
  chmod 640 "$SITE/duitku/config.php"
  echo "config.php dibuat."

  echo "== 4. Buat tabel database =="
  MYSQL_PWD="$DBP" mysql -u "$DBU" "$DBN" < "$SITE/duitku/tabel.sql" && echo "Tabel duitku_transaksi & duitku_bulanan siap."
fi

echo "== 5. Pasang callback di portal.php =="
P="$SITE/portal.php"
if grep -q "duitku/callback.php" "$P"; then
  echo "Sudah terpasang sebelumnya, dilewati."
else
  BAK="$P.bak-$(date +%Y%m%d%H%M%S)"
  cp -p "$P" "$BAK"
  BLOK='// Callback Duitku: POST dari server Duitku diteruskan ke modul pembayaran
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["merchantCode"], $_POST["merchantOrderId"], $_POST["signature"])) {
    require __DIR__ . "/duitku/callback.php";
    exit;
}'
  if head -1 "$P" | grep -q '^<?php'; then
    if sed -n '2p' "$P" | grep -q 'declare(strict_types'; then LINE=2; else LINE=1; fi
    printf '%s\n' "$BLOK" > "$P.blk"
    awk -v n="$LINE" 'NR==FNR{b=b $0 "\n"; next} {print} FNR==n{printf "%s", b}' "$P.blk" "$P" > "$P.tmp"
    rm -f "$P.blk"
  else
    { printf '<?php\n%s\n?>\n' "$BLOK"; cat "$P"; } > "$P.tmp"
  fi
  if php -l "$P.tmp" >/dev/null 2>&1; then
    cat "$P.tmp" > "$P"; rm -f "$P.tmp"
    echo "Terpasang. Backup: $BAK"
  else
    rm -f "$P.tmp"
    echo "GAGAL: hasil edit error, portal.php TIDAK diubah. Backup tetap di $BAK"
  fi
fi

chown -R "$OWNER" "$SITE/duitku"
mkdir -p "$SITE/duitku/log" && chown "$OWNER" "$SITE/duitku/log" && chmod 750 "$SITE/duitku/log"

echo "== 6. Tes =="
H=$(curl -s -o /dev/null -w "%{http_code}" https://master.serbabisa.id/portal.php || true)
echo "Portal dibuka biasa: HTTP $H (harus 200 atau 302)"
T=$(curl -s -d "merchantCode=X&merchantOrderId=TES&amount=1&signature=salah" https://master.serbabisa.id/portal.php | head -c 40 || true)
echo "Tes callback palsu: '$T' (harus: Bad Signature)"

echo "== 7. Daftar tabel database (kirim screenshot bagian ini) =="
if [ -n "$DBU" ]; then
  for t in $(MYSQL_PWD="$DBP" mysql -N -u "$DBU" "$DBN" -e "SHOW TABLES" || true); do
    echo "--- $t"
    MYSQL_PWD="$DBP" mysql -N -u "$DBU" "$DBN" -e "SELECT GROUP_CONCAT(COLUMN_NAME) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='$DBN' AND TABLE_NAME='$t'"
  done
fi
echo "SELESAI."
