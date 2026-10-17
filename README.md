pdf_from_screenshots
====================

Small utility to crop screenshots (by pixel values), optionally split tall images into multiple pages, apply light sharpening/upscaling for readability, and merge the result into a single PDF suitable for print (A4/Letter) or keeping original sizes.

Features
- Per-folder batch processing of common image formats (PNG/JPG/TIFF)
- Per-image CSV-driven cropping or interactive per-page cropping
- Split tall screenshots into multiple PDF pages for better rendering
- Optional mild text sharpening and width restoration to avoid viewer upscaling blur
- High-quality PDF export via img2pdf when available; fallback to Pillow

Quick start
1. Create a virtual environment and install deps (Windows PowerShell):
   .\create_venv.ps1
   (or on macOS/Linux: ./create_venv.sh)

2. Run the CLI:
   python pdf_from_screenshots.py -i <input-folder> -o output.pdf -e <export-folder> --top 120 --bottom 90 --left 220 --right 220

3. Example interactive use:
   python pdf_from_screenshots.py --interactive-per-page

Files of interest
- pdf_from_screenshots.py — CLI entry point and main flow
- pdf_tools.py — argument parsing, CSV loader, image discovery helpers
- image_tools.py — image operations (crop, split, fit, sharpen, DPI helpers)
- io_tools.py — PDF writing (img2pdf wrapper + Pillow fallback)
- tests/ — pytest smoke tests (tests/test_smoke_pdf_from_screenshots.py)
- requirements.txt, create_venv.ps1, create_venv.sh

Running tests
- Activate venv then: pytest -q

Notes
- img2pdf is recommended for best PDF fidelity but optional. If missing, Pillow is used.
- For Windows paths use backslashes in commands; examples use both scripts for convenience.
