"""Build a source-only archive of the four raw data sources.

Keeps the folder names Stage 1 expects, under a top-level data_set folder.
Leaves out kaggle_dinesh, unified, the fresh holdouts and any zip files.
The archive is written next to this script. Python's zipfile handles the
large entry count (over 65,535) that the Windows tar writer cannot.
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data_set")
OUT = os.path.join(HERE, "shapesense_raw_sources_v1.zip")
SOURCES = ["2D geometric shapes dataset", "kaggle_reevald", "github_handdrawn", "quickdraw", "quickdraw_repo"]
EXCLUDED = ("kaggle_dinesh", "unified", "fresh_holdout")

if os.path.exists(OUT):
    os.remove(OUT)

count = 0
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    for src in SOURCES:
        root = os.path.join(DATA, src)
        if not os.path.isdir(root):
            sys.exit(f"Missing source folder: {root}")
        for dirpath, _, files in os.walk(root):
            for name in files:
                full = os.path.join(dirpath, name)
                arc = os.path.relpath(full, REPO).replace(os.sep, "/")
                if any(e in arc for e in EXCLUDED):
                    sys.exit(f"Excluded path reached the archive: {arc}")
                z.write(full, arc)
                count += 1

with zipfile.ZipFile(OUT) as z:
    bad = z.testzip()
if bad:
    sys.exit(f"Archive failed the integrity test at {bad}")

print(f"Wrote {OUT}")
print(f"Files: {count}")
print(f"Size: {os.path.getsize(OUT)} bytes")
print("Integrity test passed.")
