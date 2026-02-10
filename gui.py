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
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import threading
import os
from typing import Optional, Dict, List

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
        
        # Language switcher
        self.lang_btn = ttk.Button(
            title_row,
            text="🌐 EN" if self.current_lang == "id" else "🌐 ID",
            width=8,
            command=self._toggle_language
        )
        self.lang_btn.pack(side=tk.RIGHT)
        
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
        
        ttk.Button(
            button_frame,
            text="💾 Export Log",
            command=self._export_log
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text=get_text("btn_help", self.current_lang),
            command=self._show_help
        ).pack(side=tk.LEFT, padx=2)
        
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
        ttk.Entry(url_frame, textvariable=self.url_var, width=60).pack(fill=tk.X)
        
        # Time Format
        time_frame = ttk.LabelFrame(self.settings_frame, text="⏰ Time Format in Excel", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.time_format_var = tk.StringVar(value=self.settings.get("time_format", "dot"))
        ttk.Radiobutton(time_frame, text="Titik (09.00, 16.00)", variable=self.time_format_var, value="dot").pack(anchor=tk.W)
        ttk.Radiobutton(time_frame, text="Titik Dua (09:00, 16:00)", variable=self.time_format_var, value="colon").pack(anchor=tk.W)
        
        # Interface Mapping
        mapping_frame = ttk.LabelFrame(self.settings_frame, text="🔗 Interface → Sheet Mapping", padding="10")
        mapping_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mapping_vars = {}
        current_mapping = self.settings.get("interface_mapping", config.INTERFACE_TO_SHEET)
        
        for i, (interface, sheet) in enumerate(current_mapping.items()):
            row_frame = ttk.Frame(mapping_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=f"{interface} →", width=20).pack(side=tk.LEFT)
            var = tk.StringVar(value=sheet)
            self.mapping_vars[interface] = var
            ttk.Entry(row_frame, textvariable=var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Browser options
        browser_frame = ttk.LabelFrame(self.settings_frame, text="🖥️ Browser Options", padding="10")
        browser_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.show_browser_var = tk.BooleanVar(value=self.settings.get("show_browser", True))
        ttk.Checkbutton(browser_frame, text="Show browser window (tampilkan browser saat scraping)", variable=self.show_browser_var).pack(anchor=tk.W)
        
        self.attach_existing_var = tk.BooleanVar(value=self.settings.get("attach_existing", False))
        ttk.Checkbutton(browser_frame, text="🔗 Attach to existing Chrome (gunakan browser yang sudah terbuka)", variable=self.attach_existing_var).pack(anchor=tk.W)
        
        # Info for attach mode
        attach_info = ttk.Frame(browser_frame)
        attach_info.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(
            attach_info,
            text="💡 Untuk pakai Chrome existing, jalankan Chrome dengan command:",
            font=("Segoe UI", 8, "italic"),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        cmd_frame = ttk.Frame(attach_info)
        cmd_frame.pack(fill=tk.X, pady=2)
        
        self.debug_cmd_var = tk.StringVar(value='"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.debug_cmd_var, font=("Consolas", 8), state="readonly")
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(cmd_frame, text="📋 Copy", width=8, command=self._copy_debug_cmd).pack(side=tk.LEFT, padx=5)
        
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
        
        # Preview table
        columns = ("Sheet", "Tanggal", "Waktu", "Curr IN", "Curr OUT", "Max IN", "Max OUT", "Avg IN", "Avg OUT", "Status")
        
        tree_frame = ttk.Frame(self.preview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        col_widths = {"Sheet": 60, "Tanggal": 80, "Waktu": 50, "Status": 80}
        for col in columns:
            self.preview_tree.heading(col, text=col)
            width = col_widths.get(col, 65)
            self.preview_tree.column(col, width=width, minwidth=50)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Buttons
        preview_btn_frame = ttk.Frame(self.preview_frame)
        preview_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(preview_btn_frame, text="🗑️ Clear Preview", command=self._clear_preview).pack(side=tk.LEFT, padx=5)
        self.write_btn = ttk.Button(preview_btn_frame, text="✍️ Write to Excel", command=self._write_preview_data, state=tk.DISABLED)
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
    
    def _toggle_language(self):
        """Toggle between Indonesian and English"""
        if self.current_lang == "id":
            self.current_lang = "en"
            self.lang_btn.config(text="🌐 ID")
        else:
            self.current_lang = "id"
            self.lang_btn.config(text="🌐 EN")
        
        self.settings["language"] = self.current_lang
        self._update_all_texts()
    
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
    
    def _copy_debug_cmd(self):
        """Copy debug command to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.debug_cmd_var.get())
        messagebox.showinfo("Info", "Command copied to clipboard!\n\nPaste dan jalankan di Command Prompt.")
    
    def _browse_excel(self):
        """Browse for Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.excel_path_var.set(file_path)
    
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
            messagebox.showerror("Error", get_text("error_no_file", lang))
            return False
        
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
        
        # Show browser
        config.SHOW_BROWSER = self.show_browser_var.get()
        
        # URL
        config.CACTI_URL = self.url_var.get()
        
        # Interface mapping - filter by selected sheets
        selected = {k: v for k, v in self.mapping_vars.items() if self.sheet_vars.get(v.get(), tk.BooleanVar(value=True)).get()}
        config.INTERFACE_TO_SHEET = {k: v.get() for k, v in self.mapping_vars.items()}
    
    def _run_scraping_thread(self, start_date: datetime, end_date: datetime, excel_path: str):
        """Thread for running scraping"""
        lang = self.current_lang
        is_dry_run = self.dry_run_var.get()
        
        try:
            mode_text = "🧪 DRY RUN MODE - " if is_dry_run else ""
            self._update_progress(f"{mode_text}Memulai proses...", 0)
            
            # Filter interfaces by selected sheets
            selected_sheets = [name for name, var in self.sheet_vars.items() if var.get()]
            
            # Scrape data with attach option
            attach_existing = self.attach_existing_var.get()
            data = run_scraper(start_date, end_date, self._update_progress, attach_to_existing=attach_existing)
            
            # Filter by selected sheets
            data = [d for d in data if d.get('sheet') in selected_sheets]
            
            self.scraped_data = data
            
            if not data:
                self._update_progress(get_text("status_no_data", lang))
            else:
                # Populate preview
                self.root.after(0, lambda: self._populate_preview(data, excel_path))
                
                if is_dry_run:
                    self._update_progress(f"🧪 DRY RUN: {len(data)} data siap untuk ditulis (preview only)", 100)
                    self.root.after(0, lambda: self.write_btn.configure(state=tk.NORMAL))
                    self.root.after(0, lambda: self.notebook.select(self.preview_frame))
                else:
                    # Write to Excel
                    write_to_excel(excel_path, data, self._update_progress)
                    self._update_progress(get_text("status_complete", lang), 100)
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        get_text("success_title", lang), 
                        get_text("success_message", lang, count=len(data))
                    ))
            
        except Exception as e:
            err_msg = str(e)
            self._update_progress(f"❌ Error: {err_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", err_msg))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.configure(state=tk.DISABLED))
    
    def _populate_preview(self, data: List[Dict], excel_path: str = ""):
        """Populate preview tree with data"""
        self._clear_preview()
        
        for item in data:
            values = (
                item.get('sheet', ''),
                item.get('date', '').strftime('%d/%m/%Y') if item.get('date') else '',
                f"{item.get('time_hour', 0):02d}.{item.get('time_minute', 0):02d}",
                item.get('curr_in', ''),
                item.get('curr_out', ''),
                item.get('max_in', ''),
                item.get('max_out', ''),
                item.get('avg_in', ''),
                item.get('avg_out', ''),
                "Pending"
            )
            self.preview_tree.insert('', tk.END, values=values)
    
    def _clear_preview(self):
        """Clear preview tree"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
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
            messagebox.showinfo("Sukses", f"Berhasil menulis {len(self.scraped_data)} data ke Excel!")
            self._clear_preview()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _save_settings(self):
        """Save settings to file"""
        new_settings = {
            "cacti_url": self.url_var.get(),
            "time_format": self.time_format_var.get(),
            "interface_mapping": {k: v.get() for k, v in self.mapping_vars.items()},
            "selected_sheets": {k: v.get() for k, v in self.sheet_vars.items()},
            "skip_filled_rows": self.skip_filled_var.get(),
            "dry_run_mode": self.dry_run_var.get(),
            "show_browser": self.show_browser_var.get(),
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
            "dry_run_mode": self.dry_run_var.get(),
        })
    
    def _stop_process(self):
        """Stop the process"""
        self.is_running = False
        self._update_progress(get_text("status_stopped", self.current_lang))
        messagebox.showwarning("Info", get_text("stop_warning", self.current_lang))
    
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
        
        ttk.Label(
            basic_frame,
            text=get_text("help_basic_steps", lang),
            font=("Segoe UI", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # ===== FEATURES =====
        features_frame = ttk.LabelFrame(scrollable_frame, text=get_text("help_features_title", lang), padding="10")
        features_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            features_frame,
            text=get_text("help_features", lang),
            font=("Consolas", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # ===== TIPS =====
        tips_frame = ttk.LabelFrame(scrollable_frame, text=get_text("help_tips_title", lang), padding="10")
        tips_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            tips_frame,
            text=get_text("help_tips", lang),
            font=("Segoe UI", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # ===== WARNINGS =====
        warning_frame = ttk.LabelFrame(scrollable_frame, text=get_text("help_warnings_title", lang), padding="10")
        warning_frame.pack(fill=tk.X, pady=(0, 10))
        
        for key in ["help_warning1", "help_warning2", "help_warning3"]:
            ttk.Label(
                warning_frame,
                text=f"⚠️ {get_text(key, lang)}",
                font=("Segoe UI", 9),
                foreground="#e67e22"
            ).pack(anchor=tk.W, pady=1)
        
        # ===== CREATOR =====
        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(10, 10))
        
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
