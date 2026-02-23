import holidays
h = holidays.country_holidays('ID', years=2026)
for k, v in sorted(h.items()):
    print(f"{k}: {v}")
