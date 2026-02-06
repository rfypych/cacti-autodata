"""
Settings Manager Module
Mengelola penyimpanan dan pembacaan settings ke file lokal
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


# Path untuk menyimpan settings
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "user_settings.json")


DEFAULT_SETTINGS = {
    # Last used values
    "last_excel_path": "",
    "last_start_date": "",
    "last_end_date": "",
    
    # Cacti configuration
    "cacti_url": "http://monitor.kabngawi.id/cacti/graph_view.php",
    
    # Time format
    "time_format": "dot",  # "dot" = 09.00, "colon" = 09:00
    
    # Interface to sheet mapping
    "interface_mapping": {
        "ether4-iForte": "iForte",
        "ether5-Telkom": "Telkom",
        "ether6-Moratel": "Moratel",
    },
    
    # Sheet selection (which sheets to process)
    "selected_sheets": {
        "iForte": True,
        "Moratel": True,
        "Telkom": True,
    },
    
    # Processing options
    "skip_filled_rows": True,
    "dry_run_mode": False,
    "show_browser": True,
    
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
