# ============================================================
# KONFIGURASI CACTI AUTODATA — TEMPLATE
# ============================================================
# Salin file ini menjadi config.py dan sesuaikan nilai-nilainya.
#   copy config.example.py config.py
# ============================================================

# URL Cacti (sesuaikan dengan URL kantor Anda)
CACTI_URL = "https://your-cacti-server.example.com/cacti/graph_view.php?action=tree&node=tbranch-XX&host_id=XX"

# Mapping interface Cacti ke nama sheet Excel
# Key = teks yang muncul di judul graph Cacti
# Value = nama sheet di Excel (harus persis sama, case-sensitive)
INTERFACE_TO_SHEET = {
    "LocalNet": "LocalNet",
    "iForte": "iForte",
    "Telkom": "Telkom",
    "Moratel": "Moratel",
}

# ==== Scraping Options ====
SKIP_WEEKENDS = True  # Default value, can be changed via GUI settings
SKIP_HOLIDAYS = False # Default value, can be changed via GUI settings

# Slot waktu yang akan diambil datanya
TIME_SLOTS = [
    (9, 0),   # 09.00
    (16, 0),  # 16.00
]

# ============================================================
# KONFIGURASI KOLOM EXCEL
# ============================================================
EXCEL_COL_TANGGAL = 1    # Kolom A
EXCEL_COL_WAKTU = 2      # Kolom B
EXCEL_COL_CURR_IN = 3    # Kolom C
EXCEL_COL_CURR_OUT = 4   # Kolom D
EXCEL_COL_MAX_IN = 5     # Kolom E
EXCEL_COL_MAX_OUT = 6    # Kolom F
EXCEL_COL_AVG_IN = 7     # Kolom G
EXCEL_COL_AVG_OUT = 8    # Kolom H

# ============================================================
# KONFIGURASI GOOGLE FORM (UPLOAD OTOMATIS)
# ============================================================
# URL Google Form (pastikan URL yang berakhiran /viewform)
GOOGLE_FORM_URL = ""

# Mapping ID Isian Form (dapatkan via Inspect Element -> "entry.XXXXXXX")
GOOGLE_FORM_ENTRIES = {
    "tanggal": "entry.",
    "total": "entry.",
    "moratel": "entry.",
    "iforte": "entry.",
    "telkom": "entry.",
}

# ============================================================
# FORMAT WAKTU DI EXCEL
# ============================================================
# Format waktu yang dipakai di Excel kantor
# PENTING: Excel kantor pakai TITIK bukan TITIK DUA!
TIME_FORMAT_EXCEL = "%H.%M"       # "09.00", "16.00"
DATE_FORMAT_EXCEL = "%d/%m/%Y"    # "02/01/2026"

# ============================================================
# PENGATURAN BROWSER
# ============================================================
SHOW_BROWSER = True
PAGE_LOAD_TIMEOUT = 30
ACTION_DELAY = 1.0

# ============================================================
# PENGATURAN EXCEL
# ============================================================
EXCEL_DATA_START_ROW = 2
SKIP_FILLED_ROWS = True
