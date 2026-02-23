import requests
import re
from datetime import datetime
from typing import Dict, List, Tuple

def parse_bandwidth_to_mbps(bw_str: str) -> float:
    """Konversi string bandwidth (ex: '4.9 G', '800 M') menjadi nilai Mbps float"""
    if not bw_str or str(bw_str).strip() == "" or str(bw_str).lower() == "nan":
        return 0.0
    
    bw_str = str(bw_str).upper().strip()
    match = re.match(r"([\d\.]+)\s*([KMG]?)", bw_str)
    if not match:
        return 0.0
        
    val = float(match.group(1))
    unit = match.group(2)
    
    if unit == 'G':
        return val * 1000.0
    elif unit == 'K':
        return val / 1000.0
    else: # M or none
        return val

def format_mbps(val: float) -> str:
    """Format float Mbps kembali ke string yang mudah dibaca (ex: 4900 -> 4.9 G)"""
    if val >= 1000:
        if val % 1000 == 0:
            return f"{int(val/1000)} G"
        return f"{val/1000:.2f} G".rstrip('0').rstrip('.')
    else:
        if val % 1 == 0:
            return f"{int(val)} M"
        return f"{val:.2f} M".rstrip('0').rstrip('.')

class GoogleFormSubmitter:
    def __init__(self, form_url: str, entry_mapping: dict):
        self.form_url = form_url
        self.entry_mapping = entry_mapping
        
    def aggregate_daily_data(self, scraped_data: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Mengubah data dari scraper (List[Dict]) menjadi agregasi harian.
        Nilai yang diambil adalah yang terbesar (MAX) dari max_out pada hari tersebut.
        """
        daily_stats = {}
        
        for row in scraped_data:
            isp_name = row.get('sheet')
            if not isp_name:
                continue
                
            date_str = row.get('date')
            if not date_str:
                continue
                
            val_mbps = parse_bandwidth_to_mbps(row.get('max_out', '0'))
            
            if date_str not in daily_stats:
                daily_stats[date_str] = {}
                
            # Simpan nilai terbesar dalam sehari untuk ISP ini
            if isp_name not in daily_stats[date_str]:
                daily_stats[date_str][isp_name] = val_mbps
            else:
                daily_stats[date_str][isp_name] = max(daily_stats[date_str][isp_name], val_mbps)
                    
        return daily_stats

    def submit_single_date(self, date_str: str, 
                           moratel_val: float, iforte_val: float, telkom_val: float,
                           dry_run: bool = False) -> Tuple[bool, str]:
        """Submit satu baris agregasi ke Google Form"""
        
        # Hitung total
        total_val = moratel_val + iforte_val + telkom_val
        
        # Format "YYYY-MM-DD" untuk form tanggal Google
        try:
            # dari excel_writer (DD/MM/YYYY) ke form (YYYY-MM-DD)
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            form_date = dt.strftime("%Y-%m-%d")
        except:
            form_date = date_str
            
        # Bentuk Payload sesuai format Google Form
        # Format nilai menggunakan format mudah dibaca, ex "4.9 G"
        # Kecuali jika Google form mensyaratkan number only, kita kirim raw 
        # (sementara ini kita asumsikan bisa kirim text)
        
        payload = {}
        
        def safe_add(key, val):
            entry_id = self.entry_mapping.get(key)
            if entry_id and entry_id != "entry.":
                payload[entry_id] = val
                
        safe_add("tanggal", form_date)
        safe_add("total", format_mbps(total_val))
        safe_add("moratel", format_mbps(moratel_val))
        safe_add("iforte", format_mbps(iforte_val))
        safe_add("telkom", format_mbps(telkom_val))
        
        # Pastikan URL mengarah ke formResponse
        submit_url = self.form_url.replace("/viewform", "/formResponse")
        
        if dry_run:
            payload_str = ", ".join(f"{k}={v}" for k, v in payload.items())
            return True, f"✅ [TEST MODE] Payload siap dikirim: {payload_str}"
            
        try:
            resp = requests.post(submit_url, data=payload, timeout=10)
            if resp.status_code in [200, 201]:
                # Google kadangkala tetap return 200 meski validasi gagal, tapi ini standar patokan.
                return True, f"Sukses ({format_mbps(total_val)})"
            else:
                return False, f"HTTP Error {resp.status_code}"
        except Exception as e:
            return False, str(e)
            
    def submit_all(self, scraped_data: List[Dict], dry_run: bool = False) -> List[Tuple[str, bool, str]]:
        """Submit seluruh data yang telah diagregasi. Return [(Tanggal, boolean_status, pesan)]"""
        daily_stats = self.aggregate_daily_data(scraped_data)
        results = []
        
        for date_str, isps in daily_stats.items():
            moratel_val = 0.0
            iforte_val = 0.0
            telkom_val = 0.0
            
            # Cocokkan nama sheet/interface dengan variabel ISP
            for k, v in isps.items():
                k_low = k.lower()
                if "moratel" in k_low: 
                    moratel_val = v
                elif "iforte" in k_low: 
                    iforte_val = v
                elif "telkom" in k_low: 
                    telkom_val = v
                    
            success, msg = self.submit_single_date(date_str, moratel_val, iforte_val, telkom_val, dry_run=dry_run)
            results.append((date_str, success, msg))
            
        return results
