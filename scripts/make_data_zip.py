"""Build the data archive the pipeline needs, from the local data_set folder.

The archive holds every folder under data_set/, not only the four raw sources:
Stage 0 compares a fresh rebuild against data_set/unified, Stage 5 reads the
sealed fresh holdouts (data_set/fresh_holdout and fresh_holdout_2), and the
Stage 1 audit samples kaggle_dinesh. Zip files are left out. The archive is
written next to this script. Python's zipfile handles the large entry count
(over 65,535) that the Windows tar writer cannot.
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data_set")
OUT = os.path.join(HERE, "shapesense_data_set_v1.zip")
REQUIRED = ["2D geometric shapes dataset", "kaggle_reevald", "github_handdrawn", "quickdraw",
            "unified", "fresh_holdout", "fresh_holdout_2"]

missing = [d for d in REQUIRED if not os.path.isdir(os.path.join(DATA, d))]
if missing:
    sys.exit(f"Missing folders under data_set/: {missing}")

if os.path.exists(OUT):
    os.remove(OUT)

count = 0
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    for dirpath, _, files in os.walk(DATA):
        for name in files:
            if name.lower().endswith(".zip"):
                continue
            full = os.path.join(dirpath, name)
            z.write(full, os.path.relpath(full, REPO).replace(os.sep, "/"))
            count += 1

with zipfile.ZipFile(OUT) as z:
    bad = z.testzip()
if bad:
    sys.exit(f"Archive failed the integrity test at {bad}")

print(f"Wrote {OUT}")
print(f"Files: {count}")
print(f"Size: {os.path.getsize(OUT)} bytes")
print("Integrity test passed.")
