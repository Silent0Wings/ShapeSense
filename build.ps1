# build.ps1 -- Compile phase1_report.tex to PDF.
#
# Usage:
#   .\build.ps1                     # builds phase1_report.tex
#   .\build.ps1 -File other.tex     # builds a different .tex file
#
# Runs pdflatex twice so references, the table of contents, and the
# bibliography resolve correctly. Auxiliary files (.aux, .log, .out, ...)
# are cleaned up after a successful build; the .pdf is left next to the
# .tex file.

param(
    [string]$File = "phase1_report.tex"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$texPath = Join-Path $root $File

if (-not (Test-Path $texPath)) {
    Write-Error "Not found: $texPath"
    exit 1
}

# Locate pdflatex. MiKTeX is preferred: on this machine the TeX Live
# install on PATH is missing packages (e.g. booktabs), while MiKTeX
# installs missing packages on demand. Known install locations are
# checked first, then PATH, as a last resort.
$candidates = @(
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
    "C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe"
)
$pdflatexExe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $pdflatexExe) {
    $pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
    if ($pdflatex) { $pdflatexExe = $pdflatex.Source }
}

if (-not $pdflatexExe) {
    Write-Error "pdflatex not found. Install MiKTeX or TeX Live."
    exit 1
}

Write-Host "Using pdflatex: $pdflatexExe"
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($File)

for ($i = 1; $i -le 2; $i++) {
    Write-Host "`n--- Pass $i/2 ---"
    & $pdflatexExe -interaction=nonstopmode -halt-on-error -output-directory="$root" "$texPath"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pdflatex failed on pass $i. See $root\$baseName.log for details."
        exit 1
    }
}

# Clean up auxiliary files, keep the PDF.
$exts = @(".aux", ".out", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk", ".synctex.gz", ".bbl", ".blg", ".log")
foreach ($ext in $exts) {
    $f = Join-Path $root "$baseName$ext"
    if (Test-Path $f) { Remove-Item $f -Force }
}

Write-Host "`nBuilt: $root\$baseName.pdf"
