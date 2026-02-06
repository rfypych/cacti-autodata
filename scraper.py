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
    
    def parse_bandwidth_value(self, text: str) -> Optional[float]:
        """
        Parse nilai bandwidth dari teks
        Contoh: "63.98 M" → 63.98, "15.79 K" → 15.79
        
        Returns:
            Nilai sebagai string dengan satuan, atau None jika gagal
        """
        if not text:
            return None
        
        # Ambil angka dan satuan
        match = re.search(r'([\d.]+)\s*([KMGTP]?)', text.strip(), re.IGNORECASE)
        if match:
            value = match.group(1)
            unit = match.group(2).upper() if match.group(2) else ""
            return f"{value} {unit}".strip()
        return text.strip()
    
    def extract_graph_data(self) -> Dict[str, Dict]:
        """
        Ekstrak data dari semua graph yang ditampilkan
        
        Returns:
            Dictionary dengan format:
            {
                "ether4-iForte": {
                    "curr_in": "63.98 M",
                    "curr_out": "25.70 M",
                    "max_in": "63.09 M",
                    "max_out": "59.62 M",
                    "avg_in": "20.81 M",
                    "avg_out": "26.33 M"
                },
                ...
            }
        """
        result = {}
        
        try:
            # Tunggu graph dimuat
            WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".graphWrapper, .rrdGraph, div[id*='graph']"))
            )
            
            # Cari semua container graph
            # Cacti biasanya menampilkan data di bawah graph
            page_source = self.driver.page_source
            
            for interface_name in config.INTERFACE_TO_SHEET.keys():
                # Cari section yang mengandung nama interface
                pattern = rf'{re.escape(interface_name)}.*?Inbound.*?Current:\s*([\d.]+\s*[KMGTP]?).*?Average:\s*([\d.]+\s*[KMGTP]?).*?Maximum:\s*([\d.]+\s*[KMGTP]?).*?Outbound.*?Current:\s*([\d.]+\s*[KMGTP]?).*?Average:\s*([\d.]+\s*[KMGTP]?).*?Maximum:\s*([\d.]+\s*[KMGTP]?)'
                
                match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
                
                if match:
                    result[interface_name] = {
                        "curr_in": self.parse_bandwidth_value(match.group(1)),
                        "avg_in": self.parse_bandwidth_value(match.group(2)),
                        "max_in": self.parse_bandwidth_value(match.group(3)),
                        "curr_out": self.parse_bandwidth_value(match.group(4)),
                        "avg_out": self.parse_bandwidth_value(match.group(5)),
                        "max_out": self.parse_bandwidth_value(match.group(6)),
                    }
                    self._update_progress(f"✓ Data {interface_name} ditemukan")
                else:
                    self._update_progress(f"✗ Data {interface_name} tidak ditemukan")
                    result[interface_name] = None
                    
        except Exception as e:
            self._update_progress(f"Error saat extract data: {str(e)}")
        
        return result
    
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
                
                # Tunggu sebentar untuk data dimuat
                time.sleep(config.ACTION_DELAY)
                
                # Ekstrak data
                graph_data = self.extract_graph_data()
                
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
