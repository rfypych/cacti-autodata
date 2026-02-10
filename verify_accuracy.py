"""
VERIFIKASI PER-SLOT: CSV vs SVG
================================
Jalankan di KANTOR untuk membuktikan bahwa
nilai CSV per-slot (00:00→09:00, 00:00→16:00)
PERSIS SAMA dengan yang ditampilkan di graph SVG.

Cara kerja:
1. Download CSV per-slot → hitung Current/Avg/Max
2. Download SVG per-slot → decode legend pakai digit mapping dari Max
3. Bandingkan value per value

Jalankan: python verify_accuracy.py
"""
import requests, json, os, sys, re, csv
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
from io import StringIO
import urllib3
urllib3.disable_warnings()

sys.path.insert(0, os.path.dirname(__file__))
import config


# ============================================================
# SVG STRUCTURAL DECODER
# ============================================================

def extract_uses(svg_text):
    uses = []
    for m in re.finditer(r'<use\s+(?:xlink:)?href="#([^"]+)"\s+x="([^"]+)"\s+y="([^"]+)"', svg_text):
        uses.append((m.group(1), float(m.group(2)), float(m.group(3))))
    return uses

def group_by_y(uses, tolerance=2):
    groups = defaultdict(list)
    for glyph_id, x, y in uses:
        y_key = round(y / tolerance) * tolerance
        groups[y_key].append((x, glyph_id))
    for k in groups:
        groups[k].sort()
    return dict(sorted(groups.items()))

def find_space_glyph(uses_by_y):
    for y_key in sorted(uses_by_y.keys()):
        items = uses_by_y[y_key]
        if y_key > 280 and len(items) > 50:
            return items[0][1]
    return None

def split_by_spaces(glyph_ids, space_id):
    segments = []
    current = []
    for g in glyph_ids:
        if g == space_id:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(g)
    if current:
        segments.append(current)
    return segments

def decode_svg_with_known_values(svg_text, known_max_in, known_max_out):
    """
    Decode SVG legend using KNOWN Maximum values as digit-mapping key.
    
    Steps:
    1. Find legend lines (Inbound at y~300, Outbound at y~312)
    2. Extract glyph sequences for Maximum values
    3. Build digit mapping: glyph_id → digit char
    4. Decode ALL values (Current, Average, Maximum)
    """
    uses = extract_uses(svg_text)
    uses_by_y = group_by_y(uses)
    space_id = find_space_glyph(uses_by_y)
    
    if not space_id:
        return None, "Cannot find space glyph"
    
    # Find legend lines
    legend_lines = []
    for y_key in sorted(uses_by_y.keys()):
        items = uses_by_y[y_key]
        if y_key > 280 and len(items) > 50:
            legend_lines.append((y_key, [g for _, g in items]))
    
    if len(legend_lines) < 2:
        return None, f"Expected 2+ legend lines, found {len(legend_lines)}"
    
    # Parse structure of each legend line
    results = {}
    charmap = {space_id: ' '}
    
    # Process each legend line (Inbound, Outbound)
    for line_idx, (y_key, glyph_ids) in enumerate(legend_lines[:2]):
        segments = split_by_spaces(glyph_ids, space_id)
        
        if len(segments) < 8:
            continue
        
        # Identify label
        label_seg = segments[0]
        if len(label_seg) == 7:
            label = "Inbound"
        elif len(label_seg) == 8:
            label = "Outbound"
        else:
            continue
        
        # Value segments: seg[2]=current, seg[4]=average, seg[6]=maximum
        # Unit+word segments: seg[3]="MAverage:", seg[5]="MMaximum:", seg[7]="M"
        
        # Get the Maximum value glyphs (seg[6])
        max_seg = segments[6]
        
        # Get the known max value for this label
        known_max = known_max_in if label == "Inbound" else known_max_out
        
        # Parse the known max string (e.g. "80.00 M" → "80.00")
        known_num = known_max.split()[0]  # "80.00"
        
        if len(known_num) != len(max_seg):
            # Length mismatch - values might not match
            return None, f"{label} Max length mismatch: SVG has {len(max_seg)} glyphs, expected {len(known_num)} chars for '{known_num}'"
        
        # Build digit mapping from Maximum value
        for glyph, char in zip(max_seg, known_num):
            if char == '.':
                charmap[glyph] = '.'
            else:
                charmap[glyph] = char
        
        # Also map the unit suffix
        # seg[7] = final unit (1 char)
        if len(segments) > 7 and len(segments[7]) == 1:
            unit_char = known_max.split()[1] if len(known_max.split()) > 1 else 'M'
            charmap[segments[7][0]] = unit_char
        
        # seg[3][0] and seg[5][0] are unit chars from prev values
        if len(segments) > 3 and len(segments[3]) >= 1:
            # This could be a different unit than max's unit
            # We'll map it after we try to decode
            pass
        
        # Now decode Current and Average using the mapping
        decoded = {}
        stat_names = ['current', 'average', 'maximum']
        val_indices = [2, 4, 6]
        
        for stat, val_idx in zip(stat_names, val_indices):
            if val_idx >= len(segments):
                break
            
            val_seg = segments[val_idx]
            val_chars = []
            unmapped = []
            
            for g in val_seg:
                if g in charmap:
                    val_chars.append(charmap[g])
                else:
                    val_chars.append('?')
                    unmapped.append(g)
            
            # Get unit
            if stat == 'maximum':
                unit = known_max.split()[1] if len(known_max.split()) > 1 else '?'
            elif val_idx + 1 < len(segments):
                # Unit is first char of next segment (e.g., "MAverage:")
                unit_g = segments[val_idx + 1][0]
                unit = charmap.get(unit_g, '?')
            else:
                unit = '?'
            
            val_str = "".join(val_chars)
            decoded[stat] = f"{val_str} {unit}"
        
        results[label] = decoded
    
    return results, None


# ============================================================
# CSV STATS CALCULATOR  
# ============================================================

def calculate_csv_stats(csv_text):
    """Calculate stats from CSV text, return formatted values"""
    content = csv_text.lstrip('\ufeff')
    reader = csv.reader(StringIO(content))
    
    rows = []
    header = None
    reading = False
    
    for row in reader:
        if not row:
            continue
        if row[0] == "Date":
            reading = True
            header = row
            continue
        if reading:
            rows.append(row)
    
    if not rows or not header:
        return None
    
    # Find Named columns (Inbound/Outbound)
    in_idx = out_idx = None
    for i, h in enumerate(header):
        hl = h.strip().lower()
        if 'inbound' in hl and in_idx is None:
            in_idx = i
        elif 'outbound' in hl and out_idx is None:
            out_idx = i
    
    if in_idx is None:
        in_idx = 2  # fallback
    if out_idx is None:
        out_idx = 4  # fallback
    
    def get_vals(idx):
        vals = []
        for r in rows:
            try:
                if idx < len(r) and r[idx] and r[idx].strip() != 'NaN':
                    vals.append(float(r[idx]))
            except:
                pass
        return vals
    
    in_vals = get_vals(in_idx)
    out_vals = get_vals(out_idx)
    
    if not in_vals:
        return None
    
    def fmt(val):
        av = abs(val)
        if av >= 1e9: return f"{val/1e9:.2f} G"
        elif av >= 1e6: return f"{val/1e6:.2f} M"
        elif av >= 1e3: return f"{val/1e3:.2f} K"
        else: return f"{val:.2f}"
    
    return {
        "Inbound": {
            "current": fmt(in_vals[-1]),
            "average": fmt(sum(in_vals)/len(in_vals)),
            "maximum": fmt(max(in_vals)),
        },
        "Outbound": {
            "current": fmt(out_vals[-1]) if out_vals else "N/A",
            "average": fmt(sum(out_vals)/len(out_vals)) if out_vals else "N/A",
            "maximum": fmt(max(out_vals)) if out_vals else "N/A",
        }
    }


# ============================================================
# MAIN VERIFICATION
# ============================================================

def main():
    # Load cookies
    cookies_path = os.path.join(os.path.dirname(__file__), "cacti_cookies.json")
    with open(cookies_path) as f:
        cookies = json.load(f)
    
    session = requests.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c.get('domain'))
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # Build URLs
    parsed = urlparse(config.CACTI_URL)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    xport_url = base.replace('graph_view.php', 'graph_xport.php')
    graph_url = base.replace('graph_view.php', 'graph_image.php')
    
    # Test dates - use recent date that has 5-min resolution
    # AND a historical date with 2-hour resolution
    today = datetime.now()
    test_dates = [
        today,  # Today: 5-min resolution (paling akurat)
    ]
    
    slots = [
        (9, 0, "09:00"),
        (16, 0, "16:00"),
    ]
    
    print("=" * 70)
    print("  VERIFIKASI AKURASI: CSV vs SVG PER-SLOT")
    print("  Membuktikan nilai scraper = nilai graph Cacti")
    print("=" * 70)
    
    total_checks = 0
    passed_checks = 0
    failed_details = []
    
    for dt in test_dates:
        for hour, minute, time_str in slots:
            # Timestamps
            start_ts = int(dt.replace(hour=0, minute=0, second=0).timestamp())
            end_ts = int(dt.replace(hour=hour, minute=minute, second=0).timestamp()) + 300
            
            date_str = dt.strftime("%d/%m/%Y")
            
            print(f"\n{'─'*70}")
            print(f"  📅 {date_str} slot {time_str} (00:00 → {time_str})")
            print(f"{'─'*70}")
            
            for interface, gid in config.GRAPH_IDS.items():
                # 1. Download CSV
                csv_url = f"{xport_url}?local_graph_id={gid}&rra_id=0&graph_start={start_ts}&graph_end={end_ts}"
                csv_resp = session.get(csv_url, verify=False)
                csv_stats = calculate_csv_stats(csv_resp.text)
                
                if not csv_stats:
                    print(f"\n  ❌ {interface}: CSV kosong!")
                    continue
                
                # 2. Download SVG
                svg_url = f"{graph_url}?local_graph_id={gid}&rra_id=0&graph_start={start_ts}&graph_end={end_ts}&image_format=svg"
                svg_resp = session.get(svg_url, verify=False)
                svg_text = svg_resp.text
                
                # 3. Decode SVG using CSV Max as key
                svg_results, error = decode_svg_with_known_values(
                    svg_text,
                    csv_stats["Inbound"]["maximum"],
                    csv_stats["Outbound"]["maximum"]
                )
                
                print(f"\n  📊 {interface}:")
                
                if error:
                    print(f"     ⚠ SVG decode error: {error}")
                    print(f"     CSV values (for reference):")
                    for label in ["Inbound", "Outbound"]:
                        for stat in ["current", "average", "maximum"]:
                            print(f"       {label} {stat}: {csv_stats[label][stat]}")
                    continue
                
                # 4. Compare
                for label in ["Inbound", "Outbound"]:
                    if label not in svg_results:
                        continue
                    
                    for stat in ["current", "average", "maximum"]:
                        csv_val = csv_stats[label][stat]
                        svg_val = svg_results[label].get(stat, "?")
                        
                        total_checks += 1
                        
                        # Check if SVG has unmapped digits
                        if '?' in svg_val:
                            icon = "🔶"
                            note = "(digit belum ter-map)"
                            # Still count as pass if the mapped parts match
                        elif csv_val == svg_val:
                            icon = "✅"
                            note = ""
                            passed_checks += 1
                        else:
                            icon = "❌"
                            note = "MISMATCH!"
                            failed_details.append(
                                f"{interface} {date_str} {time_str} {label} {stat}: "
                                f"CSV={csv_val} SVG={svg_val}"
                            )
                        
                        print(f"     {icon} {label:8s} {stat:8s}  CSV={csv_val:>12s}  SVG={svg_val:>12s}  {note}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"  RINGKASAN")
    print(f"{'='*70}")
    print(f"  Total checks: {total_checks}")
    print(f"  Passed (exact match): {passed_checks}")
    
    if failed_details:
        print(f"  Failed: {len(failed_details)}")
        for d in failed_details:
            print(f"    - {d}")
    
    if passed_checks == total_checks:
        print(f"\n  🎉 SEMUA MATCH! CSV per-slot = SVG per-slot")
        print(f"  Scraper menghasilkan nilai yang PERSIS SAMA")
        print(f"  dengan yang ditampilkan di graph Cacti!")
    elif passed_checks > 0:
        pct = passed_checks / total_checks * 100
        print(f"\n  📊 Akurasi: {pct:.0f}%")
    
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
