"""
Mock Cacti Server + Verification Test
Simulasi lokal Cacti untuk membuktikan akurasi scraper.

Server ini:
1. Serve CSV data persis seperti format Cacti graph_xport.php
2. Dengan nilai yang sudah DIKETAHUI (ground truth)
3. Scraper dijalankan terhadap server ini
4. Hasil scraper dibandingkan dengan ground truth

Jalankan: python demo_test.py
"""
import http.server
import threading
import json
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import math

# ==================================================
# GROUND TRUTH DATA
# ==================================================
# Data ini mensimulasikan traffic bandwidth nyata
# dengan nilai Current/Average/Maximum yang PASTI

GROUND_TRUTH = {
    # Graph ID 1503 = iForte
    "1503": {
        "title": "Router BGP Ngawi - Traffic - ether4-iForte",
        # Data points setiap 5 menit (300 detik)
        # Format: (timestamp_offset_minutes, inbound_bps, outbound_bps)
        "data_points": [
            # 00:00 - 03:00: traffic rendah (malam)
            (0, 5_000_000, 1_000_000),      # 00:00 = 5M, 1M
            (5, 4_800_000, 900_000),         # 00:05
            (10, 5_200_000, 1_100_000),      # 00:10
            (30, 4_500_000, 800_000),        # 00:30
            (60, 3_000_000, 600_000),        # 01:00
            (120, 2_500_000, 500_000),       # 02:00
            (180, 2_000_000, 400_000),       # 03:00
            
            # 04:00 - 08:00: traffic naik (pagi)
            (240, 10_000_000, 3_000_000),    # 04:00
            (300, 25_000_000, 5_000_000),    # 05:00
            (360, 40_000_000, 8_000_000),    # 06:00
            (420, 55_000_000, 12_000_000),   # 07:00
            (480, 70_000_000, 15_000_000),   # 08:00
            
            # 09:00: peak pagi
            (540, 80_000_000, 18_000_000),   # 09:00 = 80M, 18M
            
            # 10:00 - 12:00
            (600, 65_000_000, 14_000_000),   # 10:00
            (660, 60_000_000, 13_000_000),   # 11:00
            (720, 55_000_000, 11_000_000),   # 12:00
            
            # 13:00 - 15:00: siang
            (780, 50_000_000, 10_000_000),   # 13:00
            (840, 45_000_000, 9_000_000),    # 14:00
            (900, 42_000_000, 8_500_000),    # 15:00
            
            # 16:00: peak sore
            (960, 75_000_000, 16_000_000),   # 16:00 = 75M, 16M
        ]
    },
    
    # Graph ID 1573 = Telkom
    "1573": {
        "title": "Router BGP Ngawi - Traffic - ether5-Telkom",
        "data_points": [
            (0, 8_000_000, 2_000_000),
            (5, 7_500_000, 1_800_000),
            (60, 6_000_000, 1_500_000),
            (120, 5_000_000, 1_200_000),
            (180, 4_000_000, 1_000_000),
            (240, 12_000_000, 3_500_000),
            (300, 30_000_000, 7_000_000),
            (360, 45_000_000, 10_000_000),
            (420, 60_000_000, 13_000_000),
            (480, 72_000_000, 15_500_000),
            (540, 85_000_000, 19_000_000),   # 09:00 = 85M
            (600, 70_000_000, 16_000_000),
            (660, 65_000_000, 14_000_000),
            (720, 58_000_000, 12_000_000),
            (780, 52_000_000, 11_000_000),
            (840, 48_000_000, 9_500_000),
            (900, 44_000_000, 8_800_000),
            (960, 90_000_000, 20_000_000),   # 16:00 = 90M (peak!)
        ]
    },
    
    # Graph ID 1528 = Moratel
    "1528": {
        "title": "Router BGP Ngawi - Traffic - ether6-Moratel",
        "data_points": [
            (0, 3_000_000, 800_000),
            (5, 2_800_000, 750_000),
            (60, 2_500_000, 600_000),
            (120, 2_000_000, 500_000),
            (180, 1_500_000, 400_000),
            (240, 5_000_000, 1_500_000),
            (300, 15_000_000, 4_000_000),
            (360, 28_000_000, 7_000_000),
            (420, 38_000_000, 9_000_000),
            (480, 45_000_000, 11_000_000),
            (540, 50_000_000, 12_000_000),   # 09:00
            (600, 42_000_000, 10_000_000),
            (660, 40_000_000, 9_500_000),
            (720, 35_000_000, 8_000_000),
            (780, 32_000_000, 7_500_000),
            (840, 30_000_000, 7_000_000),
            (900, 28_000_000, 6_500_000),
            (960, 55_000_000, 13_000_000),   # 16:00 = 55M (peak!)
        ]
    }
}


def calculate_expected_values(graph_id, start_minutes, end_minutes):
    """Hitung nilai Current/Average/Maximum yang PASTI untuk range tertentu"""
    points = GROUND_TRUTH[graph_id]["data_points"]
    
    in_vals = []
    out_vals = []
    
    for offset_min, in_bps, out_bps in points:
        if start_minutes <= offset_min <= end_minutes:
            in_vals.append(in_bps)
            out_vals.append(out_bps)
    
    if not in_vals:
        return None
    
    def fmt(val):
        av = abs(val)
        if av >= 1e9: return f"{val/1e9:.2f} G"
        elif av >= 1e6: return f"{val/1e6:.2f} M"
        elif av >= 1e3: return f"{val/1e3:.2f} K"
        else: return f"{val:.2f}"
    
    return {
        "curr_in": fmt(in_vals[-1]),
        "avg_in": fmt(sum(in_vals)/len(in_vals)),
        "max_in": fmt(max(in_vals)),
        "curr_out": fmt(out_vals[-1]),
        "avg_out": fmt(sum(out_vals)/len(out_vals)),
        "max_out": fmt(max(out_vals)),
    }


class MockCactiHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler yang merespon persis seperti Cacti"""
    
    def log_message(self, format, *args):
        pass  # Suppress log output
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Handle graph_xport.php (CSV export)
        if 'graph_xport' in parsed.path:
            graph_id = params.get('local_graph_id', [''])[0]
            start_ts = int(params.get('graph_start', ['0'])[0])
            end_ts = int(params.get('graph_end', ['0'])[0])
            
            if graph_id in GROUND_TRUTH:
                csv_content = self._generate_csv(graph_id, start_ts, end_ts)
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv')
                self.end_headers()
                self.wfile.write(csv_content.encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        # Handle graph_view.php (main page - for connection test)
        elif 'graph_view' in parsed.path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body>Mock Cacti Server</body></html>")
        
        else:
            self.send_response(200)
            self.end_headers()
    
    def _generate_csv(self, graph_id, start_ts, end_ts):
        """Generate CSV output persis seperti Cacti graph_xport.php"""
        info = GROUND_TRUTH[graph_id]
        title = info["title"]
        
        # Base date from start_ts
        base_date = datetime.fromtimestamp(start_ts)
        
        lines = []
        lines.append(f'"Title","{title}"')
        lines.append('"Vertical Label","bits per second"')
        lines.append('')
        
        # Header - persis seperti format Cacti (5 kolom)
        # Col 0: Date
        # Col 1: CDEF_Inbound (biasanya nilai berbeda)
        # Col 2: Inbound (Named - yang benar)
        # Col 3: CDEF_Outbound
        # Col 4: Outbound (Named - yang benar)
        lines.append('"Date","CDEF_In","Inbound","CDEF_Out","Outbound"')
        
        # Data rows
        for offset_min, in_bps, out_bps in info["data_points"]:
            point_ts = start_ts + (offset_min * 60)
            
            # Only include points within the requested range
            if point_ts > end_ts:
                break
            
            point_dt = datetime.fromtimestamp(point_ts)
            date_str = point_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # CDEF values = slightly different (like real Cacti)
            cdef_in = in_bps * 1.05   # 5% higher
            cdef_out = out_bps * 1.05
            
            lines.append(f'"{date_str}",{cdef_in:.6e},{in_bps:.6e},{cdef_out:.6e},{out_bps:.6e}')
        
        return '\r\n'.join(lines)


def run_mock_server(port=18999):
    """Start mock Cacti server on localhost"""
    server = http.server.HTTPServer(('127.0.0.1', port), MockCactiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def run_verification():
    """Verifikasi bahwa scraper menghasilkan output yang akurat"""
    
    PORT = 18999
    print("=" * 70)
    print("  DEMO: VERIFIKASI AKURASI SCRAPER")
    print("  (Mock Cacti Server + Real Scraper)")
    print("=" * 70)
    
    # 1. Start mock server
    print("\n📡 Starting mock Cacti server on localhost:{}...".format(PORT))
    server = run_mock_server(PORT)
    time.sleep(0.5)
    print("   ✓ Server running!")
    
    # 2. Temporarily override config
    sys.path.insert(0, os.path.dirname(__file__))
    import config
    
    original_url = config.CACTI_URL
    original_graph_ids = config.GRAPH_IDS
    
    config.CACTI_URL = f"http://127.0.0.1:{PORT}/cacti/graph_view.php?action=tree"
    config.GRAPH_IDS = {
        "iForte": "1503",
        "Telkom": "1573",
        "Moratel": "1528",
    }
    
    # 3. Create fake cookies file (mock server doesn't need auth)
    cookies_path = os.path.join(os.path.dirname(__file__), "cacti_cookies.json")
    cookies_backup = None
    
    if os.path.exists(cookies_path):
        with open(cookies_path) as f:
            cookies_backup = f.read()
    
    with open(cookies_path, 'w') as f:
        json.dump([{"name": "test", "value": "mock", "domain": "127.0.0.1"}], f)
    
    try:
        # 4. Run scraper
        from scraper import CactiScraper
        
        def progress(msg, pct=-1):
            if "Mulai" in msg or "✓" in msg or "Selesai" in msg:
                print(f"   {msg}")
        
        scraper = CactiScraper(progress)
        
        # Test date: 2026-01-23
        test_date = datetime(2026, 1, 23)
        
        print(f"\n🔄 Scraping {test_date.strftime('%d/%m/%Y')}...")
        data = scraper.scrape_date_range_fast(test_date, test_date)
        
        print(f"\n   ✓ Got {len(data)} data points")
        
        # 5. Calculate expected values
        interfaces = {"iForte": "1503", "Telkom": "1573", "Moratel": "1528"}
        slots = [(9, 0, "09:00", 0, 540+5), (16, 0, "16:00", 0, 960+5)]  # +5 for buffer
        
        print("\n" + "=" * 70)
        print("  HASIL VERIFIKASI")
        print("=" * 70)
        
        total_checks = 0
        passed_checks = 0
        failed_details = []
        
        for hour, minute, time_str, start_min, end_min in slots:
            print(f"\n{'─'*70}")
            print(f"  ⏰ Slot {time_str} (data 00:00 → {time_str})")
            print(f"{'─'*70}")
            
            for iface, gid in interfaces.items():
                # Find scraper result
                result = None
                for d in data:
                    if d['interface'] == iface and d['time_hour'] == hour:
                        result = d
                        break
                
                # Calculate expected
                expected = calculate_expected_values(gid, start_min, end_min)
                
                if not result or not expected:
                    print(f"\n  ❌ {iface}: DATA TIDAK DITEMUKAN!")
                    failed_details.append(f"{iface} {time_str}: missing data")
                    continue
                
                print(f"\n  📊 {iface}:")
                
                fields = [
                    ("curr_in", "Current IN"),
                    ("curr_out", "Current OUT"),
                    ("avg_in", "Average IN"),
                    ("avg_out", "Average OUT"),
                    ("max_in", "Maximum IN"),
                    ("max_out", "Maximum OUT"),
                ]
                
                for field, label in fields:
                    got = result.get(field, "?")
                    exp = expected.get(field, "?")
                    match = got == exp
                    total_checks += 1
                    
                    if match:
                        passed_checks += 1
                        icon = "✅"
                    else:
                        icon = "❌"
                        failed_details.append(f"{iface} {time_str} {label}: got={got}, expected={exp}")
                    
                    print(f"     {icon} {label:15s}  scraper={got:>12s}  expected={exp:>12s}")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"  RINGKASAN: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks == total_checks:
            print(f"  🎉🎉🎉 SEMUA AKURAT! 100% MATCH! 🎉🎉🎉")
        else:
            print(f"  ⚠️  {total_checks - passed_checks} checks gagal:")
            for detail in failed_details:
                print(f"     - {detail}")
        
        print(f"{'='*70}\n")
        
    finally:
        # Restore original config
        config.CACTI_URL = original_url
        config.GRAPH_IDS = original_graph_ids
        
        # Restore original cookies
        if cookies_backup:
            with open(cookies_path, 'w') as f:
                f.write(cookies_backup)
        
        server.shutdown()


if __name__ == "__main__":
    run_verification()
