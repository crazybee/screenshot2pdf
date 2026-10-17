import argparse
import re
import csv
from pathlib import Path


def natural_key(path: Path):
    # find the last integer in the filename, fallback to lexicographic
    m = re.findall(r"(\d+)", path.name)
    if m:
        return (0, int(m[-1]))
    return (1, path.name)


def find_images(folder: Path):
    imgs = sorted([p for p in folder.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tif', '.tiff')], key=natural_key)
    return imgs


def parse_non_negative_int(value: str):
    v = int(value)
    if v < 0:
        raise argparse.ArgumentTypeError('Crop values must be >= 0')
    return v


def parse_positive_float(value: str):
    v = float(value)
    if v <= 0:
        raise argparse.ArgumentTypeError('DPI must be > 0')
    return v


def parse_non_negative_float(value: str):
    v = float(value)
    if v < 0:
        raise argparse.ArgumentTypeError('Value must be >= 0')
    return v


def ask_int(prompt: str, default: int = 0):
    raw = input(f'{prompt} [{default}]: ').strip()
    if raw == '':
        return default
    try:
        val = int(raw)
        return max(0, val)
    except Exception:
        m = re.search(r'-?\d+', raw)
        if m:
            try:
                return max(0, int(m.group(0)))
            except Exception:
                pass
        print(f'Invalid number "{raw}", using default {default}.')
        return default


def load_per_page_csv(csv_path: Path):
    per_page = {}
    with csv_path.open('r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'filename', 'top', 'bottom', 'left', 'right'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError('CSV must contain headers: filename,top,bottom,left,right')
        for row in reader:
            name = (row.get('filename') or '').strip()
            if not name:
                continue
            per_page[name] = (
                max(0, int(row.get('top', 0))),
                max(0, int(row.get('bottom', 0))),
                max(0, int(row.get('left', 0))),
                max(0, int(row.get('right', 0))),
            )
    return per_page
