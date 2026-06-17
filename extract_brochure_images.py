"""
Jatin Electronics Brochure - Professional Image Extraction
Extracts all images at maximum native resolution using PyMuPDF.

Strategy:
  1. Extract ALL embedded raster images at their native resolution (no resampling)
  2. Render each page at 600 DPI for composite/vector elements and crop precisely
  3. Name files descriptively based on content
"""

import fitz  # PyMuPDF
import os
from PIL import Image
import io

PDF_PATH = r"F:\Claude Code\Jatin Electronics Website\Jatin Electronics Brochure.pdf"
OUT_DIR  = r"F:\Claude Code\Jatin Electronics Website\Brochure Images Extracted"
os.makedirs(OUT_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Extract every embedded raster image at its native resolution
# ──────────────────────────────────────────────────────────────────────────────
# Map: xref → filename  (used later to skip duplicates in page renders)
print("=" * 60)
print("STEP 1: Extracting native embedded images")
print("=" * 60)

# Descriptive names keyed by (page_index, image_order_on_page)
# Determined by visual inspection of the brochure.
PAGE_IMAGE_NAMES = {
    # Page 1 — Cover
    (0, 0): "01_cover_jatin-plaza-building-exterior",
    (0, 1): "02_cover_showroom-interior-front-view",
    (0, 2): "03_cover_warehouse-floor-with-counters",
    (0, 3): "04_cover_assembly-line-display-area",
    (0, 4): "05_cover_large-production-hall",

    # Page 2 — Who We Are
    (1, 0): "06_who-we-are_electronics-wiring-close-up",

    # Page 3 — Products & Services
    (2, 0): "07_products_wire-harness-assembly-bundle",
    (2, 1): "08_products_electrical-connectors-and-terminals",
    (2, 2): "09_products_smps-transformer-yellow-core",
    (2, 3): "10_products_current-transformer-toroidal",
    (2, 4): "11_products_base-assembly-module-pcb-box",
    (2, 5): "12_products_speciality-communication-cables",

    # Page 4 — Achievements & Clients
    (3, 0): "13_achievements_zero-defect-star-award-badge",
    (3, 1): "14_achievements_iso-9001-2015-certificate",
    (3, 2): "15_clients_handshake-logo",
}

saved_xrefs = set()
image_counters = {}  # page_index → counter

for page_index in range(len(doc)):
    page = doc[page_index]
    image_list = page.get_images(full=True)
    image_counters[page_index] = 0

    for img_info in image_list:
        xref = img_info[0]

        # Skip duplicate xrefs (same image referenced on multiple pages)
        if xref in saved_xrefs:
            continue
        saved_xrefs.add(xref)

        order = image_counters[page_index]
        image_counters[page_index] += 1

        # Build output filename
        key = (page_index, order)
        base_name = PAGE_IMAGE_NAMES.get(key, f"page{page_index+1:02d}_img{order:02d}_unknown")
        out_path = os.path.join(OUT_DIR, base_name + ".png")

        # Extract image bytes
        try:
            base_image = doc.extract_image(xref)
            img_bytes  = base_image["image"]
            img_ext    = base_image["ext"]   # jpeg / png / etc.
            img_width  = base_image["width"]
            img_height = base_image["height"]

            # Load with Pillow and save as high-quality PNG (lossless)
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # Save PNG at maximum quality (lossless, no compression artefacts)
            pil_img.save(out_path, "PNG", optimize=False, compress_level=1)

            print(f"  ✓ {base_name}.png  ({img_width}×{img_height} px, native {img_ext.upper()})")

        except Exception as e:
            print(f"  ✗ xref {xref} failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Render full pages at 600 DPI for logos, icons, and composite crops
# ──────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 2: Rendering pages at 600 DPI for vector/composite crops")
print("=" * 60)

DPI = 600
SCALE = DPI / 72  # PDF points → pixels

def crop_and_save(page_render: Image.Image, page_w_pt: float, page_h_pt: float,
                  rel_rect: tuple, filename: str):
    """
    rel_rect = (left%, top%, right%, bottom%) as 0.0–1.0 fractions of page size.
    Crops from the rendered page image and saves to OUT_DIR.
    """
    pw, ph = page_render.size
    x0 = int(rel_rect[0] * pw)
    y0 = int(rel_rect[1] * ph)
    x1 = int(rel_rect[2] * pw)
    y1 = int(rel_rect[3] * ph)
    cropped = page_render.crop((x0, y0, x1, y1))
    out_path = os.path.join(OUT_DIR, filename + ".png")
    cropped.save(out_path, "PNG", optimize=False, compress_level=1)
    print(f"  ✓ {filename}.png  ({cropped.width}×{cropped.height} px)")


# ── Page 1 (index 0) — Cover ──────────────────────────────────────────────────
p0 = doc[0]
mat0 = fitz.Matrix(SCALE, SCALE)
pix0 = p0.get_pixmap(matrix=mat0, alpha=False)
img0 = Image.frombytes("RGB", [pix0.width, pix0.height], pix0.samples)
W0, H0 = p0.rect.width, p0.rect.height

# JE Logo (top-left circular logo)
crop_and_save(img0, W0, H0, (0.03, 0.03, 0.25, 0.14),
              "00a_logo_JE-circular-badge")

# Jatin Electronics wordmark
crop_and_save(img0, W0, H0, (0.27, 0.03, 0.80, 0.14),
              "00b_logo_jatin-electronics-wordmark")

# Full combined logo lockup
crop_and_save(img0, W0, H0, (0.03, 0.03, 0.80, 0.14),
              "00c_logo_full-lockup-JE-plus-wordmark")

# Building exterior (large hero photo)
crop_and_save(img0, W0, H0, (0.02, 0.14, 0.98, 0.57),
              "01_cover_jatin-plaza-building-exterior-CROPPED")

# Showroom interior - front view (bottom-left)
crop_and_save(img0, W0, H0, (0.02, 0.57, 0.50, 0.73),
              "02_cover_showroom-interior-front-view-CROPPED")

# Warehouse with counters (bottom-right)
crop_and_save(img0, W0, H0, (0.51, 0.57, 0.98, 0.73),
              "03_cover_warehouse-floor-with-counters-CROPPED")

# Assembly / display area (bottom-left second row)
crop_and_save(img0, W0, H0, (0.02, 0.74, 0.50, 0.91),
              "04_cover_assembly-line-display-area-CROPPED")

# Large production hall (bottom-right second row)
crop_and_save(img0, W0, H0, (0.51, 0.74, 0.98, 0.91),
              "05_cover_large-production-hall-CROPPED")


# ── Page 2 (index 1) — Who We Are ────────────────────────────────────────────
p1 = doc[1]
pix1 = p1.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
img1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)
W1, H1 = p1.rect.width, p1.rect.height

# Hero background — hands wiring electronics
crop_and_save(img1, W1, H1, (0.00, 0.03, 1.00, 0.48),
              "06_who-we-are_electronics-wiring-close-up-CROPPED")

# Three info-card icons (Background / Values / Goals)
crop_and_save(img1, W1, H1, (0.02, 0.47, 0.34, 0.58),
              "07a_who-we-are_icon-background-circuit-board")
crop_and_save(img1, W1, H1, (0.35, 0.47, 0.66, 0.58),
              "07b_who-we-are_icon-values-network")
crop_and_save(img1, W1, H1, (0.67, 0.47, 0.98, 0.58),
              "07c_who-we-are_icon-goals-checklist")


# ── Page 3 (index 2) — Products & Services ───────────────────────────────────
p2 = doc[2]
pix2 = p2.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
img2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples)
W2, H2 = p2.rect.width, p2.rect.height

# Wire harness bundle (large left top)
crop_and_save(img2, W2, H2, (0.02, 0.08, 0.50, 0.38),
              "08_products_wire-harness-assembly-bundle-CROPPED")

# Electrical connectors & terminals (top right)
crop_and_save(img2, W2, H2, (0.52, 0.08, 0.98, 0.26),
              "09_products_electrical-connectors-and-terminals-CROPPED")

# SMPS Transformer — yellow ferrite core (middle right top)
crop_and_save(img2, W2, H2, (0.52, 0.27, 0.75, 0.40),
              "10_products_smps-transformer-yellow-ferrite-core-CROPPED")

# Current Transformer — toroidal black (middle right bottom)
crop_and_save(img2, W2, H2, (0.76, 0.27, 0.98, 0.40),
              "11_products_current-transformer-toroidal-black-CROPPED")

# Base Assembly Module — PCB in enclosure box (large bottom left)
crop_and_save(img2, W2, H2, (0.02, 0.40, 0.50, 0.71),
              "12_products_base-assembly-module-pcb-enclosure-CROPPED")

# Speciality Communication Cables (bottom right)
crop_and_save(img2, W2, H2, (0.52, 0.40, 0.98, 0.71),
              "13_products_speciality-communication-cables-rj45-usb-CROPPED")


# ── Page 4 (index 3) — Achievements & Clients ────────────────────────────────
p3 = doc[3]
pix3 = p3.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
img3 = Image.frombytes("RGB", [pix3.width, pix3.height], pix3.samples)
W3, H3 = p3.rect.width, p3.rect.height

# Zero Defect star award badge
crop_and_save(img3, W3, H3, (0.03, 0.06, 0.28, 0.22),
              "14_achievements_zero-defect-product-star-badge")

# ISO 9001:2015 Certificate (right panel)
crop_and_save(img3, W3, H3, (0.38, 0.02, 0.98, 0.56),
              "15_achievements_iso-9001-2015-certificate-registration")

# Clients handshake icon
crop_and_save(img3, W3, H3, (0.03, 0.52, 0.25, 0.62),
              "16_clients_handshake-partnership-icon")

# Full page render (archival — all 4 pages)
print()
print("=" * 60)
print("STEP 3: Saving full-page 600 DPI archival renders")
print("=" * 60)
for page_index in range(len(doc)):
    page = doc[page_index]
    pix  = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    fname = f"FULLPAGE_{page_index+1:02d}_brochure-page-{page_index+1}-at-600dpi"
    out_path = os.path.join(OUT_DIR, fname + ".png")
    img.save(out_path, "PNG", optimize=False, compress_level=1)
    print(f"  ✓ {fname}.png  ({img.width}×{img.height} px)")

doc.close()

print()
print("=" * 60)
files = [f for f in os.listdir(OUT_DIR) if f.endswith(".png")]
total_mb = sum(os.path.getsize(os.path.join(OUT_DIR, f)) for f in files) / 1_048_576
print(f"DONE — {len(files)} images saved to:")
print(f"  {OUT_DIR}")
print(f"  Total size: {total_mb:.1f} MB")
print("=" * 60)
