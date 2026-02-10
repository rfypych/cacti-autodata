
import json
import os
import sys

def setup():
    print("\n=== Cacti Session Setup Wizard ===")
    print("Gunakan script ini jika Anda tidak memiliki Username/Password Cacti,")
    print("TAPI Anda sudah login di browser laptop Anda sekarang.")
    print("-" * 50)
    
    print("\nLangkah 1: Buka Cacti di browser Chrome/Firefox Anda yang SUDAH LOGIN.")
    print("Langkah 2: Tekan F12, pergi ke tab 'Application' (Chrome) atau 'Storage' (Firefox).")
    print("Langkah 3: Di menu kiri, pilih 'Cookies' > 'https://monitor.kabngawi.id'.")
    print("Langkah 4: Cari cookie dengan nama 'Cacti' atau 'PHPSESSID'.")
    print("Langkah 5: Klik 2x pada kolom 'Value', lalu Copy semuanya.")
    
    print("\n\n(Jika Anda bingung, nilai cookie biasanya berupa deretan huruf acak panjang seperti: n8234n2348n234...)")
    cookie_value = input("\n>> Paste VALUE cookie di sini: ").strip()
    
    if not cookie_value:
        print("\n❌ Error: Cookie tidak boleh kosong!")
        return
        
    # Konfirmasi nama cookie (default Cacti)
    cookie_name = "Cacti"
    print(f"\nDefault nama cookie adalah '{cookie_name}'.")
    choice = input("Apakah nama cookie di browser Anda berbeda? (y/n): ").lower()
    if choice == 'y':
        cookie_name = input(">> Masukkan nama cookie yang benar (contoh: PHPSESSID): ").strip()
    
    # Create simple cookie structure
    cookies = [
        {
            "domain": "monitor.kabngawi.id",
            "name": cookie_name,
            "value": cookie_value,
            "path": "/",
            "secure": False,
            "httpOnly": True
        }
    ]
    
    # Save to current directory
    filename = "cacti_cookies.json"
    try:
        with open(filename, "w") as f:
            json.dump(cookies, f, indent=2)
            
        print(f"\n✅ BERHASIL! Cookie disimpan ke '{filename}'")
        print("Sekarang coba jalankan 'python main.py' lagi.")
        print("Program akan otomatis menggunakan sesi ini.")
        
    except Exception as e:
        print(f"\n❌ Gagal menyimpan file: {e}")

if __name__ == "__main__":
    setup()
