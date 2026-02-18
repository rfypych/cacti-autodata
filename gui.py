"""
GUI Module - Enhanced Version
Antarmuka grafis untuk Cacti AutoData dengan fitur lengkap:
- Settings Panel
- Preview Data
- Dry Run Mode
- Sheet Selector
- Date Picker (dengan fallback)
- Export Log
- Remember Last Settings
- Dual Language Support (ID/EN)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime, timedelta
import threading
import queue
import webbrowser
import os
from typing import Optional, Dict, List
from setup_session import SessionManager

import config
from scraper import run_scraper
from excel_writer import write_to_excel
from languages import LANGUAGES, get_text
from settings_manager import load_settings, save_settings, update_settings


class CactiAutoDataGUI:
    """GUI utama aplikasi dengan fitur lengkap"""
    
    def __init__(self):
        self.root = tk.Tk()
        
        # Load saved settings
        self.settings = load_settings()
        self.current_lang = self.settings.get("language", "id")
        
        self.root.title(get_text("app_title", self.current_lang))
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        
        # Variables
        self.start_date_var = tk.StringVar(value=self.settings.get("last_start_date") or datetime.now().strftime("%d/%m/%Y"))
        self.end_date_var = tk.StringVar(value=self.settings.get("last_end_date") or datetime.now().strftime("%d/%m/%Y"))
        self.excel_path_var = tk.StringVar(value=self.settings.get("last_excel_path", ""))
        self.status_var = tk.StringVar(value=get_text("status_waiting", self.current_lang))
        self.progress_var = tk.DoubleVar(value=0)
        
        # Mode variables
        self.dry_run_var = tk.BooleanVar(value=self.settings.get("dry_run_mode", False))
        self.skip_filled_var = tk.BooleanVar(value=self.settings.get("skip_filled_rows", True))
        
        # Sheet selection variables
        self.sheet_vars = {}
        for sheet_name, enabled in self.settings.get("selected_sheets", {}).items():
            self.sheet_vars[sheet_name] = tk.BooleanVar(value=enabled)
        
        # Data storage for preview
        self.scraped_data: List[Dict] = []
        
        self.is_running = False
        
        self._create_notebook()
    
    def _create_notebook(self):
        """Create tabbed interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tab
        self.main_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.main_frame, text="🏠 Main")
        self._create_main_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_frame, text="⚙️ Settings")
        self._create_settings_tab()
        
        # Preview tab
        self.preview_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.preview_frame, text="👁️ Preview")
        self._create_preview_tab()
    
    def _create_main_tab(self):
        """Create main tab content"""
        # ===== HEADER =====
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_row = ttk.Frame(header_frame)
        title_row.pack(fill=tk.X)
        
        self.title_label = ttk.Label(
            title_row, 
            text="🌵 Cacti AutoData",
            font=("Segoe UI", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT)
        
        # Help Button (Moved from bottom)
        self.help_btn = ttk.Button(
            title_row,
            text="❓ Help",
            width=8,
            command=self._show_help
        )
        self.help_btn.pack(side=tk.RIGHT)
        
        self.subtitle_label = ttk.Label(
            header_frame,
            text=get_text("subtitle", self.current_lang),
            font=("Segoe UI", 9)
        )
        self.subtitle_label.pack(anchor=tk.W)
        
        # ===== INPUT SECTION =====
        input_frame = ttk.LabelFrame(self.main_frame, text=get_text("input_title", self.current_lang), padding="8")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self.input_frame = input_frame
        
        input_frame.columnconfigure(1, weight=1)
        
        # Date inputs with calendar buttons
        self.start_date_label = ttk.Label(input_frame, text=get_text("start_date", self.current_lang))
        self.start_date_label.grid(row=0, column=0, sticky=tk.W, pady=3)
        
        start_date_frame = ttk.Frame(input_frame)
        start_date_frame.grid(row=0, column=1, sticky=tk.W, pady=3)
        
        self.start_entry = ttk.Entry(start_date_frame, textvariable=self.start_date_var, width=15)
        self.start_entry.pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(start_date_frame, text="📅", width=3, command=lambda: self._show_calendar("start")).pack(side=tk.LEFT)
        ttk.Label(start_date_frame, text="DD/MM/YYYY", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=5)
        
        self.end_date_label = ttk.Label(input_frame, text=get_text("end_date", self.current_lang))
        self.end_date_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        
        end_date_frame = ttk.Frame(input_frame)
        end_date_frame.grid(row=1, column=1, sticky=tk.W, pady=3)
        
        self.end_entry = ttk.Entry(end_date_frame, textvariable=self.end_date_var, width=15)
        self.end_entry.pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(end_date_frame, text="📅", width=3, command=lambda: self._show_calendar("end")).pack(side=tk.LEFT)
        ttk.Label(end_date_frame, text="DD/MM/YYYY", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=5)
        
        # Excel file
        self.excel_label = ttk.Label(input_frame, text=get_text("excel_file", self.current_lang))
        self.excel_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        
        excel_frame = ttk.Frame(input_frame)
        excel_frame.grid(row=2, column=1, sticky=tk.EW, pady=3)
        
        self.excel_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, width=45)
        self.excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 2))
        self.browse_btn = ttk.Button(excel_frame, text="Browse", command=self._browse_excel)
        self.browse_btn.pack(side=tk.LEFT)
        
        # ===== SHEET SELECTOR =====
        sheet_frame = ttk.LabelFrame(self.main_frame, text="📑 Sheet Selection", padding="8")
        sheet_frame.pack(fill=tk.X, pady=(0, 10))
        
        sheet_inner = ttk.Frame(sheet_frame)
        sheet_inner.pack(anchor=tk.W)
        
        for sheet_name in self.sheet_vars:
            cb = ttk.Checkbutton(
                sheet_inner, 
                text=sheet_name, 
                variable=self.sheet_vars[sheet_name]
            )
            cb.pack(side=tk.LEFT, padx=10)
        
        # ===== OPTIONS =====
        options_frame = ttk.LabelFrame(self.main_frame, text="🔧 Options", padding="8")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(
            options_frame, 
            text="Skip filled rows (lewati baris yang sudah terisi)", 
            variable=self.skip_filled_var
        ).pack(anchor=tk.W)
        
        ttk.Checkbutton(
            options_frame, 
            text="🧪 Dry Run Mode (preview only, tidak menulis ke Excel)", 
            variable=self.dry_run_var
        ).pack(anchor=tk.W)
        
        self.demo_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, 
            text="🎮 Demo Mode (gunakan data dummy untuk testing)", 
            variable=self.demo_mode_var
        ).pack(anchor=tk.W)
        
        # ===== PROGRESS =====
        self.progress_frame = ttk.LabelFrame(self.main_frame, text=get_text("progress_title", self.current_lang), padding="8")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.progress_frame, textvariable=self.status_var, font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        log_frame = ttk.Frame(self.progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 8), state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Save Log Button
        ttk.Button(self.progress_frame, text="💾 Save Log", command=self._save_log).pack(anchor=tk.E, pady=(2, 0))
        
        # ===== BUTTONS =====
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(
            button_frame, 
            text=get_text("btn_start", self.current_lang),
            command=self._start_process
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text=get_text("btn_stop", self.current_lang),
            command=self._stop_process,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        # Expert Log button removed (redundant with Save Log)
        
        # Help button moved to top header
        
        
        ttk.Button(
            button_frame,
            text=get_text("btn_exit", self.current_lang),
            command=self._on_close
        ).pack(side=tk.RIGHT, padx=2)
    
    def _create_settings_tab(self):
        """Create settings tab content"""
        # URL Cacti
        url_frame = ttk.LabelFrame(self.settings_frame, text="🌐 Cacti URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.url_var = tk.StringVar(value=self.settings.get("cacti_url", config.CACTI_URL))
        ttk.Entry(url_frame, textvariable=self.url_var, width=60).pack(fill=tk.X, pady=(0, 5))
        
        # Login Button
        login_frame = ttk.Frame(url_frame)
        login_frame.pack(fill=tk.X)
        
        ttk.Label(login_frame, text="Cookie expired?").pack(side=tk.LEFT)
        ttk.Button(
            login_frame, 
            text="🔑 Login / Update Session", 
            command=self._run_login_session
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            login_frame,
            text="❓ Cara ambil cookie",
            command=self._show_cookie_help
        ).pack(side=tk.LEFT)
        
        # Time Format
        time_frame = ttk.LabelFrame(self.settings_frame, text="⏰ Time Format in Excel", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.time_format_var = tk.StringVar(value=self.settings.get("time_format", "dot"))
        ttk.Radiobutton(time_frame, text="Titik (09.00, 16.00)", variable=self.time_format_var, value="dot").pack(anchor=tk.W)
        ttk.Radiobutton(time_frame, text="Titik Dua (09:00, 16:00)", variable=self.time_format_var, value="colon").pack(anchor=tk.W)
        
        # New Section: Data & Output Rules
        data_frame = ttk.LabelFrame(self.settings_frame, text="📊 Data & Output Rules", padding="10")
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.skip_weekend_var = tk.BooleanVar(value=self.settings.get("skip_weekends", config.SKIP_WEEKENDS))
        ttk.Checkbutton(data_frame, text="Skip Weekend (Sabtu & Minggu tidak diambil)", variable=self.skip_weekend_var).pack(anchor=tk.W)
        
        self.include_metadata_var = tk.BooleanVar(value=self.settings.get("include_metadata", config.INCLUDE_METADATA))
        ttk.Checkbutton(data_frame, text="Include Metadata (Sheet info tambahan di Excel)", variable=self.include_metadata_var).pack(anchor=tk.W)
        
        # Interface Mapping
        mapping_frame = ttk.LabelFrame(self.settings_frame, text="🔗 Interface → Sheet Mapping", padding="10")
        mapping_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mapping_vars = {}
        current_mapping = self.settings.get("interface_mapping", {})
        
        # Use keys from config to ensure all interfaces are shown
        for interface, default_sheet in config.INTERFACE_TO_SHEET.items():
            # Get saved sheet name or default from config
            sheet_val = current_mapping.get(interface, default_sheet)
            
            row_frame = ttk.Frame(mapping_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=f"{interface} →", width=20).pack(side=tk.LEFT)
            var = tk.StringVar(value=sheet_val)
            self.mapping_vars[interface] = var
            ttk.Entry(row_frame, textvariable=var, width=15).pack(side=tk.LEFT, padx=5)
            
        # Browser Options removed as they are not used in Fast Mode
        
        # Save/Reset buttons
        btn_frame = ttk.Frame(self.settings_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 Save Settings", command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Reset to Defaults", command=self._reset_settings).pack(side=tk.LEFT, padx=5)
    
    def _create_preview_tab(self):
        """Create preview tab content"""
        # Info
        info_label = ttk.Label(
            self.preview_frame, 
            text="Data yang akan ditulis ke Excel akan ditampilkan di sini setelah proses scraping.",
            font=("Segoe UI", 9, "italic")
        )
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Preview Notebook (Tabs per sheet)
        self.preview_notebook = ttk.Notebook(self.preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Dictionary to store treeviews: {sheet_name: treeview}
        # Dictionary to store treeviews: {sheet_name: treeview}
        self.preview_trees = {}
        
        # Initial empty tab removed per request
        # self._create_sheet_tab("Preview")
        
        # Buttons
        preview_btn_frame = ttk.Frame(self.preview_frame)
        preview_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(preview_btn_frame, text="🗑️ Clear Preview", command=self._clear_preview).pack(side=tk.LEFT, padx=5)
        self.write_btn = ttk.Button(preview_btn_frame, text="✍️ Write to Excel", command=self._write_preview_data, state=tk.DISABLED)
        self.write_btn.pack(side=tk.LEFT, padx=5)

    def _create_sheet_tab(self, sheet_name):
        """Create a new tab for a specific sheet"""
        tab_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(tab_frame, text=sheet_name)
        
        # Treeview
        columns = ("Tanggal", "Waktu", "Curr IN", "Curr OUT", "Max IN", "Max OUT", "Avg IN", "Avg OUT", "Status")
        
        tree_frame = ttk.Frame(tab_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure row tags for striping
        # Configure row tags for striping with color
        tree.tag_configure('oddrow', background='#e3f2fd')  # Light Blue
        tree.tag_configure('evenrow', background='#ffffff') # White
        
        # Style for Header
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'), background="#d1e7dd")
        
        # Configure columns
        col_widths = {
            "Tanggal": 80, "Waktu": 60, 
            "Status": 80, "Curr IN": 80, "Curr OUT": 80, 
            "Max IN": 80, "Max OUT": 80, "Avg IN": 80, "Avg OUT": 80
        }
        
        for col in columns:
            tree.heading(col, text=col)
            width = col_widths.get(col, 70)
            tree.column(col, width=width, minwidth=50, anchor="center")
            
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.preview_trees[sheet_name] = tree
        return tree
        self.write_btn.pack(side=tk.LEFT, padx=5)
    
    def _show_calendar(self, target: str):
        """Show simple date picker dialog"""
        cal_window = tk.Toplevel(self.root)
        cal_window.title("📅 Select Date")
        cal_window.geometry("300x320")
        cal_window.transient(self.root)
        cal_window.grab_set()
        
        # Get current date from entry
        try:
            if target == "start":
                current = datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
            else:
                current = datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
        except:
            current = datetime.now()
        
        # Month/Year selection
        nav_frame = ttk.Frame(cal_window, padding="10")
        nav_frame.pack(fill=tk.X)
        
        month_var = tk.IntVar(value=current.month)
        year_var = tk.IntVar(value=current.year)
        
        def update_calendar():
            # Clear existing
            for widget in days_frame.winfo_children():
                widget.destroy()
            
            # Day headers
            for i, day in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
                ttk.Label(days_frame, text=day, width=3, font=("Segoe UI", 9, "bold")).grid(row=0, column=i)
            
            # Calculate first day of month
            first_day = datetime(year_var.get(), month_var.get(), 1)
            start_weekday = first_day.weekday()
            
            # Calculate days in month
            if month_var.get() == 12:
                next_month = datetime(year_var.get() + 1, 1, 1)
            else:
                next_month = datetime(year_var.get(), month_var.get() + 1, 1)
            days_in_month = (next_month - first_day).days
            
            # Create day buttons
            row = 1
            col = start_weekday
            for day in range(1, days_in_month + 1):
                btn = ttk.Button(
                    days_frame, 
                    text=str(day), 
                    width=3,
                    command=lambda d=day: select_date(d)
                )
                btn.grid(row=row, column=col, pady=1)
                col += 1
                if col > 6:
                    col = 0
                    row += 1
        
        def prev_month():
            if month_var.get() == 1:
                month_var.set(12)
                year_var.set(year_var.get() - 1)
            else:
                month_var.set(month_var.get() - 1)
            update_calendar()
        
        def next_month():
            if month_var.get() == 12:
                month_var.set(1)
                year_var.set(year_var.get() + 1)
            else:
                month_var.set(month_var.get() + 1)
            update_calendar()
        
        def select_date(day):
            date_str = f"{day:02d}/{month_var.get():02d}/{year_var.get()}"
            if target == "start":
                self.start_date_var.set(date_str)
            else:
                self.end_date_var.set(date_str)
            cal_window.destroy()
        
        # Navigation
        ttk.Button(nav_frame, text="◀", width=3, command=prev_month).pack(side=tk.LEFT)
        
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_label = ttk.Label(nav_frame, text=f"{month_names[month_var.get()]} {year_var.get()}", font=("Segoe UI", 11, "bold"))
        month_label.pack(side=tk.LEFT, expand=True)
        
        def update_label():
            month_label.config(text=f"{month_names[month_var.get()]} {year_var.get()}")
        
        ttk.Button(nav_frame, text="▶", width=3, command=lambda: [next_month(), update_label()]).pack(side=tk.RIGHT)
        
        # Days grid
        days_frame = ttk.Frame(cal_window, padding="10")
        days_frame.pack(fill=tk.BOTH, expand=True)
        
        update_calendar()
    
    def _update_all_texts(self):
        """Update all UI text to current language"""
        lang = self.current_lang
        self.root.title(get_text("app_title", lang))
        self.subtitle_label.config(text=get_text("subtitle", lang))
        self.input_frame.config(text=get_text("input_title", lang))
        self.start_date_label.config(text=get_text("start_date", lang))
        self.end_date_label.config(text=get_text("end_date", lang))
        self.excel_label.config(text=get_text("excel_file", lang))
        self.progress_frame.config(text=get_text("progress_title", lang))
        self.start_btn.config(text=get_text("btn_start", lang))
        self.stop_btn.config(text=get_text("btn_stop", lang))
    
    def _browse_excel(self):
        """Browse for Excel file"""
        # Default to results directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(base_dir, "results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        filename = filedialog.asksaveasfilename(
            initialdir=results_dir,
            title="Save Excel File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            defaultextension=".xlsx",
            initialfile=f"Cacti_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        if filename:
            self.excel_path_var.set(filename)
    
    def _log(self, message: str):
        """Add message to log"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _update_progress(self, message: str, percentage: int = -1):
        """Update progress bar and status"""
        self.status_var.set(message)
        if percentage >= 0:
            self.progress_var.set(percentage)
        self._log(message)
        self.root.update_idletasks()
    
    def _export_log(self):
        """Export log to file"""
        log_content = self.log_text.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showwarning("Info", "Log kosong!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialname=f"cacti_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Cacti AutoData Log\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(log_content)
                messagebox.showinfo("Sukses", f"Log tersimpan ke:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan log: {e}")
    
    def _validate_inputs(self) -> bool:
        """Validate user inputs"""
        lang = self.current_lang
        
        try:
            datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", get_text("error_start_date", lang))
            return False
        
        try:
            datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", get_text("error_end_date", lang))
            return False
        
        if not self.excel_path_var.get() and not self.dry_run_var.get():
            # Auto-generate path if empty
            pass # Allowed now, will be generated in _start_process
        
        # Check at least one sheet selected
        if not any(var.get() for var in self.sheet_vars.values()):
            messagebox.showerror("Error", "Pilih minimal satu sheet!")
            return False
        
        return True
    
    def _start_process(self):
        """Start scraping process"""
        if not self._validate_inputs():
            return
        
        # Save current settings
        self._save_last_used()
        
        # Update config based on settings
        self._apply_settings_to_config()
        
        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Clear preview
        self._clear_preview()
        
        start_date = datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
        end_date = datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
        excel_path = self.excel_path_var.get()
        
        # Auto-generate filename if empty
        if not excel_path and not self.dry_run_var.get():
            base_dir = os.path.dirname(os.path.abspath(__file__))
            results_dir = os.path.join(base_dir, "results")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            filename = f"Cacti_Data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            excel_path = os.path.join(results_dir, filename)
            self.excel_path_var.set(excel_path)
            self._log(f"📁 Auto-generated file: {filename}")
        
        thread = threading.Thread(
            target=self._run_scraping_thread,
            args=(start_date, end_date, excel_path)
        )
        thread.daemon = True
        thread.start()
    
    def _apply_settings_to_config(self):
        """Apply GUI settings to config module"""
        # Time format
        if self.time_format_var.get() == "dot":
            config.TIME_FORMAT_EXCEL = "%H.%M"
        else:
            config.TIME_FORMAT_EXCEL = "%H:%M"
        
        # Skip filled rows
        config.SKIP_FILLED_ROWS = self.skip_filled_var.get()
        
        
        # Show browser - Removed
        # config.SHOW_BROWSER = self.show_browser_var.get()
        
        # Apply new settings
        config.SKIP_WEEKENDS = self.skip_weekend_var.get()
        config.INCLUDE_METADATA = self.include_metadata_var.get()
        
        # URL
        config.CACTI_URL = self.url_var.get()
        
        # Interface mapping - filter by selected sheets
        selected = {k: v for k, v in self.mapping_vars.items() if self.sheet_vars.get(v.get(), tk.BooleanVar(value=True)).get()}
        config.INTERFACE_TO_SHEET = {k: v.get() for k, v in self.mapping_vars.items()}
    
    def _run_scraping_thread(self, start_date: datetime, end_date: datetime, excel_path: str):
        """Thread for running scraping"""
        lang = self.current_lang
        is_dry_run = self.dry_run_var.get()
        is_demo_mode = self.demo_mode_var.get()
        
        try:
            mode_text = "🧪 DRY RUN MODE - " if is_dry_run else ""
            if is_demo_mode: mode_text = "🎮 DEMO MODE - "
            
            self._update_progress(f"{mode_text}Memulai proses...", 0)
            
            # Filter interfaces by selected sheets
            selected_sheets = [name for name, var in self.sheet_vars.items() if var.get()]
            
            # Scrape data 
            # Browser options removed from UI as Fast Mode calls requests directly
            data = run_scraper(
                start_date, 
                end_date, 
                self._update_progress, 
                demo_mode=is_demo_mode
            )
            
            # Filter by selected sheets (if any selected)
            if selected_sheets and data:
                filtered = [d for d in data if d.get('sheet') in selected_sheets]
                if filtered:
                    data = filtered
                else:
                    # Sheet names don't match - show all data + warning
                    available = set(d.get('sheet') for d in data)
                    self._update_progress(
                        f"⚠ Sheet filter mismatch: selected={selected_sheets}, available={available}. Menampilkan semua data."
                    )
            
            self.scraped_data = data
            
            if not data:
                self._update_progress(get_text("status_no_data", lang))
            else:
                # Populate preview (Delayed until write is done for live mode)
                if is_dry_run:
                     self.root.after(0, lambda: self._populate_preview(data, excel_path))
                
                if is_dry_run:
                    self._update_progress(f"🧪 DRY RUN: {len(data)} data siap untuk ditulis (preview only)", 100)
                    self.root.after(0, lambda: self.write_btn.configure(state=tk.NORMAL))
                    self.root.after(0, lambda: self.notebook.select(self.preview_frame))
                else:
                    # Write to Excel with Metadata (if enabled)
                    metadata = None
                    if config.INCLUDE_METADATA:
                        metadata = {
                            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Data Period": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
                            "User": os.getlogin(),
                            "Mode": "Demo / Mock" if is_demo_mode else "Live Scraping",
                            "Source URL": config.CACTI_URL,
                            "Interfaces": ", ".join(selected_sheets) if selected_sheets else "All"
                        }
                    while True:
                        try:
                            results = write_to_excel(excel_path, data, self._update_progress, metadata=metadata)
                            
                            # Jika berhasil, keluar loop
                            break
                            
                        except PermissionError:
                            self._update_progress(f"⚠️ Gagal menyimpan: File sedang dibuka. Menunggu user...", 0)
                            
                            # Thread-safe way to ask user
                            response_queue = queue.Queue()
                            
                            def ask_retry():
                                ans = messagebox.askretrycancel(
                                    "Gagal Menyimpan", 
                                    f"File Excel '{os.path.basename(excel_path)}' sedang dibuka!\n\n"
                                    "Mohon tutup file tersebut lalu klik Retry untuk menyimpan.\n"
                                    "Jika Anda klik Cancel, data hasil scraping akan HILANG."
                                )
                                response_queue.put(ans)
                            
                            self.root.after(0, ask_retry)
                            
                            # Wait for response (blocking this thread)
                            should_retry = response_queue.get()
                            
                            if not should_retry:
                                self._update_progress(f"❌ Penyimpanan dibatalkan oleh user.")
                                return # Exit thread/process
                            
                            self._update_progress(f"🔄 Mencoba menyimpan ulang...", 50)
                            # Loop continues and tries write_to_excel again

                    # Update preview with actual results (including status)
                    self.root.after(0, lambda: self._populate_preview(results, excel_path))
                    
                    self._update_progress(get_text("status_complete", lang), 100)
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        get_text("success_title", lang), 
                        f"{get_text('success_message', lang, count=len(data))}\n\nFile saved to:\n{excel_path}"
                    ))
            
        except Exception as e:
            err_msg = str(e)
            self._update_progress(f"❌ Error: {err_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", err_msg))

        except Exception as e:
            err_msg = str(e)
            self._update_progress(f"❌ Error: {err_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", err_msg))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.configure(state=tk.DISABLED))
    
    def _populate_preview(self, data: List[Dict], excel_path: str = ""):
        """Populate preview with scraped data grouped by sheet"""
        # Clear existing data in all tabs
        for tree in self.preview_trees.values():
            for item in tree.get_children():
                tree.delete(item)
        
        if not data:
            return
            
        # Group data by sheet
        # Structure: { "iForte": [row1, row2], "Telkom": [...] }
        grouped_data = {}
        for item in data:
            sheet = item.get('sheet') or item.get('interface') or 'Unknown'
            if sheet not in grouped_data:
                grouped_data[sheet] = []
            grouped_data[sheet].append(item)
            
        # Create tabs for new sheets if needed
        for sheet_name in grouped_data.keys():
            if sheet_name not in self.preview_trees:
                self._create_sheet_tab(sheet_name)
                
        # Populate each sheet
        for sheet_name, items in grouped_data.items():
            tree = self.preview_trees.get(sheet_name)
            if not tree: continue
            
            # Sort by Date then Time
            items.sort(key=lambda x: (x.get('date', datetime.min), x.get('time_hour', 0), x.get('time_minute', 0)))
            
            last_date_str = ""
            
            for i, item in enumerate(items):
                date_val = item.get('date', '')
                date_str = date_val.strftime('%d/%m/%Y') if date_val else ''
                
                # Visual Merge: If date is same as last row, make it empty
                display_date = date_str
                if date_str == last_date_str and date_str != "":
                    display_date = ""
                else:
                    last_date_str = date_str
                
                values = (
                    display_date,
                    f"{item.get('time_hour', 0):02d}.{item.get('time_minute', 0):02d}",
                    item.get('curr_in', ''),
                    item.get('curr_out', ''),
                    item.get('max_in', ''),
                    item.get('max_out', ''),
                    item.get('avg_in', ''),
                    item.get('avg_out', ''),
                    item.get('_status', 'Pending') # Use actual status or Pending
                )
                
                # Determine tag for striping
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                tree.insert("", "end", values=values, tags=(tag,))

        # Select first tab
        if grouped_data and self.preview_notebook.tabs():
            self.preview_notebook.select(0)
        
        self.write_btn.configure(state=tk.NORMAL)
    
    def _clear_preview(self):
        """Clear preview data"""
        for tree in self.preview_trees.values():
            for item in tree.get_children():
                tree.delete(item)
        self.write_btn.configure(state=tk.DISABLED)
    
    def _write_preview_data(self):
        """Write previewed data to Excel"""
        if not self.scraped_data:
            messagebox.showwarning("Info", "Tidak ada data untuk ditulis!")
            return
        
        excel_path = self.excel_path_var.get()
        if not excel_path:
            messagebox.showerror("Error", "Pilih file Excel terlebih dahulu!")
            return
        
        try:
            write_to_excel(excel_path, self.scraped_data, self._update_progress)
            messagebox.showinfo("Sukses", f"Berhasil menulis {len(self.scraped_data)} data ke Excel!\n\nFile saved to:\n{excel_path}")
            self._clear_preview()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _save_log(self):
        """Save log to file with header"""
        if not self.log_text.get(1.0, tk.END).strip():
            messagebox.showwarning("Info", "Log kosong, tidak ada yang perlu disimpan.")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            initialdir=logs_dir,
            title="Save Log File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            defaultextension=".txt",
            initialfile=filename
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Write Header
                    f.write("="*50 + "\n")
                    f.write(f"CACTI AUTODATA - EXECUTION LOG\n")
                    f.write("="*50 + "\n")
                    f.write(f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"URL         : {self.url_var.get()}\n")
                    f.write(f"Date Range  : {self.start_date_var.get()} - {self.end_date_var.get()}\n")
                    f.write(f"Demo Mode   : {'Yes' if self.demo_mode_var.get() else 'No'}\n")
                    f.write("-" * 50 + "\n\n")
                    
                    # Write Log Content
                    f.write(self.log_text.get(1.0, tk.END))
                    
                messagebox.showinfo("Sukses", f"Log berhasil disimpan ke:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan log: {e}")

    def _save_settings(self):
        """Save settings to file"""
        new_settings = {
            "cacti_url": self.url_var.get(),
            "time_format": self.time_format_var.get(),
            "interface_mapping": {k: v.get() for k, v in self.mapping_vars.items()},
            "selected_sheets": {k: v.get() for k, v in self.sheet_vars.items()},
            "skip_weekends": self.skip_weekend_var.get(),
            "include_metadata": self.include_metadata_var.get(),
            "dry_run_mode": self.dry_run_var.get(),
            "language": self.current_lang,
        }
        
        self.settings.update(new_settings)
        if save_settings(self.settings):
            messagebox.showinfo("Sukses", "Settings tersimpan!")
        else:
            messagebox.showerror("Error", "Gagal menyimpan settings!")
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Konfirmasi", "Reset semua settings ke default?"):
            from settings_manager import DEFAULT_SETTINGS, reset_settings
            reset_settings()
            self.settings = DEFAULT_SETTINGS.copy()
            messagebox.showinfo("Info", "Settings telah direset. Restart aplikasi untuk melihat perubahan.")
    
    def _save_last_used(self):
        """Save last used values"""
        update_settings({
            "last_excel_path": self.excel_path_var.get(),
            "last_start_date": self.start_date_var.get(),
            "last_end_date": self.end_date_var.get(),
            "selected_sheets": {k: v.get() for k, v in self.sheet_vars.items()},
            "skip_filled_rows": self.skip_filled_var.get(),
            "skip_weekends": self.skip_weekend_var.get(),
            "include_metadata": self.include_metadata_var.get(),
            "dry_run_mode": self.dry_run_var.get(),
        })
    
    def _stop_process(self):
        """Stop the process"""
        self.is_running = False
        self._update_progress(get_text("status_stopped", self.current_lang))
        messagebox.showwarning("Info", get_text("stop_warning", self.current_lang))
    
    def _run_login_session(self):
        """Run manual session update (Paste Cookie)"""
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "URL Cacti belum diisi!")
            return
            
        # Extract domain from URL for cleaner cookie saving
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
        except:
            domain = "monitor.kabngawi.id"

        # Show instructions
        msg = (
            "Karena login otomatis memerlukan username/password,\n"
            "metode paling aman adalah menyalin sesi dari browser Anda sendiri.\n\n"
            "Langkah-langkah:\n"
            "1. Buka Cacti di browser Chrome/Edge Anda (pastikan sudah login).\n"
            "2. Tekan F12 -> ke tab 'Application' -> 'Cookies'.\n"
            "3. Cari cookie bernama 'Cacti' atau 'PHPSESSID'.\n"
            "4. Copy isinya (deretan huruf acak panjang).\n\n"
            "Klik OK untuk menempelkan (Paste) cookie tersebut."
        )
        
        if messagebox.askokcancel("Update Sesi Manual", msg):
            cookie_value = simpledialog.askstring(
                "Input Cookie", 
                "Paste Value Cookie di sini:",
                parent=self.root
            )
            
            if cookie_value:
                manager = SessionManager()
                success, result_msg = manager.save_cookie_manual(
                    cookie_value.strip(), 
                    domain=domain
                )
                
                if success:
                    messagebox.showinfo("Sukses", "Sesi berhasil disimpan!\nSilakan coba scraping lagi.")
                else:
                    messagebox.showerror("Gagal", f"Gagal menyimpan sesi:\n{result_msg}")

    def _show_cookie_help(self):
        """Show guide for getting cookies"""
        msg = (
            "LANGKAH-LANGKAH MENDAPATKAN COOKIE:\n\n"
            "1. Buka Cacti di browser (Chrome/Edge/Firefox) dan pastikan sudah LOGIN.\n"
            "2. Tekan tombol F12 pada keyboard untuk membuka Developer Tools.\n"
            "3. Cari tab bernama 'Application' (di Chrome/Edge) atau 'Storage' (di Firefox).\n"
            "   (Jika tidak terlihat, klik tanda panah '>>' di menu atas DevTools)\n"
            "4. Di menu kiri, buka bagian 'Cookies' lalu klik URL Cacti.\n"
            "5. Cari cookie dengan nama 'Cacti' atau 'PHPSESSID'.\n"
            "6. Klik 2x pada kolom 'Value' cookie tersebut, lalu Copy (Ctrl+C).\n"
            "7. Kembali ke aplikasi ini, klik 'Login / Update Session', lalu Paste (Ctrl+V).\n"
        )
        messagebox.showinfo("Cara Ambil Cookie", msg)

    def _show_help(self):
        """Show improved help window with multiple sections"""
        lang = self.current_lang
        
        help_window = tk.Toplevel(self.root)
        help_window.title(get_text("help_title", lang))
        help_window.geometry("600x550")
        help_window.resizable(False, False)
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Main container with scrollbar
        main_container = ttk.Frame(help_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ===== HEADER =====
        ttk.Label(
            scrollable_frame,
            text="🌵 Cacti AutoData Help",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # ===== BASIC STEPS =====
        basic_frame = ttk.LabelFrame(scrollable_frame, text=get_text("help_basic_title", lang), padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ===== CONTENT =====
        help_text = """
1. **Pilih Tanggal**: Tentukan rentang tanggal data yang ingin diambil.
2. **Pilih URL**: Pastikan URL Cacti sudah benar (default biasanya sudah oke).
3. **Setting Sheet**: Masuk ke tab 'Settings', pastikan setiap Interface sudah dipetakan ke nama Sheet Excel yang sesuai.
4. **Mulai**: Klik tombol 'Start Scraping'.
5. **Login**: Jendela browser akan muncul. Silakan login ke Cacti secara manual.
6. **Tunggu**: Setelah login, biarkan aplikasi bekerja sendiri. Jangan tutup browsernya!
7. **Selesai**: File Excel akan otomatis tersimpan di folder 'results'.

FITUR-FITUR:
----------------
• **Auto-Resume**: Jika koneksi putus, aplikasi akan mencoba lanjut dari titik terakhir.
• **Demo Mode**: Gunakan untuk latihan/testing tanpa koneksi Cacti.
• **Tabbed Preview**: Lihat data per sheet sebelum disimpan.
• **Save Log**: Simpan riwayat eksekusi untuk laporan atau troubleshooting.
• **Excel Metadata**: File output memiliki sheet 'Metadata' berisi info eksekusi.

TROUBLESHOOTING:
----------------
Q: Browser tidak muncul?
A: Pastikan Chrome sudah terinstall. Coba mode 'Show Browser' di settings.

Q: Data di Excel kosong/salah?
A: Cek tab 'Settings', pastikan mapping Interface ke Sheet sudah benar.

Q: Error "Element not found"?
A: Mungkin internet lambat atau struktur web Cacti berubah. Coba lagi dengan koneksi stabil.

Q: Tombol Start tidak bisa diklik?
A: Pastikan tanggal sudah diisi dengan format DD/MM/YYYY.

TIPS:
----------------
- Gunakan fitur 'Demo Mode' untuk melihat bagaimana hasil akhir Excel akan terlihat.
- Selalu cek 'Preview' sebelum file benar-benar disimpan jika Anda ragu.
"""
        
        text_widget = tk.Text(scrollable_frame, wrap=tk.WORD, font=("Segoe UI", 10), bg="#f0f0f0", relief=tk.FLAT, height=25)
        text_widget.insert(tk.END, help_text)
        text_widget.configure(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        # Creator Frame (Footer)
        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(20, 10))
        
        creator_frame = ttk.Frame(scrollable_frame)
        creator_frame.pack(fill=tk.X)
        
        ttk.Label(
            creator_frame,
            text=get_text("help_creator", lang),
            font=("Segoe UI", 9, "italic")
        ).pack()
        
        ttk.Label(
            creator_frame,
            text="v2.0 - Enhanced Edition",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack()
    
    def _on_close(self):
        """Handle window close"""
        self._save_last_used()
        self.root.quit()
    
    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()


def main():
    """Entry point"""
    app = CactiAutoDataGUI()
    app.run()


if __name__ == "__main__":
    main()
