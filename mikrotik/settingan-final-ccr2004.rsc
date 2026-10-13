# ==========================================================================
#  SETTINGAN FINAL CCR2004 - Serbabisa.id / PT Internet Berkah Sulawesi
#  RouterOS 7
#
#  Script ini MENYESUAIKAN konfigurasi yang sudah ada (pakai find, bukan
#  nomor rule). Tidak ada rule yang dihapus. Aman dijalankan berulang.
#
#  CARA PAKAI
#   1. Backup dulu:  /export file=sebelum-final
#   2. Upload file ini ke Winbox > Files
#   3. Terminal:     /import file-name=settingan-final-ccr2004.rsc
#   4. Cek:          /log print where message~"FINAL"
#
#  WAN : Merah ether1 (Telkom 300, FUP 3000GB)  cek 1.0.0.1
#        Biru ether2 (XL 300, tanpa FUP)        cek 4.2.2.1
#        Booster ether3 (XL 400, tanpa FUP)     cek 9.9.9.9
#        FPP ether4 (IndiBiz 100, FUP)          cek 149.112.112.112
#        Metro vlan180 (Indosat 100 dedicated)  cek 8.8.8.8
#        Starlink ether5 (cadangan terakhir)    cek 4.2.2.2
#
#  PEMBAGIAN TUGAS
#   Merah   : jalur utama semua trafik umum (24/24 PCC) + marketplace
#   Biru    : khusus TikTok                          tabel to-VIDEO3
#   Booster : khusus YouTube + download + video lain tabel to-VIDEO
#   FPP     : game, bank/e-wallet, WA, video call    tabel to-MERAH / to-WA
#   Metro   : FB / IG (boros kuota)                  tabel to-ISP6
#   ONNET   : tujuan di jaringan Telkom -> Merah, jaringan XL -> Booster
#             (cache FB/YouTube di dalam ISP tetap lewat ISP pemiliknya)
#
#  CADANGAN (sama seperti sebelumnya)
#   to-VIDEO  : Booster -> Metro + Merah -> Biru -> FPP -> Starlink
#   to-VIDEO3 : Biru -> Metro + Merah -> Booster -> FPP -> Starlink
#   to-ISP1   : Merah -> Metro -> Biru -> Booster -> FPP -> Starlink
#   to-ISP6   : Metro -> Merah -> Biru -> Booster -> FPP -> Starlink
#   to-MERAH / to-WA : FPP -> Merah -> Metro/Biru -> Booster -> Starlink
#   Netwatch Booster/Biru turun kualitas -> pindah ke Metro + Merah.
# ==========================================================================


# --------------------------------------------------------------------------
# 1. MERAH: semua trafik umum (24 bucket PCC ke Merah)
# --------------------------------------------------------------------------
:for b from=0 to=23 do={
  /ip firewall mangle set [find chain=prerouting action=mark-connection per-connection-classifier=("both-addresses-and-ports:24/" . $b)] new-connection-mark=ISP1-conn
}
# STABIL yang dulu 1/4 lewat Metro -> Merah
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=STABIL-conn new-routing-mark=to-ISP6] new-routing-mark=to-ISP1 comment="STABIL - jalur Merah 4/3"
# Marketplace butuh gambar cepat -> Merah (bukan FPP)
/ip firewall mangle set [find chain=prerouting action=mark-connection dst-address-list=ECOMMERCE] new-connection-mark=ISP1-conn comment="Ecommerce -> Merah"


# --------------------------------------------------------------------------
# 2. BIRU: khusus TikTok
# --------------------------------------------------------------------------
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=TT-conn] new-routing-mark=to-VIDEO3 comment="TT - jalur Biru"
# CDN TikTok yang dulu masuk daftar VIDEO (Booster) -> daftar TIKTOK
/ip firewall mangle set [find action=add-dst-to-address-list address-list=VIDEO tls-host~"ibytedtos|muscdn|ttwstatic"] address-list=TIKTOK


# --------------------------------------------------------------------------
# 3. BOOSTER: YouTube + download (rule YT, VIDEO, DOWNLOAD sudah ke to-VIDEO)
# --------------------------------------------------------------------------
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=YT-conn] new-routing-mark=to-VIDEO
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=VIDEO-conn] new-routing-mark=to-VIDEO
/ip firewall mangle set [find comment="DOWNLOAD via Booster"] new-routing-mark=to-VIDEO


# --------------------------------------------------------------------------
# 4. METRO: FB / IG
# --------------------------------------------------------------------------
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=FB-conn] new-routing-mark=to-ISP6 comment="FB - jalur Metro"
/ip firewall mangle set [find chain=prerouting action=mark-routing comment~"^META FB IG via"] new-routing-mark=to-ISP6 comment="META FB IG via Metro"
# Rule FB chain output (trafik router sendiri) tidak perlu
/ip firewall mangle disable [find chain=output new-routing-mark=to-ISP6 comment~"FB"]


# --------------------------------------------------------------------------
# 5. FPP: game + bank/e-wallet + WA (yang butuh stabil)
#    Rule bank dipasang DI ATAS ONNET supaya bank yang servernya di
#    jaringan Telkom/XL tidak ikut terbawa ke Merah/Booster.
# --------------------------------------------------------------------------
:if ([:len [/ip firewall mangle find comment="BANK - jalur FPP"]]=0) do={
  /ip firewall mangle add chain=prerouting action=mark-routing new-routing-mark=to-WA passthrough=no src-address-list=LOCAL-IP connection-mark=ISP4-conn comment="BANK - jalur FPP"
}
/ip firewall mangle move [find comment="BANK - jalur FPP"] destination=[find comment="ONNET - ke jaringan Telkom via Merah"]
# Game & WA sudah ke FPP (to-MERAH / to-WA) - pastikan
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=GAME-conn] new-routing-mark=to-MERAH
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=MERAH-conn] new-routing-mark=to-WA


# --------------------------------------------------------------------------
# 6. Tabel cadangan (hanya ditambah kalau belum ada)
# --------------------------------------------------------------------------
# to-ISP6 (FB, Metro): Metro -> Merah -> Biru -> Booster -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-ISP6" gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=to-ISP6 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Merah" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=to-ISP6 distance=3 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Biru" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=to-ISP6 distance=4 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Booster" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-ISP6 distance=5 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad FPP" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-ISP6 distance=9 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Starlink" }

# to-VIDEO (YouTube, Booster): Booster -> Metro + Merah -> Biru -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-VIDEO" gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=to-VIDEO distance=2 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO cad Metro" }
:if ([:len [/ip route find routing-table="to-VIDEO" gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=to-VIDEO distance=2 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO cad Merah" }
:if ([:len [/ip route find routing-table="to-VIDEO" gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=to-VIDEO distance=3 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO cad Biru" }
:if ([:len [/ip route find routing-table="to-VIDEO" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-VIDEO distance=4 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO cad FPP" }
:if ([:len [/ip route find routing-table="to-VIDEO" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-VIDEO distance=9 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO cad Starlink" }

# to-VIDEO3 (TikTok, Biru): Biru -> Metro + Merah -> Booster -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-VIDEO3" gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=to-VIDEO3 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO3 cad Metro" }
:if ([:len [/ip route find routing-table="to-VIDEO3" gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=to-VIDEO3 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO3 cad Merah" }
:if ([:len [/ip route find routing-table="to-VIDEO3" gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=to-VIDEO3 distance=3 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO3 cad Booster" }
:if ([:len [/ip route find routing-table="to-VIDEO3" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-VIDEO3 distance=4 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO3 cad FPP" }
:if ([:len [/ip route find routing-table="to-VIDEO3" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-VIDEO3 distance=9 target-scope=11 check-gateway=ping comment="FINAL to-VIDEO3 cad Starlink" }

# to-ISP1 (umum, Merah): Merah -> Metro -> Biru -> Booster -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-ISP1" gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=to-ISP1 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Metro" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=to-ISP1 distance=3 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Biru" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=to-ISP1 distance=4 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Booster" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-ISP1 distance=5 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad FPP" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-ISP1 distance=9 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Starlink" }

# to-MERAH (game) dan to-WA (bank, WA): FPP -> Merah -> Metro -> Biru -> Booster -> Starlink
:foreach t in={"to-MERAH";"to-WA"} do={
  :if ([:len [/ip route find routing-table=$t gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=$t distance=2 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Merah") }
  :if ([:len [/ip route find routing-table=$t gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=$t distance=3 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Metro") }
  :if ([:len [/ip route find routing-table=$t gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=$t distance=4 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Biru") }
  :if ([:len [/ip route find routing-table=$t gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=$t distance=5 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Booster") }
  :if ([:len [/ip route find routing-table=$t gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=$t distance=9 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Starlink") }
}


# --------------------------------------------------------------------------
# 7. Perawatan
# --------------------------------------------------------------------------
/ip dns static disable [find type=FWD]
/interface vlan set [find name=vlan180] comment="Metro Indosat 100 dedicated"
/ip dhcp-client set [find interface=ether5] add-default-route=no


# --------------------------------------------------------------------------
# 8. Putus koneksi lama supaya langsung ikut jalur baru
# --------------------------------------------------------------------------
:foreach m in={"FB-conn";"TT-conn";"ISP6-conn";"ISP4-conn"} do={
  :foreach c in=[/ip firewall connection find connection-mark=$m] do={
    :do { /ip firewall connection remove $c } on-error={}
  }
}


# --------------------------------------------------------------------------
# 9. Laporan & backup
# --------------------------------------------------------------------------
:log info ("FINAL: bucket Metro = " . [:len [/ip firewall mangle find chain=prerouting action=mark-connection new-connection-mark=ISP6-conn]] . " (harus 0, semua umum ke Merah)")
:log info ("FINAL: rule FB ke Metro = " . [:len [/ip firewall mangle find chain=prerouting action=mark-routing connection-mark=FB-conn new-routing-mark=to-ISP6]] . " (harus 3)")
:log info ("FINAL: rule TT ke Biru = " . [:len [/ip firewall mangle find chain=prerouting action=mark-routing connection-mark=TT-conn new-routing-mark=to-VIDEO3]] . " (harus 2)")
:log info ("FINAL: rule YT ke Booster = " . [:len [/ip firewall mangle find chain=prerouting action=mark-routing connection-mark=YT-conn new-routing-mark=to-VIDEO]] . " (harus 2)")
:log info ("FINAL: rule bank ke FPP = " . [:len [/ip firewall mangle find comment="BANK - jalur FPP"]] . " (harus 1)")
/export file=config-final
:log info "FINAL: selesai, backup tersimpan di config-final.rsc"
