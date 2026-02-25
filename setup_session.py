
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config
class SessionManager:
    def __init__(self):
        self.driver = None
        self.cookies_file = os.path.join(config.get_app_dir(), "cacti_cookies.json")

    def open_browser(self, url: str):
        """Membuka browser untuk login manual"""
        print(f"Opening browser to {url}...")
        
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        # Disable automation bars to look cleaner
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"Failed to open browser: {e}")
            return False

    def save_cookies(self):
        """Menyimpan cookies dari driver ke file json"""
        if not self.driver:
            return False, "Browser belum dibuka"
            
        try:
            cookies = self.driver.get_cookies()
            if not cookies:
                return False, "Tidak ada cookie ditemukan. Apakah Anda sudah login?"
            
            # Filter cookies standard
            formatted_cookies = []
            for c in cookies:
                formatted_cookies.append({
                    "domain": c.get("domain"),
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", False),
                    "httpOnly": c.get("httpOnly", False)
                })
                
            with open(self.cookies_file, "w") as f:
                json.dump(formatted_cookies, f, indent=2)
                
            return True, f"Berhasil menyimpan {len(cookies)} cookies ke {self.cookies_file}"
            
        except Exception as e:
            return False, str(e)

    def save_cookie_manual(self, cookie_value: str, cookie_name: str = "Cacti", domain: str = "monitor.kabngawi.id"):
        """Menyimpan cookie dari input manual string"""
        if not cookie_value:
            return False, "Value cookie kosong"
            
        try:
            cookies = [{
                "domain": domain,
                "name": cookie_name,
                "value": cookie_value,
                "path": "/",
                "secure": False,
                "httpOnly": True
            }]
            
            with open(self.cookies_file, "w") as f:
                json.dump(cookies, f, indent=2)
                
            return True, f"Berhasil menyimpan cookie ke {self.cookies_file}"
            
        except Exception as e:
            return False, str(e)

    def close_browser(self):
        """Menutup browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

def setup_standalone():
    """Fungsi standalone untuk dijalankan via CLI"""
    # Load config to get URL (optional, or ask user)
    try:
        import config
        url = config.CACTI_URL
    except:
        url = input("Masukkan URL Cacti: ").strip()
        
    manager = SessionManager()
    if manager.open_browser(url):
        print("\nBrowser telah terbuka.")
        print("Silakan LOGIN ke Cacti di browser tersebut.")
        print("Jika sudah berhasil login, kembali ke sini lalu tekan ENTER.")
        input(">> Tekan ENTER untuk menyimpan cookie...")
        
        success, msg = manager.save_cookies()
        print(f"\n{msg}")
        
        manager.close_browser()
    else:
        print("Gagal membuka browser. Pastikan Chrome terinstall.")

if __name__ == "__main__":
    setup_standalone()
