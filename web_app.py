"""
Cacti AutoData - Web Dashboard
Modern web interface with full feature parity to tkinter GUI.

Usage:
    python web_app.py

Then open http://localhost:5000 in your browser.
"""

import os
import sys
import json
import time
import re
import threading
import queue
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from flask import Flask, render_template, request, jsonify, Response, send_from_directory

# Import existing modules
import config
from scraper import run_scraper, CactiScraper
from excel_writer import write_to_excel
from settings_manager import load_settings, save_settings, update_settings, DEFAULT_SETTINGS
from form_submitter import GoogleFormSubmitter, parse_bandwidth_to_mbps, format_mbps

app = Flask(__name__,
            template_folder=os.path.join(config.get_resource_dir(), 'templates'),
            static_folder=os.path.join(config.get_resource_dir(), 'static'))

# ============================================================
# SHARED STATE (thread-safe)
# ============================================================
class AppState:
    """Thread-safe shared state for scraping process."""
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.progress = 0
        self.status = "Menunggu..."
        self.logs: List[str] = []
        self.scraped_data: List[Dict] = []
        self.log_queue = queue.Queue()
        self._stop_requested = False

        # Upload Form state
        self.form_running = False
        self.form_scraped_data: List[Dict] = []
        self.form_aggregated: Dict = {}
        self.form_logs: List[str] = []
        self.form_log_queue = queue.Queue()

    def reset(self):
        with self.lock:
            self.is_running = False
            self.progress = 0
            self.status = "Menunggu..."
            self.logs = []
            self.scraped_data = []
            self._stop_requested = False

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        with self.lock:
            self.logs.append(entry)
        self.log_queue.put(entry)

    def update_progress(self, message: str, percentage: int = -1):
        with self.lock:
            self.status = message
            if percentage >= 0:
                self.progress = percentage
        self.add_log(message)

    def get_state(self):
        with self.lock:
            return {
                "is_running": self.is_running,
                "progress": self.progress,
                "status": self.status,
                "log_count": len(self.logs),
            }

    def request_stop(self):
        with self.lock:
            self._stop_requested = True

    def should_stop(self):
        with self.lock:
            return self._stop_requested

    # Form-specific log
    def add_form_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        with self.lock:
            self.form_logs.append(entry)
        self.form_log_queue.put(entry)


state = AppState()

# ============================================================
# ROUTES - Pages
# ============================================================
# ============================================================
# INITIALIZATION: Apply saved settings to config
# ============================================================
def init_config_from_settings():
    settings = load_settings()
    if "cacti_url" in settings:
        config.CACTI_URL = settings["cacti_url"]
    if "skip_weekends" in settings:
        config.SKIP_WEEKENDS = settings["skip_weekends"]
    if "skip_holidays" in settings:
        config.SKIP_HOLIDAYS = settings["skip_holidays"]
    if "skip_filled_rows" in settings:
        config.SKIP_FILLED_ROWS = settings["skip_filled_rows"]
    if "include_metadata" in settings:
        config.INCLUDE_METADATA = settings["include_metadata"]
    if "time_format" in settings:
        fmt = settings["time_format"]
        config.TIME_FORMAT_EXCEL = "%H.%M" if fmt == "dot" else "%H:%M"
    if "interface_mapping" in settings:
        config.INTERFACE_TO_SHEET = settings["interface_mapping"]
    if "google_form_url" in settings:
        config.GOOGLE_FORM_URL = settings["google_form_url"]
    if "google_form_entries" in settings:
        config.GOOGLE_FORM_ENTRIES = settings["google_form_entries"]

init_config_from_settings()

@app.route('/')
def index():
    return render_template('dashboard.html')

# ============================================================
# ROUTES - Config & Settings
# ============================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Return current active configuration."""
    return jsonify({
        "cacti_url": config.CACTI_URL,
        "interfaces": config.INTERFACE_TO_SHEET,
        "graph_ids": getattr(config, 'GRAPH_IDS', {}),
        "time_slots": config.TIME_SLOTS,
        "skip_weekends": config.SKIP_WEEKENDS,
        "skip_holidays": getattr(config, 'SKIP_HOLIDAYS', False),
        "skip_filled_rows": getattr(config, 'SKIP_FILLED_ROWS', True),
        "include_metadata": getattr(config, 'INCLUDE_METADATA', True),
        "time_format": config.TIME_FORMAT_EXCEL,
        "date_format": config.DATE_FORMAT_EXCEL,
        "google_form_url": getattr(config, 'GOOGLE_FORM_URL', ''),
        "google_form_entries": getattr(config, 'GOOGLE_FORM_ENTRIES', {}),
    })


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Return saved user settings."""
    settings = load_settings()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def save_settings_api():
    """Save user settings."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Apply to config module in-memory
    if "cacti_url" in data:
        config.CACTI_URL = data["cacti_url"]
    if "skip_weekends" in data:
        config.SKIP_WEEKENDS = data["skip_weekends"]
    if "skip_holidays" in data:
        config.SKIP_HOLIDAYS = data["skip_holidays"]
    if "skip_filled_rows" in data:
        config.SKIP_FILLED_ROWS = data["skip_filled_rows"]
    if "include_metadata" in data:
        config.INCLUDE_METADATA = data["include_metadata"]
    if "time_format" in data:
        fmt = data["time_format"]
        config.TIME_FORMAT_EXCEL = "%H.%M" if fmt == "dot" else "%H:%M"
    if "interface_mapping" in data:
        config.INTERFACE_TO_SHEET = data["interface_mapping"]
    
    # Standardize selected_sheets if provided as list from frontend
    if "selected_sheets" in data and isinstance(data["selected_sheets"], list):
        # Convert list ["Sheet1", "Sheet2"] -> dict {"Sheet1": True, "Sheet2": True}
        # We also need to keep track of sheets NOT in the list as False if they were previously there
        current_settings = load_settings()
        old_selected = current_settings.get("selected_sheets", {})
        new_selected = {k: False for k in old_selected.keys()} # Reset all to False
        for s in data["selected_sheets"]:
            new_selected[s] = True
        data["selected_sheets"] = new_selected
        
    # Handle Google Form fields
    if "google_form_url" in data:
        config.GOOGLE_FORM_URL = data["google_form_url"]
    if "google_form_entries" in data:
        config.GOOGLE_FORM_ENTRIES = data["google_form_entries"]

    # Save to file
    success = update_settings(data)
    return jsonify({"success": success})


@app.route('/api/session/cookie', methods=['POST'])
def update_cookie():
    """Update Cacti session cookie."""
    data = request.get_json()
    cookie_value = data.get("cookie_value", "").strip()
    cookie_name = data.get("cookie_name", "Cacti")

    if not cookie_value:
        return jsonify({"error": "Cookie value kosong!"}), 400

    from urllib.parse import urlparse
    try:
        domain = urlparse(config.CACTI_URL).netloc
    except:
        domain = "monitor.kabngawi.id"

    from setup_session import SessionManager
    manager = SessionManager()
    success, msg = manager.save_cookie_manual(cookie_value, cookie_name=cookie_name, domain=domain)

    return jsonify({"success": success, "message": msg})


@app.route('/api/session/status', methods=['GET'])
def session_status():
    """Check if a valid cookie file exists."""
    cookie_file = os.path.join(config.get_app_dir(), 'cacti_cookies.json')
    exists = os.path.exists(cookie_file)
    age = None
    if exists:
        mtime = os.path.getmtime(cookie_file)
        age = int(time.time() - mtime)
    return jsonify({"exists": exists, "age_seconds": age})


@app.route('/api/utils/browse-file', methods=['POST'])
def browse_file():
    """Trigger a native OS file dialog to select/save an Excel file."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.wm_attributes("-topmost", 1)  # Bring to front
        
        data = request.get_json() or {}
        mode = data.get("mode", "save") # "save" or "open"
        initial_dir = data.get("initial_dir", os.path.join(config.get_app_dir(), "result"))
        
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)
            
        if mode == "save":
            filename = filedialog.asksaveasfilename(
                parent=root,
                initialdir=initial_dir,
                title="Simpan File Excel",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                defaultextension=".xlsx",
                initialfile=f"Cacti_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
        else:
            filename = filedialog.askopenfilename(
                parent=root,
                initialdir=initial_dir,
                title="Pilih File Excel",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
        root.destroy()
        
        if filename:
            return jsonify({"success": True, "path": filename})
        return jsonify({"success": False, "message": "Dibatalkan oleh user"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTES - Scraping (Excel Mode)
# ============================================================

@app.route('/api/scrape/start', methods=['POST'])
def start_scrape():
    """Start scraping process in background thread."""
    if state.is_running:
        return jsonify({"error": "Scraping sudah berjalan!"}), 409

    data = request.get_json()
    try:
        start_date = datetime.strptime(data.get("start_date", ""), "%d/%m/%Y")
        end_date = datetime.strptime(data.get("end_date", ""), "%d/%m/%Y")
    except ValueError:
        return jsonify({"error": "Format tanggal salah! Gunakan DD/MM/YYYY"}), 400

    if start_date > end_date:
        return jsonify({"error": "Tanggal akhir harus >= tanggal mulai!"}), 400

    excel_path = data.get("excel_path", "")
    is_dry_run = data.get("dry_run", False)
    is_demo_mode = data.get("demo_mode", False)
    selected_sheets = data.get("selected_sheets", [])

    # Auto-generate filename if empty and not dry run
    if not excel_path and not is_dry_run:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(base_dir, "result")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        filename = f"Cacti_Data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
        excel_path = os.path.join(results_dir, filename)

    # Apply settings to config before scraping
    if data.get("skip_weekends") is not None:
        config.SKIP_WEEKENDS = data["skip_weekends"]
    if data.get("skip_holidays") is not None:
        config.SKIP_HOLIDAYS = data["skip_holidays"]
    if data.get("skip_filled_rows") is not None:
        config.SKIP_FILLED_ROWS = data["skip_filled_rows"]
    if data.get("include_metadata") is not None:
        config.INCLUDE_METADATA = data["include_metadata"]

    # Persist last used values to settings_manager (EXE readiness)
    update_settings({
        "last_excel_path": excel_path,
        "last_start_date": start_date.strftime("%d/%m/%Y"),
        "last_end_date": end_date.strftime("%d/%m/%Y"),
        "selected_sheets": {s: True for s in selected_sheets} # Standardize to dict
    })

    state.reset()
    state.is_running = True

    thread = threading.Thread(
        target=_scraping_worker,
        args=(start_date, end_date, excel_path, is_dry_run, is_demo_mode, selected_sheets),
        daemon=True
    )
    thread.start()

    return jsonify({
        "success": True,
        "message": "Scraping dimulai!",
        "excel_path": excel_path
    })


@app.route('/api/scrape/status', methods=['GET'])
def scrape_status():
    """Get current scraping status."""
    s = state.get_state()
    return jsonify(s)


@app.route('/api/scrape/stop', methods=['POST'])
def stop_scrape():
    """Request scraping to stop."""
    state.request_stop()
    state.update_progress("⏹️ Penghentian diminta...", -1)
    return jsonify({"success": True})


@app.route('/api/scrape/logs', methods=['GET'])
def get_logs():
    """SSE endpoint for real-time log streaming."""
    def event_stream():
        while True:
            try:
                message = state.log_queue.get(timeout=30)
                yield f"data: {json.dumps({'log': message, **state.get_state()})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'heartbeat': True, **state.get_state()})}\n\n"

            if not state.is_running and state.log_queue.empty():
                yield f"data: {json.dumps({'done': True, **state.get_state()})}\n\n"
                break

    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/preview', methods=['GET'])
def get_preview():
    """Return scraped data for preview."""
    with state.lock:
        data = state.scraped_data

    grouped = {}
    for item in data:
        sheet = item.get('sheet') or item.get('interface') or 'Unknown'
        if sheet not in grouped:
            grouped[sheet] = []

        row = {
            "date": item['date'].strftime('%d/%m/%Y') if isinstance(item.get('date'), datetime) else str(item.get('date', '')),
            "time": f"{item.get('time_hour', 0):02d}.{item.get('time_minute', 0):02d}",
            "curr_in": item.get('curr_in', ''),
            "curr_out": item.get('curr_out', ''),
            "max_in": item.get('max_in', ''),
            "max_out": item.get('max_out', ''),
            "avg_in": item.get('avg_in', ''),
            "avg_out": item.get('avg_out', ''),
            "status": item.get('_status', 'Pending'),
        }
        grouped[sheet].append(row)

    return jsonify({"sheets": grouped, "total": len(data)})


@app.route('/api/excel/write', methods=['POST'])
def write_excel():
    """Write previewed data to Excel."""
    data = request.get_json()
    excel_path = data.get("excel_path", "")

    if not excel_path:
        return jsonify({"error": "Path file Excel belum ditentukan!"}), 400

    with state.lock:
        scraped = state.scraped_data

    if not scraped:
        return jsonify({"error": "Tidak ada data untuk ditulis!"}), 400

    try:
        metadata = None
        if getattr(config, 'INCLUDE_METADATA', True):
            metadata = {
                "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Source": "Web Dashboard",
                "URL": config.CACTI_URL,
            }

        results = write_to_excel(excel_path, scraped,
                                 progress_callback=lambda msg, pct: state.update_progress(msg, pct),
                                 metadata=metadata)

        with state.lock:
            state.scraped_data = results

        return jsonify({
            "success": True,
            "message": f"Berhasil menulis {len(results)} data ke Excel!",
            "path": excel_path
        })
    except PermissionError:
        return jsonify({
            "error": f"File '{os.path.basename(excel_path)}' sedang dibuka! Tutup file lalu coba lagi."
        }), 423
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs/download', methods=['GET'])
def download_log():
    """Download all current logs as a text file."""
    with state.lock:
        log_entries = list(state.logs)

    content = "=" * 50 + "\n"
    content += "CACTI AUTODATA - WEB DASHBOARD LOG\n"
    content += "=" * 50 + "\n"
    content += f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"URL: {config.CACTI_URL}\n"
    content += "-" * 50 + "\n\n"
    content += "\n".join(log_entries)

    return Response(
        content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=cacti_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        }
    )

# ============================================================
# ROUTES - Upload Form (Google Form)
# ============================================================

@app.route('/api/form/detect-ids', methods=['POST'])
def detect_form_ids():
    """Auto-detect entry IDs from a Google Form URL."""
    data = request.get_json()
    url = data.get("url", "")

    if not url or "docs.google.com/forms" not in url:
        return jsonify({"error": "URL Google Form tidak valid!"}), 400

    try:
        import requests as req
        resp = req.get(url, timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": f"HTTP Error {resp.status_code}"}), 502

        html = resp.text
        found_mapping = {}

        # Try structured FB_PUBLIC_LOAD_DATA_ first
        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);\s*</script>', html, re.DOTALL)
        if match:
            fb_data = json.loads(match.group(1))
            fields = fb_data[1][1] if len(fb_data) > 1 else []
            for f in fields:
                try:
                    label = str(f[1]).lower()
                    entry_id = f[4][0][0]

                    target_key = None
                    if "tanggal" in label or "date" in label:
                        target_key = "tanggal"
                    elif "total" in label:
                        target_key = "total"
                    elif "moratel" in label:
                        target_key = "moratel"
                    elif "iforte" in label:
                        target_key = "iforte"
                    elif "telkom" in label:
                        target_key = "telkom"

                    if target_key:
                        found_mapping[target_key] = f"entry.{entry_id}"
                except:
                    pass

        if found_mapping:
            return jsonify({"success": True, "mapping": found_mapping, "method": "auto"})

        # Fallback: brute-force extract all entry IDs
        entries = list(set(re.findall(r'entry\.(\d+)', html)))
        if entries:
            return jsonify({
                "success": True,
                "mapping": {},
                "raw_entries": [f"entry.{e}" for e in entries],
                "method": "semi-auto"
            })

        return jsonify({"error": "Tidak dapat menemukan ID form."}), 404

    except Exception as e:
        return jsonify({"error": f"Gagal fetch form: {str(e)}"}), 500


@app.route('/api/form/scrape-peak', methods=['POST'])
def scrape_form_peak():
    """Scrape 24-hour daily peak data for Google Form upload."""
    if state.form_running:
        return jsonify({"error": "Proses scraping form sudah berjalan!"}), 409

    data = request.get_json()
    try:
        start_date = datetime.strptime(data.get("start_date", ""), "%d/%m/%Y")
        end_date = datetime.strptime(data.get("end_date", ""), "%d/%m/%Y")
    except ValueError:
        return jsonify({"error": "Format tanggal salah! Gunakan DD/MM/YYYY"}), 400

    if start_date > end_date:
        return jsonify({"error": "Tanggal akhir harus >= tanggal mulai!"}), 400

    is_demo_mode = data.get("demo_mode", False)

    state.form_running = True
    state.form_scraped_data = []
    state.form_aggregated = {}
    state.form_logs = []

    thread = threading.Thread(
        target=_form_scrape_worker,
        args=(start_date, end_date, is_demo_mode),
        daemon=True
    )
    thread.start()

    return jsonify({"success": True, "message": "Scraping 24-jam dimulai..."})


@app.route('/api/form/scrape-status', methods=['GET'])
def form_scrape_status():
    """Get form scraping status."""
    return jsonify({
        "running": state.form_running,
        "has_data": len(state.form_aggregated) > 0,
    })


@app.route('/api/form/scrape-logs', methods=['GET'])
def form_scrape_logs():
    """SSE endpoint for form scraping logs."""
    def event_stream():
        while True:
            try:
                message = state.form_log_queue.get(timeout=30)
                yield f"data: {json.dumps({'log': message, 'running': state.form_running})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'heartbeat': True, 'running': state.form_running})}\n\n"

            if not state.form_running and state.form_log_queue.empty():
                yield f"data: {json.dumps({'done': True, 'running': False})}\n\n"
                break

    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/form/preview', methods=['GET'])
def get_form_preview():
    """Return aggregated daily peak data for form preview."""
    aggregated = state.form_aggregated
    rows = []
    for date_str, isps in aggregated.items():
        moratel_val = 0.0
        iforte_val = 0.0
        telkom_val = 0.0

        for k, v in isps.items():
            k_low = k.lower()
            if "moratel" in k_low:
                moratel_val = v
            elif "iforte" in k_low:
                iforte_val = v
            elif "telkom" in k_low:
                telkom_val = v

        total_val = moratel_val + iforte_val + telkom_val

        rows.append({
            "date": date_str,
            "total": format_mbps(total_val),
            "moratel": format_mbps(moratel_val),
            "iforte": format_mbps(iforte_val),
            "telkom": format_mbps(telkom_val),
            "checked": True,
        })

    return jsonify({"rows": rows, "total": len(rows)})


@app.route('/api/form/upload', methods=['POST'])
def upload_to_form():
    """Upload data to Google Form."""
    data = request.get_json()
    form_url = data.get("form_url", "")
    entry_mapping = data.get("entry_mapping", {})
    checked_dates = data.get("checked_dates", [])
    is_dry_run = data.get("dry_run", False)

    if not form_url:
        return jsonify({"error": "URL Google Form belum diisi!"}), 400

    if not state.form_scraped_data:
        return jsonify({"error": "Belum ada data! Jalankan 'Tarik Data' terlebih dahulu."}), 400

    if state.form_running:
        return jsonify({"error": "Proses form sedang berjalan!"}), 409

    state.form_running = True

    thread = threading.Thread(
        target=_form_upload_worker,
        args=(form_url, entry_mapping, checked_dates, is_dry_run),
        daemon=True
    )
    thread.start()

    return jsonify({
        "success": True,
        "message": "Proses upload dimulai..."
    })


# ============================================================
# BACKGROUND WORKERS
# ============================================================

def _scraping_worker(start_date, end_date, excel_path, is_dry_run, is_demo_mode, selected_sheets):
    """Background worker for Excel scraping."""
    try:
        mode_text = ""
        if is_dry_run:
            mode_text = "🧪 DRY RUN - "
        if is_demo_mode:
            mode_text = "🎮 DEMO MODE - "

        state.update_progress(f"{mode_text}Memulai proses...", 0)

        data = run_scraper(
            start_date,
            end_date,
            progress_callback=state.update_progress,
            demo_mode=is_demo_mode
        )

        # Filter by selected sheets
        if selected_sheets and data:
            filtered = [d for d in data if d.get('sheet') in selected_sheets]
            if filtered:
                data = filtered

        with state.lock:
            state.scraped_data = data

        if not data:
            state.update_progress("⚠️ Tidak ada data yang berhasil diambil!", 100)
        elif is_dry_run:
            state.update_progress(f"🧪 DRY RUN selesai: {len(data)} data siap di Preview", 100)
        else:
            state.update_progress("📝 Menulis data ke Excel...", 90)
            try:
                metadata = None
                if getattr(config, 'INCLUDE_METADATA', True):
                    metadata = {
                        "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Data Period": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
                        "Mode": "Demo" if is_demo_mode else "Live",
                        "Source URL": config.CACTI_URL,
                        "Source": "Web Dashboard",
                        "Interfaces": ", ".join(selected_sheets) if selected_sheets else "All"
                    }

                results = write_to_excel(excel_path, data,
                                         progress_callback=state.update_progress,
                                         metadata=metadata)

                with state.lock:
                    state.scraped_data = results

                state.update_progress(f"✅ Selesai! {len(results)} data → {os.path.basename(excel_path)}", 100)
            except PermissionError:
                state.update_progress("⚠️ File Excel dibuka! Gunakan tombol 'Write to Excel' di Preview.", 95)
            except Exception as e:
                state.update_progress(f"❌ Error Excel: {str(e)}", 95)

    except Exception as e:
        state.update_progress(f"❌ Error: {str(e)}", 0)

    finally:
        with state.lock:
            state.is_running = False


def _form_scrape_worker(start_date, end_date, demo_mode=False):
    """Background worker for 24-hour peak scraping (for Google Form)."""
    try:
        mode_text = " 🎮 DEMO MODE" if demo_mode else ""
        state.add_form_log(f"========= MULAI PREVIEW 24-JAM{mode_text} =========")

        scraper = CactiScraper(
            progress_callback=lambda msg, pct: state.add_form_log(msg)
        )

        dates_to_scrape = []
        curr = start_date
        while curr <= end_date:
            dates_to_scrape.append(curr.strftime("%d/%m/%Y"))
            curr += timedelta(days=1)

        state.add_form_log(f"Menarik data 24-Jam untuk {len(dates_to_scrape)} hari...")

        raw_data = scraper.scrape_daily_peak_for_form(dates_to_scrape, demo_mode=demo_mode)

        dummy_submitter = GoogleFormSubmitter("", {})
        aggregated = dummy_submitter.aggregate_daily_data(raw_data)

        with state.lock:
            state.form_scraped_data = raw_data
            state.form_aggregated = aggregated

        state.add_form_log(f"✅ Preview siap: {len(aggregated)} hari data teragregasi.")

    except Exception as e:
        state.add_form_log(f"❌ Error: {str(e)}")

    finally:
        state.form_running = False


def _form_upload_worker(form_url, entry_mapping, checked_dates, is_dry_run):
    """Background worker for uploading data to Google Form."""
    try:
        submitter = GoogleFormSubmitter(form_url, entry_mapping)

        # Filter by checked dates
        filtered_data = [d for d in state.form_scraped_data
                         if d.get('date') in checked_dates] if checked_dates else state.form_scraped_data

        results = []
        def on_progress(date_str, success, msg):
            results.append({"date": date_str, "success": success, "message": msg})
            state.add_form_log(f"{'✅' if success else '❌'} {date_str}: {msg}")

        submitter.submit_all(filtered_data, dry_run=is_dry_run, progress_callback=on_progress)

        success_count = sum(1 for r in results if r["success"])
        state.add_form_log(f"========= {success_count}/{len(results)} berhasil diupload =========")

    except Exception as e:
        state.add_form_log(f"❌ Error upload: {str(e)}")

    finally:
        state.form_running = False


@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """Endpoint for gracefully shutting down the web server executable."""
    # Run shutdown in a background thread to allow this request to complete
    def delayed_exit():
        import time
        time.sleep(1)
        import os
        os._exit(0)
    
    threading.Thread(target=delayed_exit, daemon=True).start()
    return jsonify({"success": True, "message": "Server is shutting down..."})

# ============================================================
# ENTRY POINT
# ============================================================

def run_server(port=8181):
    """Start the Flask server on the specified port"""
    print("=" * 50)
    print("🌵 Cacti AutoData - Web Dashboard")
    print("=" * 50)
    print(f"Buka browser: http://localhost:{port}")
    print("Ctrl+C untuk menghentikan server")
    print("=" * 50)
    app.run(debug=True, port=port, host='0.0.0.0', use_reloader=False)

if __name__ == '__main__':
    # When run directly, get port from settings or fallback to default
    settings = load_settings()
    port = settings.get("web_port", 8181)
    run_server(port=port)
