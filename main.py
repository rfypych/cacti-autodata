#!/usr/bin/env python3
"""
Cacti AutoData - Main Entry Point
Otomatis mengambil data bandwidth dari Cacti dan mengisi ke Excel

Cara menjalankan:
    python main.py
"""

import holidays
import holidays.countries  # Force PyInstaller to see this
from gui import main

if __name__ == "__main__":
    main()
