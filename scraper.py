"""
Cacti Scraper Module
Mengambil data bandwidth dari halaman Cacti menggunakan Selenium

Features:
- Auto driver management (no webdriver-manager needed)
- Option to attach to existing Chrome session
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import config


class CactiScraper:
    """Scraper untuk mengambil data bandwidth dari Cacti"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize scraper
        
        Args:
            progress_callback: Fungsi callback untuk update progress (message, percentage)
        """
        self.driver = None
        self.progress_callback = progress_callback or (lambda msg, pct: None)
        self.attached_to_existing = False
    
    def _update_progress(self, message: str, percentage: int = -1):
        """Update progress via callback"""
        self.progress_callback(message, percentage)
    
    def start_browser(self, attach_to_existing: bool = False, debug_port: int = 9222):
        """
        Mulai browser Chrome
        
        Args:
            attach_to_existing: Jika True, coba connect ke Chrome yang sudah berjalan
            debug_port: Port untuk remote debugging (default: 9222)
        """
        import os
        
        chrome_options = Options()
        
        # Try to attach to existing Chrome session
        if attach_to_existing:
            self._update_progress(f"Mencoba connect ke Chrome (port {debug_port})...", 5)
            try:
                chrome_options.add_experimental_option("debuggerAddress", f"localhost:{debug_port}")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.attached_to_existing = True
                self._update_progress("✓ Berhasil connect ke Chrome yang sudah terbuka!", 10)
                return
            except Exception as e:
                self._update_progress(f"⚠ Tidak bisa connect ke Chrome existing")
                self._update_progress("Memulai browser Chrome baru...", 5)
        else:
            self._update_progress("Memulai browser Chrome...", 5)
        
        # Start new Chrome session with custom profile
        chrome_options = Options()  # Reset options
        
        # Use a dedicated profile for this app
        profile_dir = os.path.join(os.path.dirname(__file__), "chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        if not config.SHOW_BROWSER:
            chrome_options.add_argument("--headless=new")  # New headless mode
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable automation detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Selenium 4.6+ has built-in driver manager
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        self.attached_to_existing = False
        
        # Load cookies if available
        self._load_cookies()
        
        self._update_progress("Browser siap!", 10)
    
    def _load_cookies(self):
        """Load cookies from cacti_cookies.json if available"""
        import os
        import json
        
        cookies_file = os.path.join(os.path.dirname(__file__), "cacti_cookies.json")
        
        if "auth_login.php" in self.driver.current_url:
            self._update_progress("⚠ Terdeteksi halaman Login (cookie expired/invalid).")
            
            if not config.SHOW_BROWSER:
                self._update_progress("❌ Headless mode: Tidak bisa login manual. Stop.")
                return False
                
            self._update_progress("⏳ MENUNGGU LOGIN MANUAL...", 100)
            print("\n" + "="*50)
            print("SILAKAN LOGIN MANUAL DI BROWSER CHROME YANG TERBUKA")
            print("1. Masukkan Username & Password")
            print("2. Klik Login sampai masuk Dashboard")
            print("3. KEMBALI KE SINI dan tekan ENTER untuk lanjut...")
            print("="*50 + "\n")
            
            input("Tekan Enter setelah Anda berhasil Login...")
            
            # Save new cookies for next time
            import json
            cookies = self.driver.get_cookies()
            cookies_file = os.path.join(os.path.dirname(__file__), "cacti_cookies.json")
            
            # Convert to our JSON format
            json_cookies = []
            for c in cookies:
                json_cookies.append({
                    "name": c['name'],
                    "value": c['value'],
                    "domain": c.get('domain', ''),
                    "path": c.get('path', '/'),
                    "secure": c.get('secure', False)
                })
                
            with open(cookies_file, 'w') as f:
                json.dump(json_cookies, f, indent=2)
            self._update_progress(f"✅ Cookies baru disimpan ({len(cookies)} cookies)!", -1)
            
            # Refresh to confirm
            self.driver.get(config.CACTI_URL)
            time.sleep(3)
        
        # Cek lagi setelah potensi manual login
        if "auth_login.php" in self.driver.current_url:
            self._update_progress("❌ Masih di halaman login. Gagal.")
            return False
        
        if not os.path.exists(cookies_file):
            self._update_progress("ℹ Tidak ada cookies tersimpan (first run)")
            return
        
        try:
            # Navigate to the domain first (required for adding cookies)
            self.driver.get(config.CACTI_URL)
            
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                selenium_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                }
                
                # Add optional fields
                if cookie.get("path"):
                    selenium_cookie["path"] = cookie["path"]
                if cookie.get("secure"):
                    selenium_cookie["secure"] = True
                
                try:
                    self.driver.add_cookie(selenium_cookie)
                except:
                    pass
            
            self._update_progress(f"🍪 {len(cookies)} cookies dimuat (session tersimpan)")
            
            # Refresh to apply cookies
            self.driver.refresh()
            
        except Exception as e:
            self._update_progress(f"⚠ Gagal load cookies: {str(e)}")
    
    def close_browser(self):
        """Tutup browser (skip jika attached to existing)"""
        if self.driver:
            if self.attached_to_existing:
                self._update_progress("Browser existing tidak ditutup (managed externally)")
            else:
                self.driver.quit()
            self.driver = None
    
    def navigate_to_cacti(self):
        """Buka halaman Cacti"""
        self._update_progress(f"Membuka {config.CACTI_URL}...", 15)
        self.driver.get(config.CACTI_URL)
        time.sleep(config.ACTION_DELAY)
    
    def set_time_filter(self, date: datetime, hour: int, minute: int):
        """
        Set filter waktu di Cacti
        
        Args:
            date: Tanggal yang diinginkan
            hour: Jam target (untuk To)
            minute: Menit target (untuk To)
        """
        # Format tanggal untuk Cacti (YYYY-MM-DD HH:MM:SS)
        from_datetime = date.replace(hour=0, minute=0, second=0)
        to_datetime = date.replace(hour=hour, minute=minute, second=0)
        
        from_str = from_datetime.strftime("%Y-%m-%d %H:%M:%S")
        to_str = to_datetime.strftime("%Y-%m-%d %H:%M:%S")
        
        self._update_progress(f"Setting waktu: {from_str} → {to_str}")
        
        try:
            # Cari input From
            from_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='date1'], input[name*='date1'], input.dateTime1"))
            )
            from_input.clear()
            from_input.send_keys(from_str)
            
            # Cari input To
            to_input = self.driver.find_element(By.CSS_SELECTOR, "input[id*='date2'], input[name*='date2'], input.dateTime2")
            to_input.clear()
            to_input.send_keys(to_str)
            
            time.sleep(config.ACTION_DELAY)
            
            # Klik tombol Refresh/Go
            try:
                refresh_btn = self.driver.find_element(By.CSS_SELECTOR, "input[value='Refresh'], input[value='Go'], button:contains('Refresh')")
                refresh_btn.click()
            except:
                # Alternatif: tekan Enter
                to_input.send_keys("\n")
            
            # Tunggu halaman refresh
            time.sleep(config.ACTION_DELAY * 2)
            
        except Exception as e:
            self._update_progress(f"Warning: Gagal set filter waktu - {str(e)}")
    
    def extract_graph_data(self, start_ts: int = 0, end_ts: int = 0) -> Dict[str, Dict]:
        """
        Ekstrak data dari semua graph menggunakan fitur CSV Export Cacti
        
        Args:
            start_ts: Unix timestamp awal
            end_ts: Unix timestamp akhir
            
        Returns:
            Dictionary data bandwidth
        """
        result = {}
        processed_ids = set()
        
        try:
            # 1. Tunggu graph dimuat untuk memastikan page render
            WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[id*='wrapper_']"))
            )
            
            # 2. Cari semua graph ID (wrapper_1234)
            page_source = self.driver.page_source
            # Pattern: id="wrapper_1730"
            graph_ids = re.findall(r'id=["\']wrapper_(\d+)["\']', page_source)
            # Filter duplicates
            unique_graph_ids = list(set(graph_ids))
            
            # Quiet log
            # self._update_progress(f"Found {len(unique_graph_ids)} graphs: {unique_graph_ids}", -1)
            
            # 3. Setup session requests untuk download CSV
            import requests
            session = requests.Session()
            # Copy cookies dari Selenium driver ke requests session
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
            
            # User agent syncing (PENTING: Gunakan UA yang sama persis dengan browser)
            # Cacti bisa menolak session jika UA beda
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            session.headers.update({
                'User-Agent': user_agent,
                'Referer': config.CACTI_URL,
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # 4. Ambil dan parse CSV untuk setiap graph
            for graph_id in unique_graph_ids:
                if graph_id in processed_ids:
                    continue
                
                # Pass timestamp ke fungsi get_csv
                csv_data = self._get_csv_data(session, graph_id, start_ts, end_ts)
                if not csv_data:
                    continue
                
                # Cek Title untuk mapping ke interface name
                # Contoh Title: "Router BGP Ngawi - Traffic - ether2-LocalNet"
                title = csv_data.get("title", "")
                
                matched_interface = None
                for interface_key in config.INTERFACE_TO_SHEET.keys():
                    # Case insensitive check
                    if interface_key.lower() in title.lower():
                        matched_interface = interface_key
                        break
                
                if matched_interface:
                    stats = self._calculate_stats_from_csv(csv_data['rows'], csv_data['header'])
                    result[matched_interface] = stats
                    self._update_progress(f"✓ Data {matched_interface} berhasil diambil")
                    processed_ids.add(graph_id)
                else:
                    # Graph ini bukan target kita (misal CPU usage, dll)
                    pass

            # Isi None untuk interface yang tidak ditemukan
            for interface_name in config.INTERFACE_TO_SHEET.keys():
                if interface_name not in result:
                    self._update_progress(f"✗ Data {interface_name} tidak ditemukan")
                    result[interface_name] = None
                    
        except Exception as e:
            self._update_progress(f"Error saat extract data: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return result

    def _get_csv_data(self, session, graph_id: str, start_ts: int = 0, end_ts: int = 0) -> Optional[Dict]:
        """Download dan parse CSV dari Cacti"""
        import csv
        from io import StringIO
        from urllib.parse import urlparse
        
        # Parse Base URL untuk membuang query params yang ada di config.CACTI_URL
        parsed_url = urlparse(config.CACTI_URL)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        # Ganti graph_view.php dengan graph_xport.php
        xport_url = base_url.replace('graph_view.php', 'graph_xport.php')
        
        # Construct clean URL
        # rra_id=1 typical for Daily (5 Min Average) high res
        url = f"{xport_url}?local_graph_id={graph_id}&rra_id=1&view_type=tree"
        
        # Append specific time range if provided
        if start_ts > 0 and end_ts > 0:
            url += f"&graph_start={start_ts}&graph_end={end_ts}"
        
        # self._update_progress(f"    [DEBUG] URL: {url}", -1)
        
        try:
            resp = session.get(url, verify=False)
            if resp.status_code != 200:
                self._update_progress(f"Gagal download CSV ID {graph_id}: Status {resp.status_code}", -1)
                return None
            
            # Parse CSV Content
            content = resp.text
            # self._update_progress(f"    [DEBUG] Raw Content: {repr(content[:50])}...", -1)
            
            f = StringIO(content)
            reader = csv.reader(f)
            
            metadata = {}
            rows = []
            
            reading_data = False
            header_row = None
            
            for row in reader:
                if not row:
                    continue
                
                # Handle "Title" with potential BOM
                if len(row) >= 2 and "Title" in row[0]:
                    metadata['title'] = row[1]
                
                if row[0] == "Date":
                    reading_data = True
                    header_row = row
                    continue
                
                if reading_data:
                    rows.append(row)
            
            return {
                "title": metadata.get('title', ''),
                "header": header_row,
                "rows": rows
            }
            
        except Exception as e:
            self._update_progress(f"Error parsing CSV ID {graph_id}: {str(e)}", -1)
            return None

    def _calculate_stats_from_csv(self, rows: List[List[str]]) -> Dict:
        """Hitung statistik (Current/Avg/Max) dari data mentah CSV"""
        # Mapping kolom: biasanya col 1 & 3 adalah In & Out (setelah date)
        # Tapi header bisa: Date, col, Inbound, col, Outbound
        # Kita perlu cari index kolom yang valid
        
        # Sederhana: ambil 2 kolom numerik pertama yang kita temukan pada data row terakhir valid
        # Namun, kita butuh AVG val, MAX val, CURR val. 
        # CSV export (xport) Cacti "Daily" memberikan data per 5 menit (series).
        # Jadi kita harus hitung manual:
        # Current = Baris terakhir (atau rata-rata beberapa baris terakhir)
        # Average = Rata-rata seluruh baris
        # Max = Nilai maksimum seluruh baris
        
        in_values = []
        out_values = []
        
        for row in rows:
            # row[0] is Date
            # row[1]... are values. Some might be NaN.
            # Berdasarkan sampel: 
            # Date, col12(InVal), Inbound(InVal), col14(OutVal), Outbound(OutVal)
            # Jadi index 1 dan 3 (0-based: 1, 3) adalah raw val
            
            try:
                # Kolom 1 biasanya Inbound (jika format standar)
                # Parse float
                val_in = float(row[1]) if row[1] and row[1] != 'NaN' else 0.0
                in_values.append(val_in)
                
                # Kolom 3 biasanya Outbound
                # Cacti row length sample: 7 items (Date, val1, val1_rpt, val2, val2_rpt, ...)
                if len(row) > 3:
                     val_out = float(row[3]) if row[3] and row[3] != 'NaN' else 0.0
                     out_values.append(val_out)
            except (ValueError, IndexError):
                continue
                
        # Helper format
        def fmt(val):
            # Convert bits/sec to readable format
            # Val dari CSV biasanya bits per second (default Cacti)
            # Tapi user minta output "M" (Mega) atau "K". Format Excel AutoData sepertinya text "68.9 M"
            
            if val is None: return "0.00"
            
            # Cacti store raw bits.
            # Logic GUI lama: "Parse nilai bandwidth dari teks 63.98 M"
            # Logic baru: Kita punya raw float. Kita harus format jadi string mirip Cacti UI
            
            # Auto scale
            abs_val = abs(val)
            if abs_val >= 1e9:
                return f"{val/1e9:.2f} G"
            elif abs_val >= 1e6:
                return f"{val/1e6:.2f} M"
            elif abs_val >= 1e3:
                return f"{val/1e3:.2f} K"
            else:
                return f"{val:.2f}"

        # Calculate Stats
        # Current = Last value
        curr_in = in_values[-1] if in_values else 0
        curr_out = out_values[-1] if out_values else 0
        
        # Average
        avg_in = sum(in_values) / len(in_values) if in_values else 0
        avg_out = sum(out_values) / len(out_values) if out_values else 0
        
        # Max
        max_in = max(in_values) if in_values else 0
        max_out = max(out_values) if out_values else 0
        
        return {
            "curr_in": fmt(curr_in),
            "avg_in": fmt(avg_in),
            "max_in": fmt(max_in),
            "curr_out": fmt(curr_out),
            "avg_out": fmt(avg_out),
            "max_out": fmt(max_out),
        }
    
    def scrape_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Scrape data untuk range tanggal
        
        Args:
            start_date: Tanggal mulai
            end_date: Tanggal akhir
            
        Returns:
            List of dictionaries dengan data per tanggal dan waktu
        """
        all_data = []
        
        # Hitung total iterasi untuk progress
        days = (end_date - start_date).days + 1
        total_iterations = days * len(config.TIME_SLOTS)
        current_iteration = 0
        
        current_date = start_date
        while current_date <= end_date:
            for hour, minute in config.TIME_SLOTS:
                current_iteration += 1
                progress = 15 + int((current_iteration / total_iterations) * 70)
                
                time_str = f"{hour:02d}:{minute:02d}"
                date_str = current_date.strftime(config.DATE_FORMAT_EXCEL)
                
                self._update_progress(
                    f"Mengambil data {date_str} {time_str}...",
                    progress
                )
                
                # Set filter waktu
                self.set_time_filter(current_date, hour, minute)
                
                # Hitung timestamp untuk URL export
                # Cacti butuh Unix timestamp
                # Strategi: Selalu ambil dari jam 00:00 sampai jam target
                # Ini mensimulasikan "Graph View" harian
                from_dt = current_date.replace(hour=0, minute=0, second=0)
                to_dt = current_date.replace(hour=hour, minute=minute, second=0)
                
                start_ts = int(from_dt.timestamp())
                end_ts = int(to_dt.timestamp())
                
                # Tambahkan buffer 5 menit ke end_ts untuk memastikan data jam 16:00 masuk (inclusive)
                # Cacti kadang memotong pas di detik akhir
                end_ts += 300 
                
                time.sleep(config.ACTION_DELAY)
                
                # Ekstrak data dengan timestamp eksplisit
                graph_data = self.extract_graph_data(start_ts, end_ts)
                
                # Simpan dengan metadata tanggal/waktu
                for interface_name, data in graph_data.items():
                    if data:
                        all_data.append({
                            "date": current_date,
                            "time_hour": hour,
                            "time_minute": minute,
                            "interface": interface_name,
                            "sheet": config.INTERFACE_TO_SHEET.get(interface_name),
                            **data
                        })
            
            current_date += timedelta(days=1)
        
        self._update_progress(f"Selesai mengambil {len(all_data)} data!", 85)
        return all_data

    def _calculate_stats_from_csv(self, rows: List[List[str]], header: List[str]) -> Dict:
        """
        Hitung statistik (Current/Avg/Max) dari data mentah CSV
        
        Args:
           rows: List of data rows
           header: Header row (untuk deteksi kolom)
        """
        if not rows or not header:
             return None

        # 1. Deteksi Kolom In/Out
        idx_in = -1
        idx_out = -1
        
        # Cari kolom dengan kata kunci (biasanya "Traffic - In" atau "Inbound")
        for i, col in enumerate(header):
            col_lower = col.lower()
            if "traffic_in" in col_lower or "inbound" in col_lower:
                idx_in = i
            elif "traffic_out" in col_lower or "outbound" in col_lower:
                idx_out = i
        
        # Fallback jika tidak menemukan nama spesifik (Cacti standard: 1=In, 2=Out, atau 1=In, 3=Out)
        # Ingat kolom 0 adalah Date
        if idx_in == -1 and len(header) > 1: idx_in = 1
        if idx_out == -1 and len(header) > 2: 
            # Jika kolom 2 sepertinya bukan duplicate dari In (kadang format In, In_d, Out...)
            idx_out = 2 if len(header) == 3 else 3
            if idx_out >= len(header): idx_out = -1

        in_values = []
        out_values = []
        
        for row in rows:
            try:
                # Parse In
                if idx_in != -1 and idx_in < len(row):
                    val = row[idx_in]
                    if val and val != 'NaN':
                        # Cacti CSV exports bits/sec in this setup (confirmed by user data magnitude)
                        in_values.append(float(val)) 
                
                # Parse Out
                if idx_out != -1 and idx_out < len(row):
                    val = row[idx_out]
                    if val and val != 'NaN':
                        out_values.append(float(val))
            except ValueError:
                continue
                
        # Helper format
        def fmt(val):
            if val is None: return "0.00"
            abs_val = abs(val)
            if abs_val >= 1e9:   return f"{val/1e9:.2f} G"
            elif abs_val >= 1e6: return f"{val/1e6:.2f} M"
            elif abs_val >= 1e3: return f"{val/1e3:.2f} K"
            else:                return f"{val:.2f}"

        # Calculate Stats (Current = Last, Avg = Mean, Max = Peak)
        curr_in = in_values[-1] if in_values else 0
        curr_out = out_values[-1] if out_values else 0
        
        avg_in = sum(in_values) / len(in_values) if in_values else 0
        avg_out = sum(out_values) / len(out_values) if out_values else 0
        
        max_in = max(in_values) if in_values else 0
        max_out = max(out_values) if out_values else 0
        
        return {
            "curr_in": fmt(curr_in),
            "avg_in": fmt(avg_in),
            "max_in": fmt(max_in),
            "curr_out": fmt(curr_out),
            "avg_out": fmt(avg_out),
            "max_out": fmt(max_out),
        }



def run_scraper(start_date: datetime, end_date: datetime, 
                progress_callback: Optional[Callable] = None,
                attach_to_existing: bool = False) -> List[Dict]:
    """
    Fungsi utama untuk menjalankan scraper
    
    Args:
        start_date: Tanggal mulai
        end_date: Tanggal akhir
        progress_callback: Callback untuk progress update
        attach_to_existing: Jika True, coba connect ke Chrome yang sudah berjalan
        
    Returns:
        List data yang di-scrape
    """
    scraper = CactiScraper(progress_callback)
    
    try:
        scraper.start_browser(attach_to_existing=attach_to_existing)
        scraper.navigate_to_cacti()
        data = scraper.scrape_date_range(start_date, end_date)
        return data
    finally:
        scraper.close_browser()


def start_chrome_debug_mode():
    """
    Instruksi untuk menjalankan Chrome dengan debug mode
    
    User harus jalankan command ini di Command Prompt:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222
    
    Kemudian baru bisa attach ke session tersebut
    """
    import subprocess
    import sys
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = f'"{chrome_path}" --remote-debugging-port=9222'
    
    print(f"Untuk menggunakan Chrome existing, jalankan command ini:")
    print(f"\n{cmd}\n")
    print("Kemudian buka Cacti di browser tersebut, dan jalankan program dengan opsi 'Attach to Existing'")
    
    return cmd
