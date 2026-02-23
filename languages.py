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
        
        # Help window - TABS STRUCTURE
        "help_title": "❓ Bantuan Lengkap - Cacti AutoData",
        "help_tabs": {
            "Pengenalan": """Selamat datang di **Cacti AutoData**! 🌵

Aplikasi ini dibuat khusus untuk mengotomatisasi perekaman data bandwidth (Traffic In / Out) dari server Cacti ke dalam file laporan Excel ataupun Google Forms.

**Keunggulan Utama:**
• **Bypass Login Manual:** Mengambil data sesion langsung dari Browser Chrome Anda (via Cookie).
• **Mode Excel:** Memampatkan nilai *Current, Average, Max* ke letak kolom/baris yang tepat di template Excel perusahaan Anda.
• **Mode Google Form:** Menarik data 24-Jam penuh tanpa batasan jam kerja untuk diunggah otomatis ke Formulir.""",
            
            "Tab Utama (Excel)": """**Fungsi:** Mengambil data spesifik berdasarkan jam (09:00 & 16:00) untuk ditulis ke Excel.

**Langkah-langkah:**
1. Klik 📅 pada **Tanggal Mulai** dan **Tanggal Akhir**.
2. Klik **Browse** untuk memuat file Template Excel Anda.
3. Di bagian bawah (*Centang Sheet*), pilih sheet (ISP) mana saja yang ingin diproses.
4. Klik **🚀 Mulai Rekap**. Data akan ditarik dari Cacti namun *TIDAK LANGSUNG* ditulis ke Excel. Data tersebut akan mampir ke tab **Preview** terlebih dahulu.

**Opsi Tambahan (Options):**
• *Skip filled rows:* Melewati baris/tanggal yang sudah terisi di Excel.
• *Skip weekend:* Lewati pencarian data untuk hari Sabtu & Minggu.
• *Skip Libur Nasional:* Lewati tanggal-tanggal merah & Cuti Bersama secara mutlak (terhubung ke kalender online).
• *Dry Run:* Menyimulasikan proses penarikan tanpa risiko salah mengubah data (aman untuk diuji coba).""",
            
            "Tab Settings & Cookie": """**Pengaturan Aplikasi (Settings)**

• **Cookie Browser:** Aplikasi Cacti biasa membutuhkan otorisasi. Klik **"Setel Cookie Chrome dari Clipboard"** setelah Anda login di browser agar aplikasi memiliki izin akses otomatis. Tombol **"Bantuan Menyiapkan Cookie"** akan mengajarkan Anda cara menyalin string Cookie dari DevTools.
• **URL Cacti:** Alamat root/graph utama dari Cacti.
• **Format Waktu:** Sesuaikan dengan komputer / Excel Anda (Titik vs Titik Dua).
• **Mapping Interface:** Hubungkan ID Graf Cacti spesifik ("Localhost - Traffic - eth0") ke nama sheet yang diakui di file Excel Anda.""",
            
            "Tab Preview": """**Mengecek & Menyimpan Data Excel**

Setelah proses di Tab Utama selesai, pindahlah ke Tab ini.
Anda akan melihat tabel berisi nilai **Cur In, Cur Out, Max In, dsb** beserta statusnya *(Siap Tulis, Sudah Terisi, dsb)*.

• Data dikelompokkan berdasarkan Sheet/ISP (lihat deretan tombol tab kecil di atas tabel).
• Jika Anda yakin nilainya benar, klik **"💾 Tulis ke Excel Asli"**. Output akhir (laporan yang sudah dirapikan) akan tersimpan secara terpisah di dalam folder **`results/`** agar file template asli kantor Anda tidak rusak.""",
            
            "Tab Upload Form": """**Fungsi:** Form Upload berfungsi menyetor kapasitas absolut harian (Max Out) langsung ke Google Form (Survei/Evaluasi kapasitas).

**Perbedaan Utama:**
Fitur ini independen dari Excel! Ia akan mendownload log raw CSV selama **00:00 hingga 23:59** untuk menemukan puncak kecepatan absolut dalam 24-jam penuh.

**Langkah:**
1. Isikan Link Google Form Anda (yang sudah diatur jadi Akses Publik / Bukan untuk internal organisasi perusahaan saja).
2. Isi rentang tanggal.
3. Klik **"🔍 Tarik Data 24-Jam & Preview"**.
4. Setelah tabel terisi penuh, perhatikan baris yang memiliki ikon kotak centang `[x]`. Anda bisa membatalkan/mencentang ulang hari tertentu jika ingin di-skip.
5. Klik **"▶️ Upload ke Google Form"**. Perhatikan log status _real-time_ di sebelah kanan panel!""",
            
            "Troubleshooting": """**Tanya Jawab Error Umum:**

**Q: Tarik Form Google 'HTTP Error 401 Unauthorized' tertahan selamanya?**
A: Pastikan di _Setting Form_ milik pembuat (di Google Forms), opsi "Batasi untuk organisasi [Perusahaan]..." sedang DIMATIKAN. Robot tidak bisa login Google, jadi butuh form akses publik.

**Q: Error "Cookie tidak valid / Sesi habis"**
A: Buka web Cacti Anda di Google Chrome, pastikan Anda dalam kondisi ter-login. Tekan F12 -> Network. Buka ulang salah satu Graphic. Temukan header `Cookie` di Request Headers, copy teks panjangnya. Kembali ke app: Settings -> Paste & Setel Cookie.

**Q: Kok Kabeh jadi "0.27 M" bukan "270 K"?**
A: Jika Anda mendapatkan versi lawas, bug pembulatan teks ini sudah diperbaiki di Versi 2! Aplikasi sudah mengenali pecahan Gigabits, Megabits, dan Kilobits.

**Q: File hasil 'Permission Error / Akses Ditolak'**
A: Artinya file Excel tersebut sedang terbuka di Office/aplikasi lain. Tutup pelan-pelan MS Excel Anda, lalu klik `Retry` di Cacti AutoData."""
        },
        "help_creator": "Dibuat & Dikembangkan oleh: Rofikul Huda | GitHub: @rfypych",
        
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
        
        # Help window - TABS STRUCTURE
        "help_title": "❓ Comprehensive Help - Cacti AutoData",
        "help_tabs": {
            "Introduction": """Welcome to **Cacti AutoData**! 🌵

This application automates the scraping of bandwidth reports (Traffic In / Out) from your Cacti server, restructuring them into Excel spreadsheets or Google Forms.

**Core Highlights:**
• **Cookie Authentication:** Uses your browser's existing Cacti login session. No credentials saved locally!
• **Excel Mode:** Scrapes exact 09:00 / 16:00 snapshots to smartly map values (`Current`, `Average`, `Max`) directly into complex corporate Excel Templates.
• **Google Form Mode:** Extracts full 24-Hour absolut peaks automatically parsing daily boundaries.""",
            
            "Main Tab (Excel)": """**Function:** Initiates snapshot data fetching for Excel report generation.

**Steps:**
1. Click 📅 on **Start Date** and **End Date** to select range.
2. Click **Browse** to target your company's blank/existing Excel template.
3. Select which Interface Sheets you want to evaluate via checkboxes.
4. Click **🚀 Start Recording**. The data will be downloaded from your Cacti server into memory (it WON'T instantly touch the Excel file. It halts at the Preview Tab).

**Configuration Toggles:**
• *Skip filled rows:* Bypasses any date row in Excel that already contains data.
• *Skip weekend:* Ignores Saturday & Sunday completely.
• *Skip National Holidays:* Bypasses Red Dates and recognized "Cuti Bersama" via dynamic API calendars.
• *Dry Run:* Test scraping engine without actually risking Excel file corruption.""",
            
            "Settings & Cookie Tab": """**Application Setup**

• **Browser Cookie:** This app needs authorization limits from your PC. Login to Cacti manually inside Google Chrome, grab the Cookie from Network DevTools, and click **"Set Cookie from Clipboard"**. Click the "Help" icon next to it if you're lost.
• **Cacti URL:** Point to your company's Cacti graph tree root.
• **Time Format:** Excel expects either HH:MM or HH.MM (Dots vs Colons) depending on local settings.
• **Interface Mapping:** Route internal Graph IDs ("Localhost - Traffic - eth0") strictly to matching Sheet names defined manually in your Excel Template.""",
            
            "Preview Tab": """**Verifying & Writing Excel Data**

Post-scraping from the Main Tab, navigate here to manually vet the results.
You'll see grouped tables rendering **Cur In, Max Out, etc**, accompanied by predicted Actions (New Write, Update, Skip).

• Data is grouped via ISP (Top mini tabs).
• When verified, finalize via **"💾 Write to Excel"**. The output gets constructed safely inside the **`results/`** folder. Original templates remain perfectly intact and unharmed.""",
            
            "Form Upload Tab": """**Function:** Dedicated tool to upload 24-Hour absolute capacity peaks directly to Google Forms.

**Differences vs Excel Mode:**
This completely bypasses Excel! The app will literally evaluate the 00:00 - 23:59 graph data range for any given day, ignoring arbitrary working hours, guaranteeing the absolute Maximum Threshold is located.

**Steps:**
1. Provide the Target Google Form URL (Must be Public!).
2. Set Date boundaries.
3. Click **"🔍 Fetch 24H Peak Data & Preview"**.
4. You can uncheck dates via the list box `[x]`. 
5. Click **"▶️ Upload to Google Form"** and monitor the live HTTP post-results.""",
            
            "Troubleshooting": """**Common Issues Q&A:**

**Q: Google Form Upload hangs / throws 'HTTP Error 401 Unauthorized'?**
A: In your Google Form Settings page, ensure the option "Restrict to users in [Organization]..." is completely DISABLED. AutoData bot is unauthenticated.

**Q: Error: "Cookie Invalid / Session Timeout"**
A: Your Cacti session expired. Go back to Chrome, interact with Cacti once, extract the fresh `Cookie` header via F12 Network panel, and paste it back to Settings.

**Q: File result 'Permission Error / Access Denied'**
A: Most likely caused by Excel locking the file visibly. Fully close Microsoft Excel, return to Cacti AutoData, and hit `Retry`."""
        },
        "help_creator": "Created & Maintained by: Rofikul Huda | GitHub: @rfypych",
        
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
