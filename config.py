# ============================================================
# KONFIGURASI CACTI AUTODATA
# ============================================================
# File ini berisi semua pengaturan yang perlu disesuaikan
# saat di kantor. Ubah nilai-nilai di bawah sesuai kebutuhan.
# ============================================================

# URL Cacti (sesuaikan dengan URL kantor)
# Halaman yang menampilkan 4 chart: LocalNet, iForte, Telkom, Moratel
CACTI_URL = "https://monitor.kabngawi.id/cacti/graph_view.php?action=tree&node=tbranch-169&host_id=101&site_id=-1&host_template_id=-1&hgd=&hyper=true&rfilter="

# Mapping interface Cacti ke nama sheet Excel
# Key = teks yang muncul di judul graph Cacti
# Value = nama sheet di Excel (harus persis sama, case-sensitive)
INTERFACE_TO_SHEET = {
    "LocalNet": "LocalNet", # Was ether2-LocalNet
    "iForte": "iForte",     # Was ether4-iForte
    "Telkom": "Telkom",     # Was ether5-Telkom
    "Moratel": "Moratel",   # Was ether6-Moratel
}

# Mapping interface ke Graph ID Cacti (untuk mode tanpa Selenium)
# Didapat dari inspect HTML halaman Cacti
GRAPH_IDS = {
    "iForte": "1503",
    "Telkom": "1573",
    "Moratel": "1528",
}

# Slot waktu yang akan diambil datanya
# Format: (jam, menit)
TIME_SLOTS = [
    (9, 0),   # 09.00
    (16, 0),  # 16.00
]

# ============================================================
# KONFIGURASI KOLOM EXCEL
# ============================================================
# Sesuai dengan struktur Excel asli dari kantor

# Kolom untuk tanggal (kolom A = 1)
EXCEL_COL_TANGGAL = 1

# Kolom untuk waktu (kolom B = 2)
EXCEL_COL_WAKTU = 2

# Kolom data bandwidth
EXCEL_COL_CURR_IN = 3   # Kolom C: Curent(IN)
EXCEL_COL_CURR_OUT = 4  # Kolom D: Curent (Out)
EXCEL_COL_MAX_IN = 5    # Kolom E: Max (IN)
EXCEL_COL_MAX_OUT = 6   # Kolom F: Max (Out)
EXCEL_COL_AVG_IN = 7    # Kolom G: Average (IN)
EXCEL_COL_AVG_OUT = 8   # Kolom H: Average (Out)

# ============================================================
# FORMAT WAKTU DI EXCEL
# ============================================================
# Format waktu yang dipakai di Excel kantor
# PENTING: Excel kantor pakai TITIK bukan TITIK DUA!
# Contoh: "09.00", "16.00"

TIME_FORMAT_EXCEL = "%H.%M"  # Hasil: "09.00", "16.00"

# Alternatif jika pakai titik dua:
# TIME_FORMAT_EXCEL = "%H:%M"  # Hasil: "09:00", "16:00"

# ============================================================
# FORMAT TANGGAL DI EXCEL
# ============================================================
# Format tanggal yang dipakai di Excel
DATE_FORMAT_EXCEL = "%d/%m/%Y"  # Hasil: "02/01/2026"

# ============================================================
# PENGATURAN BROWSER
# ============================================================
# Tampilkan browser saat scraping? 
# True = browser terlihat (bagus untuk debugging)
# False = browser tersembunyi (headless mode)
SHOW_BROWSER = True

# Waktu tunggu maksimal (detik) untuk elemen halaman muncul
PAGE_LOAD_TIMEOUT = 30

# Waktu jeda antar aksi (detik)
ACTION_DELAY = 1.0

# ============================================================
# BARIS AWAL DATA DI EXCEL
# ============================================================
# Baris pertama yang berisi data (bukan header)
# Baris 1 adalah header, jadi data mulai dari baris 2
EXCEL_DATA_START_ROW = 2

# ============================================================
# FITUR SKIP BARIS TERISI
# ============================================================
# Jika True, program akan melewati baris yang sudah ada datanya
# dan hanya mengisi baris yang masih kosong
# ============================================================
# FITUR SKIP WEEKEND (SABTU & MINGGU)
# ============================================================
# Jika True, data hari Sabtu dan Minggu tidak akan diambil
SKIP_WEEKENDS = True
