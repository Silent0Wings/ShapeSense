@echo off
rem Builds the data archive the pipeline needs (the whole data_set folder) in this scripts folder.
rem The work is done by make_data_zip.py: Windows tar cannot write an archive
rem with this many files (over 65,535) without damaging it.

python "%~dp0make_data_zip.py"
if errorlevel 1 (
    echo Failed to create the archive.
    exit /b 1
)
