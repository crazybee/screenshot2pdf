from pathlib import Path
from PIL import Image, ImageFilter

try:
    # Pillow 9+ exposes Resampling
    if hasattr(Image, 'Resampling'):
        RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    else:
        RESAMPLE_LANCZOS = Image.LANCZOS
except Exception:
    RESAMPLE_LANCZOS = Image.LANCZOS


def crop_by_pixels(img: Image.Image, top: int, bottom: int, left: int, right: int):
    w, h = img.size
    x1 = max(0, left)
    y1 = max(0, top)
    x2 = min(w, w - max(0, right))
    y2 = min(h, h - max(0, bottom))
    if x2 <= x1 or y2 <= y1:
        return img
    return img.crop((x1, y1, x2, y2))


def get_image_dpi(img: Image.Image):
    dpi = img.info.get('dpi')
    if dpi is None:
        return None
    if isinstance(dpi, (tuple, list)):
        if len(dpi) >= 2:
            return float(dpi[0]), float(dpi[1])
        if len(dpi) == 1:
            val = float(dpi[0])
            return val, val
    try:
        val = float(dpi)
        return val, val
    except (TypeError, ValueError):
        return None


def resolve_pdf_dpi(images, override_dpi=None):
    if override_dpi is not None:
        return float(override_dpi)

    dpis = []
    for img in images:
        dpi = get_image_dpi(img)
        if dpi is not None:
            dpis.append(max(float(dpi[0]), float(dpi[1])))

    base_dpi = max(dpis) if dpis else 300.0
    return max(base_dpi, 300.0)


def split_image_vertically(img: Image.Image, max_height: int):
    if max_height <= 0 or img.size[1] <= max_height:
        return [img]

    w, h = img.size
    pieces = []
    y = 0
    while y < h:
        y2 = min(h, y + max_height)
        part = img.crop((0, y, w, y2))
        dpi = img.info.get('dpi')
        if dpi is not None:
            part.info['dpi'] = dpi
        pieces.append(part)
        y = y2
    return pieces


def compute_effective_page_height(width: int, requested_max_height: int):
    if requested_max_height <= 0:
        return 0
    max_megapixels_per_page = 12_000_000
    limit_by_pixels = max(2000, max_megapixels_per_page // max(1, width))
    return max(2000, min(requested_max_height, limit_by_pixels))


def apply_text_sharpen(img: Image.Image, strength: float):
    if strength <= 0:
        return img
    percent = int(min(500, max(80, 100 + (strength * 120))))
    return img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=percent, threshold=2))


def restore_width_for_readability(img: Image.Image, target_width: int):
    if target_width <= 0 or img.size[0] >= target_width:
        return img
    scale = target_width / img.size[0]
    new_height = max(1, int(round(img.size[1] * scale)))
    restored = img.resize((target_width, new_height), resample=RESAMPLE_LANCZOS)
    dpi = img.info.get('dpi')
    if dpi is not None:
        restored.info['dpi'] = dpi
    return restored


def mm_to_px(mm: float, dpi: float):
    return max(1, int(round((mm / 25.4) * dpi)))


def paper_size_to_pixels(paper_size: str, dpi: float):
    size = paper_size.lower()
    if size == 'a4':
        return mm_to_px(210.0, dpi), mm_to_px(297.0, dpi)
    if size == 'letter':
        return mm_to_px(215.9, dpi), mm_to_px(279.4, dpi)
    return None


def fit_image_to_paper(img: Image.Image, paper_width: int, paper_height: int, margin_px: int):
    content_w = max(1, paper_width - (2 * margin_px))
    content_h = max(1, paper_height - (2 * margin_px))
    src_w, src_h = img.size

    # Fill the printable width of the page to avoid left/right whitespace. The
    # input image is assumed to already be split into page-sized vertical chunks,
    # so a width-based fit is the correct behavior for A4 printing.
    scale = content_w / src_w
    target_w = max(1, int(round(src_w * scale)))
    target_h = max(1, int(round(src_h * scale)))
    if target_h > content_h:
        scale = content_h / src_h
        target_h = max(1, int(round(src_h * scale)))
        target_w = max(1, int(round(src_w * scale)))

    if (target_w, target_h) == img.size:
        fitted = img.copy()
    else:
        fitted = img.resize((target_w, target_h), resample=RESAMPLE_LANCZOS)
    page = Image.new('RGB', (paper_width, paper_height), (255, 255, 255))
    offset_x = (paper_width - target_w) // 2
    offset_y = (paper_height - target_h) // 2
    if target_w >= paper_width - 2:
        offset_x = 0
    page.paste(fitted, (offset_x, offset_y))
    dpi = img.info.get('dpi')
    if dpi is not None:
        page.info['dpi'] = dpi
    return page


def prepare_images_for_paper(images, dpi: float, paper_size: str, margin_mm: float):
    paper_pixels = paper_size_to_pixels(paper_size, dpi)
    if paper_pixels is None:
        return images
    page_w, page_h = paper_pixels
    margin_px = mm_to_px(margin_mm, dpi)
    max_margin = (min(page_w, page_h) // 2) - 1
    margin_px = max(0, min(margin_px, max(0, max_margin)))
    printable_w = max(1, page_w - (2 * margin_px))
    printable_h = max(1, page_h - (2 * margin_px))

    resized = []
    for img in images:
        src_w, src_h = img.size
        if src_w <= 1 or src_h <= 1:
            resized.append(fit_image_to_paper(img, page_w, page_h, margin_px))
            continue
        safe_piece_height = max(1, int(round((printable_h * src_w) / max(1, printable_w))))
        pieces = split_image_vertically(img, safe_piece_height)
        resized.extend(fit_image_to_paper(piece, page_w, page_h, margin_px) for piece in pieces)
    return resized
