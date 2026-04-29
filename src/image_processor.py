import datetime
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Output directory for saved donor photos
_HERE     = pathlib.Path(__file__).parent
PHOTO_DIR = _HERE.parent / "output" / "donor_photos"


# Internal Utility Helpers
def _pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


# Read
def read_image(path: str) -> Image.Image:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    return Image.open(str(p)).convert("RGB")


# Save
def save_image(pil_img: Image.Image, original_path: str = "") -> pathlib.Path:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = pathlib.Path(original_path).suffix if original_path else ".jpg"
    if not ext:
        ext = ".jpg"
    dest = PHOTO_DIR / f"donor_{ts}{ext}"
    pil_img.save(str(dest))
    return dest


# Resize
def resize_image(pil_img: Image.Image, scale: float = 0.5) -> Image.Image:
    if scale <= 0:
        raise ValueError("scale must be > 0")
    w, h  = pil_img.size
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return pil_img.resize((new_w, new_h), Image.LANCZOS)


# Flip
def flip_image(pil_img: Image.Image, direction: str = "horizontal") -> Image.Image:
    flip_code = {"horizontal": 1, "vertical": 0, "both": -1}.get(direction, 1)
    bgr     = _pil_to_bgr(pil_img)
    flipped = cv2.flip(bgr, flip_code)
    return _bgr_to_pil(flipped)


# Crop
def crop_image(pil_img: Image.Image, box=None) -> Image.Image:
    if box is None:
        w, h = pil_img.size
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        box  = (left, top, left + side, top + side)
    return pil_img.crop(box)


# Grayscale
def grayscale_image(pil_img: Image.Image) -> Image.Image:
    bgr  = _pil_to_bgr(pil_img)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # single-channel -> RGB so UI can display uniformly
    return Image.fromarray(gray).convert("RGB")


# Enhance contrast
def enhance_contrast(pil_img: Image.Image, factor: float = 2.0) -> Image.Image:
    if factor < 0:
        raise ValueError("factor must be >= 0")
    return ImageEnhance.Contrast(pil_img).enhance(factor)


# All
def process_all(path: str, save: bool = False) -> dict:
    original = read_image(path)          

    results = {
        "original":  original,
        "resized":   resize_image(original),     
        "flipped":   flip_image(original),        
        "cropped":   crop_image(original),        
        "grayscale": grayscale_image(original),   
        "contrast":  enhance_contrast(original), 
    }

    if save:
        for name, img in results.items():
            PHOTO_DIR.mkdir(parents=True, exist_ok=True)
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ext  = pathlib.Path(path).suffix or ".jpg"
            dest = PHOTO_DIR / f"{name}_{ts}{ext}"
            img.save(str(dest))

    return results


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