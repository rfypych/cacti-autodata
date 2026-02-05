# 🌵 Cacti AutoData

Automatically record bandwidth data from Cacti monitoring system to Excel spreadsheet.

## 📋 Description

This tool is designed to help with bandwidth data recording tasks from Cacti monitoring system to Excel. The program will:

1. Open a browser and access the Cacti page
2. Change the time filter according to the input date
3. Extract Current, Maximum, and Average values for Inbound/Outbound
4. Fill the data into an existing Excel file (matching date and time)

## 🚀 Installation

### 1. Install Python

Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

> ⚠️ During installation, check ✅ **"Add Python to PATH"**

### 2. Install Dependencies

Open Command Prompt in the project folder, then run:

```bash
pip install -r requirements.txt
```

### 3. Install Chrome Browser

Make sure Google Chrome is installed on the computer.

## 📖 Usage

### 1. Run the Program

```bash
python main.py
```

### 2. In the GUI Window:

1. Fill in **Start Date** and **End Date** (format: DD/MM/YYYY)
2. Click **Browse** to select the Excel file from the office
3. Click **🚀 Start Recording**
4. Wait until the process is complete

### 3. Language

Click the **🌐** button in the top right corner to switch between Indonesian and English.

### 4. Result

Bandwidth data will be automatically filled in the Excel file according to matching date and time.

## ⚙️ Configuration

If you need to adjust settings, edit the `config.py` file:

### Cacti URL
```python
CACTI_URL = "http://monitor.kabngawi.id/cacti/graph_view.php"
```

### Interface to Sheet Mapping
```python
INTERFACE_TO_SHEET = {
    "ether4-iForte": "iForte",
    "ether5-Telkom": "Telkom",
    "ether6-Moratel": "Moratel",
}
```

### Excel Columns
```python
EXCEL_COL_TANGGAL = 1  # Column A
EXCEL_COL_WAKTU = 2    # Column B
EXCEL_COL_CURR_IN = 3  # Column C
# ... etc
```

### Time Format
```python
TIME_FORMAT_EXCEL = "%H:%M"  # Example: "09:00"
# or
TIME_FORMAT_EXCEL = "%H:%M:%S"  # Example: "09:00:00"
```

## 🔧 Troubleshooting

### Browser doesn't appear
- Make sure Chrome is installed
- Try setting `SHOW_BROWSER = True` in config.py

### Data not found in Excel
- Check sheet names (case-sensitive)
- Check date/time format in Excel vs config.py
- Make sure Excel file already has content (dates & times)

### Cannot access Cacti
- Make sure you're connected to the office network
- Check URL in config.py

## 📁 File Structure

```
cacti-autodata/
├── main.py           # Entry point
├── gui.py            # Graphical interface
├── scraper.py        # Cacti scraping logic
├── excel_writer.py   # Excel writing logic
├── config.py         # Settings (EDIT THIS)
├── languages.py      # Language strings (ID/EN)
├── requirements.txt  # Dependencies
└── README.md         # This documentation
```

## 📝 Notes

- The program must run on a computer that can access Cacti
- Do not close the browser that opens during the process
- Backup the Excel file before running the program (just in case)

---

Created by: **Rofikul Huda** | GitHub: [@rfypych](https://github.com/rfypych)
