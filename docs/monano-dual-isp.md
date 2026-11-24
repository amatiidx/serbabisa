# Monano: Dual ISP Starlink + Indihome (MikroTik RouterOS v7)

Tujuan:

- **Starlink (SL)** jadi jalur utama untuk semua trafik.
- **Game online** dan **WhatsApp** (chat, kirim media, voice/video call) lewat **Indihome (IH)**.
- **Failover**: kalau salah satu ISP mati, semua trafik otomatis pindah ke ISP yang masih hidup, lalu kembali sendiri saat ISP itu pulih.

Skrip ini untuk **RouterOS v7** (memakai `/routing table`). Untuk v6 bagian routing-table harus diganti `routing-mark` di `/ip route`.

## Aman untuk remote

Kalau router dikonfigurasi dari jauh (Winbox lewat VPN/tunnel, IP publik, atau MikroTik Cloud), ikuti ini supaya akses tidak putus:

1. **Nyalakan Safe Mode** dulu (Winbox: tombol *Safe Mode*; terminal: `Ctrl+X`). Kalau koneksi remote putus, semua perubahan dibatalkan otomatis dalam ±9 menit.
2. **Tambahkan route baru dulu**, baru matikan `add-default-route` (urutan di bagian 2 sudah begitu). Kalau dibalik, router sempat tanpa internet dan remote langsung putus.
3. **Remote dari LAN/hotspot** (misal Winbox dari laptop di VLAN) aman, karena trafik lokal dilewati di aturan mangle pertama.
4. **Remote lewat IP publik Indihome**: balasan router dipaksa keluar lewat Indihome lagi (mark `IH-in` di bagian 5), jadi tidak putus.
5. **Remote lewat VPN client di router** (umum dipakai karena Starlink CGNAT): VPN ikut tabel `main`, jadi lewat Starlink dan pindah ke Indihome kalau Starlink mati. Kalau mau VPN selalu lewat satu ISP, tambahkan route khusus ke IP server VPN (lihat contoh di bagian 2).
6. **WireGuard**: lihat bagian 9.
7. Jangan tutup jendela remote sebelum `/ip route print` menunjukkan route default aktif (flag `A`).

## 0. Ganti dulu placeholder ini

Semua nilai di bawah adalah contoh. Cek di router (`/interface print`, `/ip dhcp-client print`, `/ip route print`) lalu ganti sebelum paste.

| Placeholder | Arti | Cara cek |
|---|---|---|
| `ether1-SL` | Interface ke router/dish Starlink | `/interface print` |
| `pppoe-IH` | Interface Indihome. Jika ONT mode bridge biasanya PPPoE client; jika ONT mode router biasanya ether biasa dengan DHCP/IP statis | `/interface print` |
| `GW_SL` | Gateway Starlink (lihat kolom gateway di DHCP client) | `/ip dhcp-client print detail` |
| `GW_IH` | Gateway Indihome. Untuk PPPoE cukup isi nama interface `pppoe-IH` | `/ip route print` |
| `LAN` | Interface list berisi semua sisi LAN, termasuk `vlan20` (hotspot) dan `vlan30` (PPPoE server) | `/interface list member print` |
| `192.168.0.0/16`, `10.0.0.0/8` dll | Subnet lokal (hotspot, PPPoE pool, management) | `/ip address print`, `/ip pool print` |

> Catatan: Starlink dalam mode bypass biasanya memberi IP CGNAT `100.64.x.x`. Jangan menebak gateway, ambil dari DHCP client.

## 1. Interface list dan address list lokal

```routeros
/interface list
add name=WAN comment="SL + IH"
add name=LAN comment="sisi pelanggan" 
/interface list member
add list=WAN interface=ether1-SL
add list=WAN interface=pppoe-IH
add list=LAN interface=vlan20 comment="hotspot"
add list=LAN interface=vlan30 comment="PPPoE"
# tambahkan bridge/vlan LAN lain bila ada

/ip firewall address-list
add list=LOCAL address=10.0.0.0/8
add list=LOCAL address=172.16.0.0/12
add list=LOCAL address=192.168.0.0/16
add list=LOCAL address=100.64.0.0/10 comment="CGNAT Starlink + pool lokal"
```

Kalau list `LAN`/`WAN` sudah ada, lewati baris `add name=...` dan cukup tambahkan member yang belum ada.

## 2. Routing table dan route (failover rekursif)

Cek gateway dengan `ping` biasa ke gateway Starlink sering menipu: dish tetap menjawab walau internet putus. Karena itu dipakai **route rekursif**: router mengecek host internet (1.1.1.1 lewat SL, 8.8.8.8 lewat IH). Jika host itu tidak terjangkau, route default ISP tersebut dimatikan otomatis.

```routeros
/routing table
add name=to-IH fib

/ip route
# Host pengecek: masing-masing dipaksa lewat ISP-nya
add dst-address=1.1.1.1/32 gateway=GW_SL scope=10 comment="cek SL"
add dst-address=8.8.8.8/32 gateway=GW_IH scope=10 comment="cek IH"

# Tabel utama (main): SL utama, IH cadangan
add dst-address=0.0.0.0/0 gateway=1.1.1.1 target-scope=11 check-gateway=ping distance=1 comment="main via SL"
add dst-address=0.0.0.0/0 gateway=8.8.8.8 target-scope=11 check-gateway=ping distance=2 comment="main backup via IH"

# Tabel to-IH (game + WA): IH utama, SL cadangan
add dst-address=0.0.0.0/0 gateway=8.8.8.8 target-scope=11 check-gateway=ping distance=1 routing-table=to-IH comment="IH utama"
add dst-address=0.0.0.0/0 gateway=1.1.1.1 target-scope=11 check-gateway=ping distance=2 routing-table=to-IH comment="IH backup via SL"

# (Opsional) VPN remote selalu lewat satu ISP. Ganti IP_SERVER_VPN dengan IP server VPN Anda.
# add dst-address=IP_SERVER_VPN/32 gateway=8.8.8.8 target-scope=11 check-gateway=ping distance=1 comment="VPN remote via IH"
# add dst-address=IP_SERVER_VPN/32 gateway=1.1.1.1 target-scope=11 check-gateway=ping distance=2 comment="VPN remote backup via SL"
```

Cek dulu `/ip route print`: route `main via SL` harus aktif (flag `A`). **Baru setelah itu** matikan default route otomatis dari ISP supaya tidak bentrok:

```routeros
/ip dhcp-client
set [find interface=ether1-SL] add-default-route=no
# Jika IH juga DHCP (ONT mode router), lakukan hal yang sama:
# set [find interface=ether2-IH] add-default-route=no
# Jika IH PPPoE client:
/interface pppoe-client set [find name=pppoe-IH] add-default-route=no
```

Saat masih ada route default dari DHCP/PPPoE (distance 1), route rekursif di atas mungkin belum aktif karena kalah prioritas. Itu normal; setelah `add-default-route=no` route rekursif yang dipakai.

Akibat samping: ping ke 1.1.1.1 selalu lewat SL, dan ke 8.8.8.8 selalu lewat IH. Jika pelanggan memakai DNS 1.1.1.1/8.8.8.8 langsung itu tetap jalan, hanya jalurnya tetap.

**Gateway Starlink berubah-ubah?** Jika `GW_SL` dari DHCP bisa ganti, pakai script di DHCP client supaya route `cek SL` ikut diperbarui:

```routeros
/ip dhcp-client set [find interface=ether1-SL] script=":if (\$bound=1) do={ /ip route set [find comment=\"cek SL\"] gateway=\$\"gateway-address\" }"
```

## 3. Daftar alamat WhatsApp

WhatsApp memakai banyak IP milik Meta yang berganti-ganti, jadi IP-nya dikumpulkan otomatis dari nama domain (SNI/TLS) yang dilihat router.

```routeros
/ip firewall address-list
add list=WA address=whatsapp.net
add list=WA address=g.whatsapp.net
add list=WA address=mmg.whatsapp.net
add list=WA address=media.fcgk1-1.fna.whatsapp.net comment="contoh CDN, boleh dihapus"
add list=WA address=web.whatsapp.com
add list=WA address=whatsapp.com
```

RouterOS akan me-resolve FQDN ini secara berkala. Mangle di bagian 5 juga menambah IP baru ke list `WA` setiap kali ada koneksi TLS ke `*whatsapp*`.

**Opsional (RouterOS 7.15 ke atas, pelanggan memakai DNS router):** DNS router bisa langsung mengisi address list untuk semua subdomain:

```routeros
/ip dns static
add name=whatsapp.net type=FWD forward-to=8.8.8.8 match-subdomain=yes address-list=WA
add name=whatsapp.com type=FWD forward-to=8.8.8.8 match-subdomain=yes address-list=WA
```

Cek dulu apakah opsi `address-list` ada di versi Anda (`/ip dns static add ?`).

## 4. Port game

Port di bawah adalah daftar komunitas untuk game populer di Indonesia. Developer bisa mengganti port kapan saja, jadi pantau di `/ip firewall connection print where connection-mark=IH-conn` dan sesuaikan.

Game ditandai berdasarkan port di mangle bagian 5.

| Game | TCP | UDP |
|---|---|---|
| Mobile Legends | 5000-5221, 5224-5227, 5229-5241, 5243-5508, 5551-5559, 5601-5700, 9001, 9443, 10003, 30000-30300 | 5000-5221, 5224-5241, 5243-5508, 5551-5559, 5601-5700, 2702, 3702, 4001-4009, 8001, 8130, 8443, 9000-9010, 9120, 9992, 10003, 30000-30300 |
| Free Fire | 6006, 6008, 6674, 7889, 10000-10012, 11000-11019, 12006, 12008, 13006, 39003, 39006, 39698, 39779, 39800 | 6006, 6008, 6674, 7008, 7889, 8008, 9008, 9030, 10000-10013, 10100, 11000-11019, 12008, 13006, 17000 |
| PUBG Mobile | 17500, 18081, 20000-20002 | 8011, 9030, 10010-10650, 12070-12460, 13004, 14000, 17000, 17500, 20000-20002, 41182-42474 |

## 5. Mangle

Aturan: koneksi baru dari LAN yang cocok (game/WA) diberi tanda `IH-conn`, lalu setiap paketnya diberi routing mark `to-IH`. Koneksi lain tanpa tanda, jadi ikut tabel `main` (Starlink).

```routeros
/ip firewall mangle
# --- 0. Jangan sentuh trafik lokal ---
add chain=prerouting dst-address-list=LOCAL action=accept comment="lokal: skip"

# --- 1. Balasan koneksi dari luar tetap keluar lewat ISP yang sama ---
add chain=prerouting in-interface=ether1-SL connection-mark=no-mark action=mark-connection new-connection-mark=SL-in passthrough=yes
add chain=prerouting in-interface=pppoe-IH connection-mark=no-mark action=mark-connection new-connection-mark=IH-in passthrough=yes
add chain=output connection-mark=SL-in action=mark-routing new-routing-mark=main passthrough=no
add chain=output connection-mark=IH-in action=mark-routing new-routing-mark=to-IH passthrough=no

# --- 2. Kumpulkan IP WhatsApp dari SNI ---
add chain=prerouting in-interface-list=LAN protocol=tcp dst-port=443 tls-host=*whatsapp* action=add-dst-to-address-list address-list=WA address-list-timeout=1d comment="WA: pelajari IP"

# --- 3. Tandai koneksi WhatsApp ---
add chain=prerouting in-interface-list=LAN connection-mark=no-mark dst-address-list=WA action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="WA"
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=udp dst-port=3478-3484 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="WA call / STUN"

# --- 4. Tandai koneksi game (maks 15 entri per rule) ---
# Mobile Legends
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=tcp dst-port=5000-5221,5224-5227,5229-5241,5243-5508,5551-5559,5601-5700,9001,9443,10003,30000-30300 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="ML tcp"
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=udp dst-port=5000-5221,5224-5241,5243-5508,5551-5559,5601-5700,2702,3702,4001-4009,8001,8130,8443,9000-9010,9120,9992,10003 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="ML udp 1"
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=udp dst-port=30000-30300 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="ML udp 2"
# Free Fire
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=tcp dst-port=6006,6008,6674,7889,10000-10012,11000-11019,12006,12008,13006,39003,39006,39698,39779,39800 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="FF tcp"
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=udp dst-port=6006,6008,6674,7008,7889,8008,9008,9030,10000-10013,10100,11000-11019,12008,13006,17000 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="FF udp"
# PUBG Mobile
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=tcp dst-port=17500,18081,20000-20002 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="PUBG tcp"
add chain=prerouting in-interface-list=LAN connection-mark=no-mark protocol=udp dst-port=8011,9030,10010-10650,12070-12460,13004,14000,17000,17500,20000-20002,41182-42474 action=mark-connection new-connection-mark=IH-conn passthrough=yes comment="PUBG udp"

# --- 5. Routing mark ---
add chain=prerouting in-interface-list=LAN connection-mark=IH-conn action=mark-routing new-routing-mark=to-IH passthrough=no comment="game+WA -> IH"
add chain=prerouting in-interface-list=LAN connection-mark=IH-in action=mark-routing new-routing-mark=to-IH passthrough=no
```

**Tentang hotspot (VLAN 20):** hotspot MikroTik membuat rule mangle/NAT dinamis sendiri. Rule di atas tetap bekerja karena memakai `prerouting` dan `in-interface-list=LAN`. Pastikan `vlan20` (atau bridge hotspot) masuk list `LAN`.

**Koneksi WA pertama:** IP WA yang belum ada di list baru dipelajari saat koneksi TLS berjalan, jadi koneksi pertama ke IP baru masih lewat SL. Koneksi berikutnya ke IP itu sudah lewat IH. List FQDN di bagian 3 membuat ini jarang terjadi.

## 6. NAT

```routeros
/ip firewall nat
add chain=srcnat out-interface=ether1-SL action=masquerade comment="NAT SL"
add chain=srcnat out-interface=pppoe-IH action=masquerade comment="NAT IH"
```

Jika sudah ada satu masquerade umum `out-interface-list=WAN`, itu juga cukup.

## 7. FastTrack (penting)

Paket yang di-FastTrack melewati mangle, sehingga routing mark hilang dan game/WA bisa nyasar ke Starlink. Batasi FastTrack hanya untuk koneksi tanpa tanda:

```routeros
/ip firewall filter
set [find action=fasttrack-connection] connection-mark=no-mark
```

Koneksi Starlink tetap di-FastTrack (tanpa tanda), jadi CPU tetap ringan.

## 8. Uji coba

1. `/ip route print where dst-address=0.0.0.0/0` harus menampilkan route SL aktif di `main`, IH aktif di `to-IH`.
2. Dari HP pelanggan buka WA dan main ML, lalu cek:
   `/ip firewall connection print where connection-mark=IH-conn`
   Harus ada koneksi ke IP WA/game.
3. Cek `/ip firewall mangle print stats` agar counter rule bertambah.
4. Uji failover: cabut kabel Starlink. Dalam ±10–30 detik route `main via SL` jadi unreachable dan semua lewat IH. Colok lagi, otomatis balik. Ulangi dengan Indihome.
5. Speedtest dari klien harus menampilkan ISP Starlink; `https://ipinfo.io` dari klien juga.

## 9. Remote lewat WireGuard

### A. Router Monano sebagai client ke server/VPS (paling umum, karena Starlink CGNAT)

Trafik WireGuard dibuat oleh router sendiri, jadi tidak kena mangle LAN di atas. Ia mengikuti tabel `main`: lewat Starlink, pindah ke Indihome kalau Starlink mati. Agar lebih stabil, kunci endpoint WireGuard ke Indihome (latensi lebih rata, tidak terpengaruh obstruksi dish) dengan Starlink sebagai cadangan. Ganti `IP_SERVER_WG` dengan IP publik server/VPS WireGuard (lihat `endpoint-address` di `/interface wireguard peers print`), dan `NAMA_PEER` dengan nama/komentar peer-nya.

```routeros
/ip route
add dst-address=IP_SERVER_WG/32 gateway=8.8.8.8 target-scope=11 check-gateway=ping distance=1 comment="WG via IH"
add dst-address=IP_SERVER_WG/32 gateway=1.1.1.1 target-scope=11 check-gateway=ping distance=2 comment="WG backup via SL"

# Keepalive wajib supaya server cepat tahu alamat baru router setelah pindah ISP
/interface wireguard peers
set [find comment=NAMA_PEER] persistent-keepalive=25s
```

Kalau `endpoint-address` berupa nama domain (bukan IP), pakai IP hasil resolve-nya di route di atas, atau ganti endpoint ke IP.

**Setelah failover tunnel kadang macet** karena koneksi lama masih tercatat. Netwatch ini menghapus koneksi WireGuard lama otomatis. `IP_TUNNEL_SERVER` adalah IP server di dalam tunnel (contoh `10.10.10.1`), `PORT_WG` adalah port `endpoint-port`.

```routeros
/tool netwatch
add host=IP_TUNNEL_SERVER interval=30s timeout=2s comment="cek WG" \
    down-script="/ip firewall connection remove [find protocol=udp dst-address~\"IP_SERVER_WG:PORT_WG\"]"
```

### B. Router Monano sebagai server (port WireGuard dibuka di IP publik Indihome)

Tidak perlu tambahan. Paket masuk lewat Indihome diberi mark `IH-in`, dan balasannya dipaksa keluar lewat Indihome (bagian 5). Pastikan firewall input mengizinkan port WireGuard dari `pppoe-IH`, dan subnet tunnel WireGuard (misal `10.10.10.0/24`) termasuk dalam list `LOCAL` (sudah, jika memakai 10.0.0.0/8).

## Rollback

Hapus berdasarkan comment/mark yang dibuat di atas:

```routeros
/ip firewall mangle remove [find where new-connection-mark=IH-conn or new-routing-mark=to-IH or new-connection-mark~"-in" or comment~"WA"]
/ip route remove [find where routing-table=to-IH or comment~"cek "]
/ip route remove [find where comment~"main"]
/routing table remove [find name=to-IH]
# kembalikan add-default-route=yes pada DHCP client / PPPoE client
```
