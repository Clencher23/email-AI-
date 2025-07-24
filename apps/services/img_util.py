# # image_utils.py

import base64
from PIL import Image
from io import BytesIO

def compress_image_to_target_size(input_base64, target_mb=1.15, target_dimension=1568, quality=85):
    """
    Compresses a base64 image to a target size in MB while maintaining a square aspect ratio.

    Args:
        input_base64: Base64 encoded image string
        target_mb: Target size in MB (default: 1.15 MB)
        target_dimension: Target dimension for width and height in pixels (default: 1568)
        quality: Initial JPEG quality to try (default: 85)

    Returns:
        Base64 encoded compressed image string
    """
    # Decode base64 to image
    image_data = base64.b64decode(input_base64)
    image = Image.open(BytesIO(image_data))

    # Resize to target dimensions (square aspect ratio)
    image = image.resize((target_dimension, target_dimension), Image.Resampling.LANCZOS)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    min_quality = 1
    max_quality = 95
    current_quality = quality
    best_result = None
    target_bytes = int(target_mb * 1024 * 1024)
    iterations = 0
    max_iterations = 10

    while min_quality <= max_quality and iterations < max_iterations:
        iterations += 1
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=current_quality, optimize=True)
        compressed_bytes = buf.getvalue()
        if abs(len(compressed_bytes) - target_bytes) / target_bytes < 0.05:
            best_result = compressed_bytes
            break
        if len(compressed_bytes) > target_bytes:
            max_quality = current_quality - 1
        else:
            min_quality = current_quality + 1
            if best_result is None or len(compressed_bytes) > len(best_result):
                best_result = compressed_bytes
        current_quality = (min_quality + max_quality) // 2

    if best_result is None:
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=1, optimize=True)
        best_result = buf.getvalue()

    return base64.b64encode(best_result).decode("utf-8")
