# ============================================================
# KONFIGURASI CACTI AUTODATA
# ============================================================
# File ini berisi semua pengaturan yang perlu disesuaikan
# saat di kantor. Ubah nilai-nilai di bawah sesuai kebutuhan.
# ============================================================

# URL Cacti (sesuaikan dengan URL kantor)
CACTI_URL = "http://monitor.kabngawi.id/cacti/graph_view.php"

# Mapping interface Cacti ke nama sheet Excel
# Key = teks yang muncul di judul graph Cacti
# Value = nama sheet di Excel (harus persis sama, case-sensitive)
INTERFACE_TO_SHEET = {
    "ether4-iForte": "iForte",
    "ether5-Telkom": "Telkom",
    "ether6-Moratel": "Moratel",
}

# Slot waktu yang akan diambil datanya
# Format: (jam, menit)
TIME_SLOTS = [
    (9, 0),   # 09:00
    (16, 0),  # 16:00
]

# ============================================================
# KONFIGURASI KOLOM EXCEL
# ============================================================
# Sesuaikan nama kolom dengan yang ada di file Excel kantor
# Bisa berupa nama kolom (string) atau nomor kolom (integer, 1-indexed)

# Kolom untuk tanggal (biasanya kolom A = 1)
EXCEL_COL_TANGGAL = 1  # atau "tanggal"

# Kolom untuk waktu (biasanya kolom B = 2)
EXCEL_COL_WAKTU = 2  # atau "waktu"

# Kolom data bandwidth
EXCEL_COL_CURR_IN = 3   # Current Inbound
EXCEL_COL_CURR_OUT = 4  # Current Outbound
EXCEL_COL_MAX_IN = 5    # Maximum Inbound
EXCEL_COL_MAX_OUT = 6   # Maximum Outbound
EXCEL_COL_AVG_IN = 7    # Average Inbound
EXCEL_COL_AVG_OUT = 8   # Average Outbound

# ============================================================
# FORMAT WAKTU DI EXCEL
# ============================================================
# Sesuaikan format waktu yang dipakai di Excel kantor
# Contoh: "09:00", "09:00:00", "9:00", dll.

# Format waktu untuk matching (gunakan strftime format)
# %H = jam 24-hour dengan leading zero (09)
# %M = menit dengan leading zero (00)
# %S = detik dengan leading zero (00)
TIME_FORMAT_EXCEL = "%H:%M"  # Contoh hasil: "09:00"

# Alternatif format jika perlu detik:
# TIME_FORMAT_EXCEL = "%H:%M:%S"  # Contoh hasil: "09:00:00"

# ============================================================
# FORMAT TANGGAL DI EXCEL
# ============================================================
# Format tanggal yang dipakai di Excel
# %d = tanggal dengan leading zero (01)
# %m = bulan dengan leading zero (02)
# %Y = tahun 4 digit (2026)

DATE_FORMAT_EXCEL = "%d/%m/%Y"  # Contoh hasil: "01/02/2026"

# Alternatif format:
# DATE_FORMAT_EXCEL = "%Y-%m-%d"  # Contoh hasil: "2026-02-01"

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
# Biasanya baris 2 jika baris 1 adalah header
EXCEL_DATA_START_ROW = 2
