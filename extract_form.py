import requests
import re
import json

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeFoeV-XLURb6RfIL20LrUCldthoaeAp0HDLFF5P5TEZlpHKA/viewform"

print("Fetching form...")
try:
    resp = requests.get(FORM_URL, timeout=15)
    print(f"Status: {resp.status_code}")
    html = resp.text
    
    # Extract FB_PUBLIC_LOAD_DATA_ JSON
    match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);\s*</script>', html, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        # The fields are usually at data[1][1]
        fields = data[1][1] if len(data) > 1 else []
        print("Fields found:")
        for f in fields:
            try:
                label = f[1]
                entry_id = f[4][0][0]
                print(f"  Label: {label!r} -> entry.{entry_id}")
            except:
                pass
    else:
        print("FB_PUBLIC_LOAD_DATA_ not found, trying regex on entry IDs...")
        entries = re.findall(r'entry\.(\d+)', html)
        print("Entry IDs found:", entries)
        
except Exception as e:
    print(f"Error: {e}")
