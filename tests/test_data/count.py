import os
from pathlib import Path

CONTAINS_DIR = Path("contains")

print("| Data set      | Items | Screenshots | Accuracy   |")
print("| ------------- | ----- | ----------- | ---------- |")

total_items = 0
total_pngs = 0

EXCLUDE = ["example", "download"]

for data_set in os.listdir(CONTAINS_DIR):
    if data_set in EXCLUDE:
        continue

    items = len(os.listdir(CONTAINS_DIR / data_set))
    total_items += items

    pngs = 0

    for item in os.listdir(CONTAINS_DIR / data_set):
        pngs += len(os.listdir(CONTAINS_DIR / data_set / item))

    total_pngs += pngs

    print(f"| {data_set:<13s} | {items:<5d} | {pngs:<11d} |            |")

print(f"| **Total**     | {total_items:<5d} | {total_pngs:<11d} | **%**      |")
