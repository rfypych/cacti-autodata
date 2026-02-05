# ============================================================
# LANGUAGE STRINGS - DUAL LANGUAGE SUPPORT
# ============================================================
# Indonesian (id) and English (en)
# ============================================================

LANGUAGES = {
    "id": {
        "app_title": "🌵 Cacti AutoData - Bandwidth Recorder",
        "subtitle": "Otomatis rekap data bandwidth dari Cacti ke Excel",
        
        # Input section
        "input_title": "📅 Input Data",
        "start_date": "Tanggal Mulai:",
        "end_date": "Tanggal Akhir:",
        "excel_file": "File Excel:",
        "date_format_hint": "(format: DD/MM/YYYY)",
        "browse": "Browse",
        
        # Config section
        "config_title": "⚙️ Konfigurasi Aktif",
        "config_url": "URL Cacti",
        "config_interface": "Interface",
        "config_sheet": "Sheet Excel",
        "config_time": "Slot Waktu",
        "config_hint": "💡 Ubah file config.py jika perlu menyesuaikan pengaturan",
        
        # Progress section
        "progress_title": "📊 Progress",
        "status_waiting": "Menunggu...",
        "status_starting": "Memulai proses...",
        "status_complete": "✅ Proses selesai!",
        "status_stopped": "⏹️ Proses dihentikan oleh user",
        "status_no_data": "⚠️ Tidak ada data yang berhasil diambil!",
        
        # Buttons
        "btn_start": "🚀 Mulai Rekap",
        "btn_stop": "⏹️ Berhenti",
        "btn_help": "❓ Help",
        "btn_exit": "❌ Keluar",
        
        # Help window
        "help_title": "❓ Bantuan - Cara Penggunaan",
        "help_header": "📋 Langkah-Langkah Penggunaan",
        "help_steps": """
1️⃣  Pastikan Anda terhubung ke jaringan kantor
     (komputer harus bisa mengakses Cacti)

2️⃣  Isi tanggal mulai dan tanggal akhir sesuai
     range yang ingin direkap

3️⃣  Klik "Browse" untuk memilih file Excel
     yang sudah disediakan dari kantor

4️⃣  Klik "🚀 Mulai Rekap" dan tunggu prosesnya
     selesai

5️⃣  Program akan otomatis membuka browser,
     mengambil data, dan mengisi Excel""",
        "help_warning1": "⚠️  Jangan tutup browser yang terbuka saat proses berjalan!",
        "help_warning2": "⚠️  Jika ada error, periksa file config.py untuk menyesuaikan pengaturan",
        "help_creator": "Dibuat oleh: Rofikul Huda | GitHub: @rfypych",
        
        # Messages
        "error_start_date": "Format tanggal mulai salah!\nGunakan format: DD/MM/YYYY",
        "error_end_date": "Format tanggal akhir salah!\nGunakan format: DD/MM/YYYY",
        "error_date_range": "Tanggal akhir harus >= tanggal mulai!",
        "error_no_file": "Pilih file Excel terlebih dahulu!",
        "success_title": "Sukses",
        "success_message": "Berhasil merekap {count} data ke Excel!",
        "stop_warning": "Proses akan berhenti setelah langkah saat ini selesai",
    },
    
    "en": {
        "app_title": "🌵 Cacti AutoData - Bandwidth Recorder",
        "subtitle": "Automatically record bandwidth data from Cacti to Excel",
        
        # Input section
        "input_title": "📅 Input Data",
        "start_date": "Start Date:",
        "end_date": "End Date:",
        "excel_file": "Excel File:",
        "date_format_hint": "(format: DD/MM/YYYY)",
        "browse": "Browse",
        
        # Config section
        "config_title": "⚙️ Active Configuration",
        "config_url": "Cacti URL",
        "config_interface": "Interface",
        "config_sheet": "Excel Sheet",
        "config_time": "Time Slots",
        "config_hint": "💡 Edit config.py file to adjust settings",
        
        # Progress section
        "progress_title": "📊 Progress",
        "status_waiting": "Waiting...",
        "status_starting": "Starting process...",
        "status_complete": "✅ Process complete!",
        "status_stopped": "⏹️ Process stopped by user",
        "status_no_data": "⚠️ No data was retrieved!",
        
        # Buttons
        "btn_start": "🚀 Start Recording",
        "btn_stop": "⏹️ Stop",
        "btn_help": "❓ Help",
        "btn_exit": "❌ Exit",
        
        # Help window
        "help_title": "❓ Help - How to Use",
        "help_header": "📋 Step-by-Step Guide",
        "help_steps": """
1️⃣  Make sure you are connected to the office network
     (computer must be able to access Cacti)

2️⃣  Fill in the start date and end date according
     to the range you want to record

3️⃣  Click "Browse" to select the Excel file
     provided by the office

4️⃣  Click "🚀 Start Recording" and wait for the
     process to complete

5️⃣  The program will automatically open a browser,
     retrieve data, and fill in the Excel file""",
        "help_warning1": "⚠️  Do not close the browser while the process is running!",
        "help_warning2": "⚠️  If there's an error, check config.py to adjust settings",
        "help_creator": "Created by: Rofikul Huda | GitHub: @rfypych",
        
        # Messages
        "error_start_date": "Invalid start date format!\nUse format: DD/MM/YYYY",
        "error_end_date": "Invalid end date format!\nUse format: DD/MM/YYYY",
        "error_date_range": "End date must be >= start date!",
        "error_no_file": "Please select an Excel file first!",
        "success_title": "Success",
        "success_message": "Successfully recorded {count} data to Excel!",
        "stop_warning": "Process will stop after the current step completes",
    }
}

# Default language
DEFAULT_LANGUAGE = "id"

def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """Get localized text by key"""
    text = LANGUAGES.get(lang, LANGUAGES[DEFAULT_LANGUAGE]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
