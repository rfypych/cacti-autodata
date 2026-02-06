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
        
        # Help window - IMPROVED
        "help_title": "❓ Bantuan - Cacti AutoData",
        "help_basic_title": "📋 LANGKAH DASAR",
        "help_basic_steps": """1. Pastikan terhubung ke jaringan kantor
2. Pilih range tanggal (klik 📅 untuk kalender)
3. Browse file Excel dari kantor
4. Pilih sheet yang akan diproses
5. Klik "🚀 Mulai Rekap\"""",

        "help_features_title": "✨ FITUR LENGKAP",
        "help_features": """🏠 Tab Main      → Input data & mulai proses
⚙️ Tab Settings  → Ubah URL, format waktu, mapping
👁️ Tab Preview   → Lihat data sebelum ditulis

📑 Sheet Selector → Pilih sheet mana yang diproses
🧪 Dry Run Mode   → Test tanpa menulis ke Excel
💾 Export Log     → Simpan log ke file .txt
🔄 Auto-Save      → Settings & path tersimpan otomatis""",

        "help_tips_title": "💡 TIPS",
        "help_tips": """• Skip Filled Rows = lewati baris yang sudah terisi
• Gunakan Dry Run dulu untuk test
• Cek Preview sebelum Write to Excel
• Settings tersimpan di user_settings.json""",

        "help_warnings_title": "⚠️ PERINGATAN",
        "help_warning1": "Jangan tutup browser saat proses berjalan!",
        "help_warning2": "Backup Excel sebelum proses pertama kali",
        "help_warning3": "Pastikan file Excel tidak sedang dibuka di program lain",
        
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
        
        # Help window - IMPROVED
        "help_title": "❓ Help - Cacti AutoData",
        "help_basic_title": "📋 BASIC STEPS",
        "help_basic_steps": """1. Make sure you're connected to office network
2. Select date range (click 📅 for calendar)
3. Browse to your Excel file
4. Select which sheets to process
5. Click "🚀 Start Recording\"""",

        "help_features_title": "✨ FEATURES",
        "help_features": """🏠 Main Tab      → Input data & start process
⚙️ Settings Tab  → Change URL, time format, mapping
👁️ Preview Tab   → View data before writing

📑 Sheet Selector → Choose which sheets to process
🧪 Dry Run Mode   → Test without writing to Excel
💾 Export Log     → Save log to .txt file
🔄 Auto-Save      → Settings & paths saved automatically""",

        "help_tips_title": "💡 TIPS",
        "help_tips": """• Skip Filled Rows = skip rows with existing data
• Use Dry Run first to test
• Check Preview before Write to Excel
• Settings saved in user_settings.json""",

        "help_warnings_title": "⚠️ WARNINGS",
        "help_warning1": "Don't close browser while process is running!",
        "help_warning2": "Backup Excel before first run",
        "help_warning3": "Make sure Excel file is not open elsewhere",
        
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
