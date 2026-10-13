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
#
#  PEMBAGIAN JALUR
#   WAN : Merah ether1 (Telkom 300, FUP 3000GB)  cek 1.0.0.1
#         Biru ether2 (XL 300, tanpa FUP)        cek 4.2.2.1
#         Booster ether3 (XL 400, tanpa FUP)     cek 9.9.9.9
#         FPP ether4 (IndiBiz 100, FUP)          cek 149.112.112.112
#         Metro vlan180 (Indosat 100 dedicated)  cek 8.8.8.8
#         Starlink ether5 (cadangan terakhir)    cek 4.2.2.2
#
#   Umum ............ Merah 14/24 + Metro 10/24 (PCC)  tabel to-ISP1 / to-ISP6
#   FB / IG ......... Booster                           tabel to-VIDEO
#   YouTube/download  Booster                           tabel to-VIDEO
#   TikTok .......... Biru                              tabel to-VIDEO3
#   Game ............ FPP                               tabel to-MERAH
#   WA .............. FPP                               tabel to-WA
#   Bank/ecommerce .. Merah                             tabel to-ISP1
#   ONNET ........... Telkom -> Merah, XL -> Booster
#
#   Booster/Biru turun kualitas -> netwatch pindahkan ke Metro + Merah.
#   Starlink distance 9 di semua tabel (cadangan terakhir).
# ==========================================================================


# --------------------------------------------------------------------------
# 1. FB / IG ke Booster, TikTok ke Biru
# --------------------------------------------------------------------------
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=FB-conn] new-routing-mark=to-VIDEO comment="FB - jalur Booster"
/ip firewall mangle set [find chain=prerouting action=mark-routing connection-mark=TT-conn] new-routing-mark=to-VIDEO3 comment="TT - jalur Biru"
/ip firewall mangle set [find comment="META FB IG via Biru"] new-routing-mark=to-VIDEO comment="META FB IG via Booster"
# Rule FB di chain output (trafik router sendiri) tidak perlu lewat Metro
/ip firewall mangle disable [find chain=output new-routing-mark=to-ISP6 comment~"FB"]


# --------------------------------------------------------------------------
# 2. PCC umum: Merah 14 bucket, Metro 10 bucket (Metro digenjot, dedicated)
#    Kurangi/tambah angka di daftar Metro kalau perlu.
# --------------------------------------------------------------------------
{
  :local metro {1;3;5;7;9;11;13;15;19;23}
  :for b from=0 to=23 do={
    :local pcc ("both-addresses-and-ports:24/" . $b)
    :local mark "ISP1-conn"
    :if ([:typeof [:find $metro $b]] != "nil") do={ :set mark "ISP6-conn" }
    /ip firewall mangle set [find chain=prerouting action=mark-connection per-connection-classifier=$pcc] new-connection-mark=$mark
  }
}


# --------------------------------------------------------------------------
# 3. Tabel cadangan (hanya ditambah kalau belum ada)
# --------------------------------------------------------------------------
# to-ISP6 (umum Metro): Metro -> Merah -> Biru -> Booster -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-ISP6" gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=to-ISP6 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Merah" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=to-ISP6 distance=3 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Biru" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=to-ISP6 distance=4 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Booster" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-ISP6 distance=5 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad FPP" }
:if ([:len [/ip route find routing-table="to-ISP6" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-ISP6 distance=9 target-scope=11 check-gateway=ping comment="FINAL to-ISP6 cad Starlink" }

# to-VIDEO (FB/YT, Booster): Booster -> Metro + Merah -> Biru -> FPP -> Starlink
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

# to-ISP1 (umum Merah): Merah -> Metro -> Biru -> Booster -> FPP -> Starlink
:if ([:len [/ip route find routing-table="to-ISP1" gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=to-ISP1 distance=2 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Metro" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=to-ISP1 distance=3 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Biru" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=to-ISP1 distance=4 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Booster" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="149.112.112.112"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=149.112.112.112 routing-table=to-ISP1 distance=5 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad FPP" }
:if ([:len [/ip route find routing-table="to-ISP1" gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=to-ISP1 distance=9 target-scope=11 check-gateway=ping comment="FINAL to-ISP1 cad Starlink" }

# to-MERAH (game) dan to-WA: FPP -> Merah -> Metro -> Biru -> Booster -> Starlink
:foreach t in={"to-MERAH";"to-WA"} do={
  :if ([:len [/ip route find routing-table=$t gateway="1.0.0.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=1.0.0.1 routing-table=$t distance=2 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Merah") }
  :if ([:len [/ip route find routing-table=$t gateway="8.8.8.8"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=8.8.8.8 routing-table=$t distance=3 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Metro") }
  :if ([:len [/ip route find routing-table=$t gateway="4.2.2.1"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.1 routing-table=$t distance=4 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Biru") }
  :if ([:len [/ip route find routing-table=$t gateway="9.9.9.9"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=9.9.9.9 routing-table=$t distance=5 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Booster") }
  :if ([:len [/ip route find routing-table=$t gateway="4.2.2.2"]]=0) do={ /ip route add dst-address=0.0.0.0/0 gateway=4.2.2.2 routing-table=$t distance=9 target-scope=11 check-gateway=ping comment=("FINAL " . $t . " cad Starlink") }
}


# --------------------------------------------------------------------------
# 4. Perawatan
# --------------------------------------------------------------------------
# DNS static FWD bikin NXDOMAIN FB/TikTok - pastikan mati
/ip dns static disable [find type=FWD]
# Label interface supaya tidak tertukar
/interface vlan set [find name=vlan180] comment="Metro Indosat 100 dedicated"
# Starlink tidak boleh pasang default route sendiri
/ip dhcp-client set [find interface=ether5] add-default-route=no


# --------------------------------------------------------------------------
# 5. Putus koneksi FB/TikTok lama supaya langsung ikut jalur baru
# --------------------------------------------------------------------------
:foreach m in={"FB-conn";"TT-conn"} do={
  :foreach c in=[/ip firewall connection find connection-mark=$m] do={
    :do { /ip firewall connection remove $c } on-error={}
  }
}


# --------------------------------------------------------------------------
# 6. Laporan & backup
# --------------------------------------------------------------------------
:log info ("FINAL: bucket Metro = " . [:len [/ip firewall mangle find chain=prerouting new-connection-mark=ISP6-conn]] . " (harus 10)")
:log info ("FINAL: rule FB ke Booster = " . [:len [/ip firewall mangle find chain=prerouting action=mark-routing connection-mark=FB-conn new-routing-mark=to-VIDEO]])
:log info ("FINAL: rule TT ke Biru = " . [:len [/ip firewall mangle find chain=prerouting action=mark-routing connection-mark=TT-conn new-routing-mark=to-VIDEO3]])
/export file=config-final
:log info "FINAL: selesai, backup tersimpan di config-final.rsc"
