import json
from pathlib import Path

# Read the current mappings
mapping_file = Path("data/json/unit_mappings.json")
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add cooling <-> 쿨링 mapping
data["term_replacements"]["쿨링"] = "cooling"
data["term_replacements"]["cooling"] = "쿨링"

# Save the updated mappings
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Also update the backup file if it exists
backup_file = Path("data/unit_mappings.json")
if backup_file.exists():
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("SUCCESS: cooling <-> 쿨링 mapping added")
