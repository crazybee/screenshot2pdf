#!/usr/bin/env python3
"""
Crop screenshots by explicit pixel values and merge into one PDF.
Defaults to A4-sized pages for predictable printing.
Generic usage for sequential screenshot sets.
Requires: pillow (pip install pillow)
Recommended for best quality: img2pdf (pip install img2pdf)

Examples:
  python pdf_from_screenshots.py -i ./pdf/901 -o exam_901.pdf -e ./exports --top 120 --bottom 90 --left 220 --right 220
  python pdf_from_screenshots.py --interactive-per-page
"""

import argparse
from pathlib import Path
from PIL import Image

# Split functionality into modules for maintainability
from pdf_tools import (
    natural_key,
    find_images,
    parse_non_negative_int,
    parse_positive_float,
    parse_non_negative_float,
    ask_int,
    load_per_page_csv,
)
from image_tools import (
    crop_by_pixels,
    get_image_dpi,
    resolve_pdf_dpi,
    split_image_vertically,
    compute_effective_page_height,
    apply_text_sharpen,
    restore_width_for_readability,
    prepare_images_for_paper,
)
from io_tools import save_high_res_pdf


def main():
    parser = argparse.ArgumentParser(description='Crop screenshots by exact pixel values and merge to PDF')
    parser.add_argument('-i', '--input-folder', type=str, help='Folder containing sequential screenshot images')
    parser.add_argument('-o', '--output-filename', type=str, help='Final PDF filename (e.g. exam.pdf)')
    parser.add_argument('-e', '--export-folder', type=str, help='Folder to write the final PDF into')
    parser.add_argument('--top', type=parse_non_negative_int, help='Pixels to remove from top')
    parser.add_argument('--bottom', type=parse_non_negative_int, help='Pixels to remove from bottom')
    parser.add_argument('--left', type=parse_non_negative_int, help='Pixels to remove from left')
    parser.add_argument('--right', type=parse_non_negative_int, help='Pixels to remove from right')
    parser.add_argument('--interactive-per-page', action='store_true', help='Prompt top/bottom/left/right for each image')
    parser.add_argument('--crop-csv', type=str, help='CSV with filename,top,bottom,left,right for per-image cropping')
    parser.add_argument('--dpi', type=parse_positive_float, help='PDF output DPI. Defaults to the source image DPI or 300 if unavailable')
    parser.add_argument('--max-page-height', type=parse_non_negative_int, default=8000, help='Split very tall images into multiple PDF pages at this pixel height (0 disables split)')
    parser.add_argument('--sharpen', type=parse_non_negative_float, default=0.0, help='Mild text sharpening strength for screenshots (0 disables)')
    parser.add_argument('--restore-width', action=argparse.BooleanOptionalAction, default=True, help='Upscale cropped pages back to original width before PDF export to keep text crisp')
    parser.add_argument('--paper-size', type=str, choices=('a4', 'letter', 'original'), default='a4', help='Output paper size. Defaults to A4 for print-ready PDFs')
    parser.add_argument('--paper-margin-mm', type=parse_non_negative_float, default=5.0, help='Margin used when fitting content to paper pages (ignored with --paper-size original)')
    args = parser.parse_args()

    # Interactive prompts if missing
    if not args.input_folder:
        args.input_folder = input('Input folder with images: ').strip() or '.'
    if not args.output_filename:
        args.output_filename = input('Output PDF filename (e.g. exam.pdf): ').strip() or 'output.pdf'
    if not args.export_folder:
        args.export_folder = input('Export folder (where PDF will be saved): ').strip() or '.'

    input_folder = Path(args.input_folder).expanduser().resolve()
    export_folder = Path(args.export_folder).expanduser().resolve()
    output_filename = args.output_filename
    if not output_filename.lower().endswith('.pdf'):
        output_filename = output_filename + '.pdf'

    if not input_folder.exists() or not input_folder.is_dir():
        print(f'Error: input folder does not exist: {input_folder}')
        return
    export_folder.mkdir(parents=True, exist_ok=True)

    image_paths = find_images(input_folder)
    if not image_paths:
        print(f'No images found in {input_folder}. Supported extensions: png,jpg,jpeg,tif,tiff')
        return

    print(f'Found {len(image_paths)} image(s). Preparing manual crop values...')
    default_top = args.top if args.top is not None else 0
    default_bottom = args.bottom if args.bottom is not None else 0
    default_left = args.left if args.left is not None else 0
    default_right = args.right if args.right is not None else 0

    per_page_csv = {}
    if args.crop_csv:
        csv_path = Path(args.crop_csv).expanduser().resolve()
        if not csv_path.exists():
            print(f'Error: crop CSV does not exist: {csv_path}')
            return
        try:
            per_page_csv = load_per_page_csv(csv_path)
        except Exception as e:
            print(f'Error reading crop CSV: {e}')
            return

    if (
        args.top is None
        and args.bottom is None
        and args.left is None
        and args.right is None
        and not args.interactive_per_page
        and not args.crop_csv
    ):
        default_top = ask_int('Pixels to remove from TOP', 0)
        default_bottom = ask_int('Pixels to remove from BOTTOM', 0)
        default_left = ask_int('Pixels to remove from LEFT', 0)
        default_right = ask_int('Pixels to remove from RIGHT', 0)

    if not args.interactive_per_page:
        print(f'Using default crop (top={default_top}, bottom={default_bottom}, left={default_left}, right={default_right}) unless overridden by CSV.')

    final_images = []
    total_splits = 0
    for p in image_paths:
        with Image.open(p) as im:
            source_dpi = get_image_dpi(im)
            source_width = im.size[0]
            if im.mode in ('RGBA', 'LA'):
                bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode not in ('RGB', 'L', 'P', 'CMYK', 'YCbCr'):
                im = im.convert('RGB')
            if source_dpi is not None:
                im.info['dpi'] = source_dpi

            top = default_top
            bottom = default_bottom
            left = default_left
            right = default_right

            if p.name in per_page_csv:
                top, bottom, left, right = per_page_csv[p.name]

            if args.interactive_per_page:
                print(f'\n{p.name} ({im.size[0]}x{im.size[1]})')
                top = ask_int('  TOP', top)
                bottom = ask_int('  BOTTOM', bottom)
                left = ask_int('  LEFT', left)
                right = ask_int('  RIGHT', right)

            im = crop_by_pixels(im, top, bottom, left, right)
            if im.size[0] <= 1 or im.size[1] <= 1:
                print(f'Warning: crop too aggressive for {p.name}; using original image for this page.')
                with Image.open(p) as original:
                    original_dpi = get_image_dpi(original)
                    if original.mode in ('RGBA', 'LA'):
                        bg = Image.new('RGB', original.size, (255, 255, 255))
                        bg.paste(original, mask=original.split()[-1])
                        im = bg
                    elif original.mode not in ('RGB', 'L', 'P', 'CMYK', 'YCbCr'):
                        im = original.convert('RGB')
                    else:
                        im = original.copy()
                    if original_dpi is not None:
                        im.info['dpi'] = original_dpi
            else:
                if im.mode not in ('RGB', 'L', 'P', 'CMYK', 'YCbCr'):
                    im = im.convert('RGB')
                if source_dpi is not None:
                    im.info['dpi'] = source_dpi

            effective_max_height = compute_effective_page_height(im.size[0], args.max_page_height)
            pieces = split_image_vertically(im, effective_max_height)
            if args.restore_width and im.size[0] < source_width:
                pieces = [restore_width_for_readability(piece, source_width) for piece in pieces]
            if args.sharpen > 0:
                pieces = [apply_text_sharpen(piece, args.sharpen) for piece in pieces]
            total_splits += max(0, len(pieces) - 1)
            final_images.extend(pieces)

    if total_splits > 0:
        print(f'Split tall screenshots into {total_splits} additional page(s) for sharper rendering in PDF viewers.')
    if args.restore_width:
        print('Restored cropped page width to original screenshot width to prevent viewer upscaling blur.')
    if args.sharpen > 0:
        print(f'Applied mild text sharpening (strength={args.sharpen}).')

    pdf_dpi = resolve_pdf_dpi(final_images, args.dpi)
    for img in final_images:
        img.info['dpi'] = (pdf_dpi, pdf_dpi)
    final_images = prepare_images_for_paper(final_images, pdf_dpi, args.paper_size, args.paper_margin_mm)
    for img in final_images:
        img.info['dpi'] = (pdf_dpi, pdf_dpi)
    print(f'Using PDF DPI {pdf_dpi:.1f} without crop-dependent DPI downscaling.')
    if args.paper_size != 'original':
        print(f'Fitting pages to {args.paper_size.upper()} with {args.paper_margin_mm:.1f} mm margin for consistent printing.')
    else:
        print('Keeping original image page size (no paper fitting).')

    out_path = export_folder / output_filename
    print(f'Saving PDF to {out_path} ...')
    if not save_high_res_pdf(final_images, out_path, pdf_dpi):
        return

    print('Done. PDF created:', out_path)


if __name__ == '__main__':
    main()
