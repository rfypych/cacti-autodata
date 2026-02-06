"""
Cookie Copier - Copy login session from system Chrome to Selenium
Copies Cacti cookies from your logged-in Chrome browser
"""

import os
import shutil
import sqlite3
import json
from typing import Optional


def get_chrome_cookies_path() -> Optional[str]:
    """Get path to Chrome cookies database"""
    user_home = os.path.expanduser("~")
    
    # Windows Chrome cookie locations
    possible_paths = [
        os.path.join(user_home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cookies"),
        os.path.join(user_home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Network", "Cookies"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def copy_cookies_for_domain(domain: str, output_file: str = "cacti_cookies.json") -> bool:
    """
    Copy cookies for a specific domain from Chrome
    
    Args:
        domain: Domain to extract cookies for (e.g., "monitor.kabngawi.id")
        output_file: Output JSON file path
        
    Returns:
        True if successful, False otherwise
    """
    cookies_path = get_chrome_cookies_path()
    
    if not cookies_path:
        print("❌ Chrome cookies database tidak ditemukan!")
        print("   Pastikan Chrome terinstall dan pernah digunakan.")
        return False
    
    print(f"📁 Found cookies at: {cookies_path}")
    
    # Chrome locks the database, so we copy it first
    temp_cookies = "temp_cookies.db"
    try:
        shutil.copy2(cookies_path, temp_cookies)
    except PermissionError:
        print("❌ Tidak bisa copy cookies - Chrome sedang berjalan!")
        print("   Tutup Chrome dulu, lalu jalankan script ini lagi.")
        return False
    except Exception as e:
        print(f"❌ Error copying cookies: {e}")
        return False
    
    try:
        conn = sqlite3.connect(temp_cookies)
        cursor = conn.cursor()
        
        # Query cookies for the domain
        cursor.execute("""
            SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
            FROM cookies 
            WHERE host_key LIKE ?
        """, (f"%{domain}%",))
        
        cookies = []
        for row in cursor.fetchall():
            cookies.append({
                "name": row[0],
                "value": row[1],
                "domain": row[2],
                "path": row[3],
                "expiry": row[4],
                "secure": bool(row[5]),
                "httpOnly": bool(row[6])
            })
        
        conn.close()
        
        if cookies:
            with open(output_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"✅ {len(cookies)} cookies ditemukan untuk {domain}")
            print(f"   Disimpan ke: {output_file}")
            return True
        else:
            print(f"⚠ Tidak ada cookies untuk {domain}")
            print("   Pastikan Anda sudah login ke Cacti di Chrome.")
            return False
            
    except Exception as e:
        print(f"❌ Error reading cookies: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(temp_cookies):
            os.remove(temp_cookies)


def load_cookies_to_selenium(driver, cookies_file: str = "cacti_cookies.json") -> bool:
    """
    Load cookies from JSON file to Selenium WebDriver
    
    Args:
        driver: Selenium WebDriver instance
        cookies_file: Path to cookies JSON file
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(cookies_file):
        print(f"❌ File cookies tidak ditemukan: {cookies_file}")
        return False
    
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            # Selenium requires specific format
            selenium_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
            }
            
            # Add optional fields
            if cookie.get("secure"):
                selenium_cookie["secure"] = True
            
            try:
                driver.add_cookie(selenium_cookie)
            except Exception as e:
                # Some cookies may fail, that's okay
                pass
        
        print(f"✅ {len(cookies)} cookies dimuat ke browser")
        return True
        
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
        return False


if __name__ == "__main__":
    import config
    
    # Extract domain from Cacti URL
    from urllib.parse import urlparse
    parsed = urlparse(config.CACTI_URL)
    domain = parsed.netloc
    
    print(f"\n🍪 Cacti Cookie Copier")
    print(f"=" * 40)
    print(f"Cacti URL: {config.CACTI_URL}")
    print(f"Domain: {domain}")
    print()
    
    print("⚠️  PENTING: Tutup Chrome dulu sebelum menjalankan script ini!")
    print()
    
    input("Tekan Enter untuk melanjutkan...")
    
    success = copy_cookies_for_domain(domain)
    
    if success:
        print("\n✅ Cookies berhasil dicopy!")
        print("   Sekarang jalankan main.py, program akan otomatis pakai cookies ini.")
    else:
        print("\n❌ Gagal copy cookies. Lihat pesan error di atas.")
