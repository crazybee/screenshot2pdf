import sys
import subprocess
from pathlib import Path
from PIL import Image
import importlib


def test_import_modules():
    # Ensure refactored modules are importable
    importlib.import_module('pdf_from_screenshots')
    importlib.import_module('pdf_tools')
    importlib.import_module('image_tools')
    importlib.import_module('io_tools')


def test_single_image_creates_pdf(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    script = project_root / 'pdf_from_screenshots.py'

    input_dir = tmp_path / 'input'
    export_dir = tmp_path / 'out'
    input_dir.mkdir()
    export_dir.mkdir()

    # create a simple white image
    img_path = input_dir / 'page1.png'
    im = Image.new('RGB', (800, 600), (255, 255, 255))
    im.save(img_path)

    out_pdf = 'result.pdf'

    completed = subprocess.run(
        [sys.executable, str(script), '-i', str(input_dir), '-o', out_pdf, '-e', str(export_dir), '--max-page-height', '0'],
        check=True,
        capture_output=True,
        text=True,
    )

    pdf_path = export_dir / out_pdf
    assert pdf_path.exists() and pdf_path.stat().st_size > 0, (
        f"PDF was not created. stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
