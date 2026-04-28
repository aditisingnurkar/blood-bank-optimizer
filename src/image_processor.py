"""
HEMATIX — Image Processor
Core image processing logic for Assignment 9.
Zero tkinter / UI code — pure PIL + OpenCV functions only.

All functions accept a PIL.Image.Image and return a PIL.Image.Image
so the UI layer (_PhotoTab) can display results without knowing internals.

Operations covered:
  Op 1  read_image()       — load image from file path -> PIL Image
  Op 2  (display handled by UI layer)
  Op 3  save_image()       — save PIL Image to output folder with timestamp
  Op 4  resize_image()     — resize to given scale factor (default 0.5 = half)
  Op 5  flip_image()       — horizontal flip via OpenCV
  Op 6  crop_image()       — centre-square crop via PIL
  Op 7  grayscale_image()  — BGR -> GRAY via OpenCV, returned as RGB PIL Image
  Op 8  enhance_contrast() — PIL ImageEnhance.Contrast with configurable factor
"""

import datetime
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Output directory for saved donor photos
_HERE     = pathlib.Path(__file__).parent
PHOTO_DIR = _HERE.parent / "output" / "donor_photos"


# ══════════════════════════════════════════════════════════════════════════
# INTERNAL UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to OpenCV BGR ndarray."""
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR ndarray to PIL RGB image."""
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


# ══════════════════════════════════════════════════════════════════════════
# Op 1 — READ
# ══════════════════════════════════════════════════════════════════════════

def read_image(path: str) -> Image.Image:
    """
    Op 1: Read an image from disk using PIL.
    Returns a PIL Image in RGB mode.
    Raises FileNotFoundError if path does not exist.
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    return Image.open(str(p)).convert("RGB")


# ══════════════════════════════════════════════════════════════════════════
# Op 3 — SAVE
# ══════════════════════════════════════════════════════════════════════════

def save_image(pil_img: Image.Image, original_path: str = "") -> pathlib.Path:
    """
    Op 3: Save the image with a new timestamped filename.
    Saves into PHOTO_DIR (output/donor_photos/).
    Returns the full path of the saved file.
    """
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = pathlib.Path(original_path).suffix if original_path else ".jpg"
    if not ext:
        ext = ".jpg"
    dest = PHOTO_DIR / f"donor_{ts}{ext}"
    pil_img.save(str(dest))
    return dest


# ══════════════════════════════════════════════════════════════════════════
# Op 4 — RESIZE
# ══════════════════════════════════════════════════════════════════════════

def resize_image(pil_img: Image.Image, scale: float = 0.5) -> Image.Image:
    """
    Op 4: Resize image by a scale factor using PIL.
    Default scale=0.5 produces a half-size image.
    Returns a new PIL Image.
    """
    if scale <= 0:
        raise ValueError("scale must be > 0")
    w, h  = pil_img.size
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return pil_img.resize((new_w, new_h), Image.LANCZOS)


# ══════════════════════════════════════════════════════════════════════════
# Op 5 — FLIP
# ══════════════════════════════════════════════════════════════════════════

def flip_image(pil_img: Image.Image, direction: str = "horizontal") -> Image.Image:
    """
    Op 5: Flip image using OpenCV cv2.flip().
    direction: 'horizontal' (default) | 'vertical' | 'both'
    Returns a new PIL Image.
    """
    flip_code = {"horizontal": 1, "vertical": 0, "both": -1}.get(direction, 1)
    bgr     = _pil_to_bgr(pil_img)
    flipped = cv2.flip(bgr, flip_code)
    return _bgr_to_pil(flipped)


# ══════════════════════════════════════════════════════════════════════════
# Op 6 — CROP
# ══════════════════════════════════════════════════════════════════════════

def crop_image(pil_img: Image.Image, box=None) -> Image.Image:
    """
    Op 6: Crop image using PIL .crop().
    box: (left, top, right, bottom) in pixels.
         If None, crops a centre square (min dimension x min dimension).
    Returns a new PIL Image.
    """
    if box is None:
        w, h = pil_img.size
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        box  = (left, top, left + side, top + side)
    return pil_img.crop(box)


# ══════════════════════════════════════════════════════════════════════════
# Op 7 — GRAYSCALE
# ══════════════════════════════════════════════════════════════════════════

def grayscale_image(pil_img: Image.Image) -> Image.Image:
    """
    Op 7: Convert image to grayscale using OpenCV cv2.COLOR_BGR2GRAY.
    Returns a new PIL Image in RGB mode (greyscale tones, displayable directly).
    """
    bgr  = _pil_to_bgr(pil_img)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # single-channel -> RGB so UI can display uniformly
    return Image.fromarray(gray).convert("RGB")


# ══════════════════════════════════════════════════════════════════════════
# Op 8 — ENHANCE CONTRAST
# ══════════════════════════════════════════════════════════════════════════

def enhance_contrast(pil_img: Image.Image, factor: float = 2.0) -> Image.Image:
    """
    Op 8: Enhance image contrast using PIL ImageEnhance.Contrast.
    factor = 1.0  -> original
    factor > 1.0  -> higher contrast  (default 2.0)
    factor < 1.0  -> lower  contrast
    Returns a new PIL Image.
    """
    if factor < 0:
        raise ValueError("factor must be >= 0")
    return ImageEnhance.Contrast(pil_img).enhance(factor)


# ══════════════════════════════════════════════════════════════════════════
# CONVENIENCE — run all ops at once (batch / testing)
# ══════════════════════════════════════════════════════════════════════════

def process_all(path: str, save: bool = False) -> dict:
    """
    Run all 8 operations on the image at `path`.
    Returns a dict mapping operation name -> result PIL Image.
    If save=True, each result is also written to PHOTO_DIR.
    """
    original = read_image(path)          # Op 1

    results = {
        "original":  original,
        "resized":   resize_image(original),      # Op 4
        "flipped":   flip_image(original),        # Op 5
        "cropped":   crop_image(original),        # Op 6
        "grayscale": grayscale_image(original),   # Op 7
        "contrast":  enhance_contrast(original),  # Op 8
    }
    # Op 2 = display; handled by whoever calls this function
    # Op 3 = save below

    if save:
        for name, img in results.items():
            PHOTO_DIR.mkdir(parents=True, exist_ok=True)
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ext  = pathlib.Path(path).suffix or ".jpg"
            dest = PHOTO_DIR / f"{name}_{ts}{ext}"
            img.save(str(dest))

    return results


# ══════════════════════════════════════════════════════════════════════════
# QUICK SELF-TEST  (python image_processor.py <path_to_image>)
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_processor.py <image_path>")
        sys.exit(1)

    src = sys.argv[1]
    print(f"Running all ops on: {src}\n")
    out = process_all(src, save=True)
    for op, img in out.items():
        print(f"  {op:12s}  ->  {img.size[0]}x{img.size[1]}  mode={img.mode}")
    print(f"\nAll results saved to: {PHOTO_DIR}")