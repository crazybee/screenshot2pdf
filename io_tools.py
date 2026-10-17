from pathlib import Path
import tempfile

from image_tools import get_image_dpi

try:
    import img2pdf
except Exception:  # pragma: no cover
    img2pdf = None


def save_high_res_pdf(images, out_path: Path, dpi: float):
    if img2pdf is not None:
        temp_dir = Path(tempfile.mkdtemp(prefix='pdf_from_screenshots_'))
        temp_files = []
        try:
            for idx, img in enumerate(images):
                temp_path = temp_dir / f'page_{idx:04d}.png'
                img_dpi = get_image_dpi(img)
                if img_dpi is None:
                    img_dpi = (dpi, dpi)
                img.save(temp_path, format='PNG', dpi=img_dpi, optimize=False)
                temp_files.append(str(temp_path))
            with out_path.open('wb') as fp:
                fp.write(img2pdf.convert(temp_files))
            return True
        finally:
            for temp_path in temp_files:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass
            try:
                temp_dir.rmdir()
            except Exception:
                pass

    try:
        first, rest = images[0], images[1:]
        first.info['dpi'] = (dpi, dpi)
        for image in rest:
            image.info['dpi'] = (dpi, dpi)
        first.save(out_path, 'PDF', resolution=dpi, save_all=True, append_images=rest, quality=100)
        return True
    except Exception as e:
        print('Error writing PDF:', e)
        return False
