import fitz  # PyMuPDF
import base64
from PIL import Image
from io import BytesIO

def pdf_pages_to_base64_images(pdf_file, quality=85, dpi=200):
    """
    Converts each page of a PDF file to a base64-encoded JPEG image.
    Args:
        pdf_file: File-like object (already seek(0)), e.g., from Flask's upload.
        quality: JPEG quality (default 85).
        dpi: Render DPI (default 200).
    Returns:
        List of base64-encoded JPEG strings (one per page).
    """
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()

    # ✅ FIX: Use fitz.open(...) from PyMuPDF properly
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    images_base64 = []

    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        img_bytes = buf.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        images_base64.append(img_base64)

    return images_base64
