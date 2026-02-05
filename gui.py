"""
GUI Module
Antarmuka grafis untuk Cacti AutoData menggunakan Tkinter
With dual language support (Indonesian/English)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
from typing import Optional

import config
from scraper import run_scraper
from excel_writer import write_to_excel
from languages import LANGUAGES, get_text


class CactiAutoDataGUI:
    """GUI utama aplikasi"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.current_lang = "id"  # Default: Indonesian
        
        self.root.title(get_text("app_title", self.current_lang))
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Variables
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.excel_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value=get_text("status_waiting", self.current_lang))
        self.progress_var = tk.DoubleVar(value=0)
        
        self.is_running = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Buat semua widget"""
        # Main container dengan padding
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== HEADER =====
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title and language switcher in same row
        title_row = ttk.Frame(header_frame)
        title_row.pack(fill=tk.X)
        
        self.title_label = ttk.Label(
            title_row, 
            text="🌵 Cacti AutoData",
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Language switcher
        self.lang_btn = ttk.Button(
            title_row,
            text="🌐 EN",
            width=8,
            command=self._toggle_language
        )
        self.lang_btn.pack(side=tk.RIGHT)
        
        self.subtitle_label = ttk.Label(
            header_frame,
            text=get_text("subtitle", self.current_lang),
            font=("Segoe UI", 10)
        )
        self.subtitle_label.pack()
        
        # ===== INPUT SECTION =====
        self.input_frame = ttk.LabelFrame(self.main_frame, text=get_text("input_title", self.current_lang), padding="10")
        self.input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Grid layout untuk input
        self.input_frame.columnconfigure(1, weight=1)
        
        # Tanggal Mulai
        self.start_date_label = ttk.Label(self.input_frame, text=get_text("start_date", self.current_lang))
        self.start_date_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        start_entry = ttk.Entry(self.input_frame, textvariable=self.start_date_var, width=20)
        start_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.start_date_hint = ttk.Label(self.input_frame, text=get_text("date_format_hint", self.current_lang), font=("Segoe UI", 8))
        self.start_date_hint.grid(row=0, column=2, sticky=tk.W)
        
        # Tanggal Akhir
        self.end_date_label = ttk.Label(self.input_frame, text=get_text("end_date", self.current_lang))
        self.end_date_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        end_entry = ttk.Entry(self.input_frame, textvariable=self.end_date_var, width=20)
        end_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.end_date_hint = ttk.Label(self.input_frame, text=get_text("date_format_hint", self.current_lang), font=("Segoe UI", 8))
        self.end_date_hint.grid(row=1, column=2, sticky=tk.W)
        
        # File Excel
        self.excel_label = ttk.Label(self.input_frame, text=get_text("excel_file", self.current_lang))
        self.excel_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        excel_frame = ttk.Frame(self.input_frame)
        excel_frame.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        excel_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, width=50)
        excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.browse_btn = ttk.Button(excel_frame, text=get_text("browse", self.current_lang), command=self._browse_excel)
        self.browse_btn.pack(side=tk.LEFT)
        
        # ===== KONFIGURASI INFO =====
        self.config_frame = ttk.LabelFrame(self.main_frame, text=get_text("config_title", self.current_lang), padding="10")
        self.config_frame.pack(fill=tk.X, pady=(0, 15))
        
        config_info = f"""
URL Cacti: {config.CACTI_URL}
Interface: {', '.join(config.INTERFACE_TO_SHEET.keys())}
Sheet Excel: {', '.join(config.INTERFACE_TO_SHEET.values())}
Slot Waktu: {', '.join([f"{h:02d}:{m:02d}" for h, m in config.TIME_SLOTS])}
        """.strip()
        
        config_label = ttk.Label(self.config_frame, text=config_info, font=("Consolas", 9))
        config_label.pack(anchor=tk.W)
        
        self.config_hint = ttk.Label(
            self.config_frame, 
            text=get_text("config_hint", self.current_lang),
            font=("Segoe UI", 8, "italic")
        )
        self.config_hint.pack(anchor=tk.W, pady=(5, 0))
        
        # ===== PROGRESS SECTION =====
        self.progress_frame = ttk.LabelFrame(self.main_frame, text=get_text("progress_title", self.current_lang), padding="10")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        status_label = ttk.Label(
            self.progress_frame, 
            textvariable=self.status_var,
            font=("Segoe UI", 9)
        )
        status_label.pack(anchor=tk.W)
        
        # Log area
        log_frame = ttk.Frame(self.progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9), state=tk.DISABLED)
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
            command=self._start_process,
            style="Accent.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text=get_text("btn_stop", self.current_lang),
            command=self._stop_process,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.help_btn = ttk.Button(
            button_frame,
            text=get_text("btn_help", self.current_lang),
            command=self._show_help
        )
        self.help_btn.pack(side=tk.LEFT, padx=5)
        
        self.exit_btn = ttk.Button(
            button_frame,
            text=get_text("btn_exit", self.current_lang),
            command=self.root.quit
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=5)
    
    def _toggle_language(self):
        """Toggle between Indonesian and English"""
        if self.current_lang == "id":
            self.current_lang = "en"
            self.lang_btn.config(text="🌐 ID")
        else:
            self.current_lang = "id"
            self.lang_btn.config(text="🌐 EN")
        
        self._update_all_texts()
    
    def _update_all_texts(self):
        """Update all UI text to current language"""
        lang = self.current_lang
        
        # Window title
        self.root.title(get_text("app_title", lang))
        
        # Subtitle
        self.subtitle_label.config(text=get_text("subtitle", lang))
        
        # Input section
        self.input_frame.config(text=get_text("input_title", lang))
        self.start_date_label.config(text=get_text("start_date", lang))
        self.end_date_label.config(text=get_text("end_date", lang))
        self.excel_label.config(text=get_text("excel_file", lang))
        self.start_date_hint.config(text=get_text("date_format_hint", lang))
        self.end_date_hint.config(text=get_text("date_format_hint", lang))
        self.browse_btn.config(text=get_text("browse", lang))
        
        # Config section
        self.config_frame.config(text=get_text("config_title", lang))
        self.config_hint.config(text=get_text("config_hint", lang))
        
        # Progress section
        self.progress_frame.config(text=get_text("progress_title", lang))
        
        # Buttons
        self.start_btn.config(text=get_text("btn_start", lang))
        self.stop_btn.config(text=get_text("btn_stop", lang))
        self.help_btn.config(text=get_text("btn_help", lang))
        self.exit_btn.config(text=get_text("btn_exit", lang))
        
        # Status (only if waiting)
        if self.status_var.get() in [get_text("status_waiting", "id"), get_text("status_waiting", "en")]:
            self.status_var.set(get_text("status_waiting", lang))
    
    def _show_help(self):
        """Tampilkan jendela bantuan"""
        lang = self.current_lang
        
        help_window = tk.Toplevel(self.root)
        help_window.title(get_text("help_title", lang))
        help_window.geometry("550x450")
        help_window.resizable(False, False)
        
        # Make it modal
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Content frame
        content_frame = ttk.Frame(help_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            content_frame,
            text=get_text("help_header", lang),
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Instructions
        ttk.Label(
            content_frame,
            text=get_text("help_steps", lang).strip(),
            font=("Segoe UI", 10),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # Warnings
        warning_frame = ttk.Frame(content_frame)
        warning_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(
            warning_frame,
            text=get_text("help_warning1", lang),
            font=("Segoe UI", 9),
            foreground="orange"
        ).pack(anchor=tk.W)
        
        ttk.Label(
            warning_frame,
            text=get_text("help_warning2", lang),
            font=("Segoe UI", 9),
            foreground="orange"
        ).pack(anchor=tk.W)
        
        # Creator info
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(15, 10))
        ttk.Label(
            content_frame,
            text=get_text("help_creator", lang),
            font=("Segoe UI", 9, "italic")
        ).pack()
    
    def _browse_excel(self):
        """Buka dialog untuk memilih file Excel"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File" if self.current_lang == "en" else "Pilih File Excel",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.excel_path_var.set(file_path)
    
    def _log(self, message: str):
        """Tambah pesan ke log"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _update_progress(self, message: str, percentage: int = -1):
        """Update progress bar dan status"""
        self.status_var.set(message)
        if percentage >= 0:
            self.progress_var.set(percentage)
        self._log(message)
        self.root.update_idletasks()
    
    def _validate_inputs(self) -> bool:
        """Validasi input user"""
        lang = self.current_lang
        
        # Validasi tanggal mulai
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", get_text("error_start_date", lang))
            return False
        
        # Validasi tanggal akhir
        try:
            end_date = datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", get_text("error_end_date", lang))
            return False
        
        # Validasi range tanggal
        if end_date < start_date:
            messagebox.showerror("Error", get_text("error_date_range", lang))
            return False
        
        # Validasi file Excel
        excel_path = self.excel_path_var.get()
        if not excel_path:
            messagebox.showerror("Error", get_text("error_no_file", lang))
            return False
        
        return True
    
    def _start_process(self):
        """Mulai proses scraping"""
        if not self._validate_inputs():
            return
        
        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Parse dates
        start_date = datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
        end_date = datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
        excel_path = self.excel_path_var.get()
        
        # Run in separate thread
        thread = threading.Thread(
            target=self._run_scraping_thread,
            args=(start_date, end_date, excel_path)
        )
        thread.daemon = True
        thread.start()
    
    def _run_scraping_thread(self, start_date: datetime, end_date: datetime, excel_path: str):
        """Thread untuk menjalankan scraping"""
        lang = self.current_lang
        
        try:
            self._update_progress(get_text("status_starting", lang), 0)
            
            # Scrape data dari Cacti
            data = run_scraper(start_date, end_date, self._update_progress)
            
            if not data:
                self._update_progress(get_text("status_no_data", lang))
            else:
                # Tulis ke Excel
                write_to_excel(excel_path, data, self._update_progress)
                self._update_progress(get_text("status_complete", lang), 100)
                
                # Show success message
                self.root.after(0, lambda: messagebox.showinfo(
                    get_text("success_title", lang), 
                    get_text("success_message", lang, count=len(data))
                ))
            
        except Exception as e:
            self._update_progress(f"❌ Error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.configure(state=tk.DISABLED))
    
    def _stop_process(self):
        """Hentikan proses"""
        lang = self.current_lang
        self.is_running = False
        self._update_progress(get_text("status_stopped", lang))
        messagebox.showwarning("Info", get_text("stop_warning", lang))
    
    def run(self):
        """Jalankan GUI"""
        self.root.mainloop()


def main():
    """Entry point"""
    app = CactiAutoDataGUI()
    app.run()


if __name__ == "__main__":
    main()
