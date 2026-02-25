"""
Settings Manager Module
Mengelola penyimpanan dan pembacaan settings ke file lokal
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

import config

# Path untuk menyimpan settings
SETTINGS_FILE = os.path.join(config.get_app_dir(), "user_settings.json")


DEFAULT_SETTINGS = {
    # Last used values (Session persistence)
    "last_excel_path": "",
    "last_start_date": "",
    "last_end_date": "",
    
    # Cacti configuration
    "cacti_url": "https://monitor.kabngawi.id/cacti/graph_view.php?action=tree&node=tbranch-169&host_id=101&site_id=-1&host_template_id=-1&hgd=&hyper=true&rfilter=",
    
    # Time format
    "time_format": "dot",  # "dot" = 09.00, "colon" = 09:00
    
    # Interface to sheet mapping (Synced with config.py defaults)
    "interface_mapping": {
        "LocalNet": "LocalNet",
        "iForte": "iForte", 
        "Telkom": "Telkom",
        "Moratel": "Moratel",
    },
    
    # Sheet selection (which sheets to process)
    "selected_sheets": {
        "LocalNet": False, # PARITY: Default off
        "iForte": True,
        "Moratel": True,
        "Telkom": True,
    },
    
    # Processing options
    "skip_filled_rows": True,
    "skip_weekends": True,
    "skip_holidays": False,
    "include_metadata": False,
    "dry_run_mode": False,
    "demo_mode": False,
    "show_browser": True,
    
    # Google Form settings (New in v3.1 for EXE readiness)
    "google_form_url": "https://docs.google.com/forms/d/e/1FAIpQLSeFoeV-XLURb6RfIL20LrUCldthoaeAp0HDLFF5P5TEZlpHKA/viewform",
    "google_form_entries": {
        "tanggal": "",
        "total": "",
        "moratel": "",
        "iforte": "",
        "telkom": "",
    },
    
    # Hybrid GUI-Web settings (v4.0)
    "web_port": 8181,
    
    # UI preferences
    "language": "id",
}


def load_settings() -> Dict[str, Any]:
    """Load settings from file, or return defaults if file doesn't exist"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = DEFAULT_SETTINGS.copy()
                settings.update(saved)
                return settings
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting value"""
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set a single setting value"""
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)


def update_settings(updates: Dict[str, Any]) -> bool:
    """Update multiple settings at once"""
    settings = load_settings()
    settings.update(updates)
    return save_settings(settings)


def reset_settings() -> bool:
    """Reset all settings to defaults"""
    return save_settings(DEFAULT_SETTINGS.copy())
