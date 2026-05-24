import cv2
import numpy as np


def to_grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def smooth(gray, ksize=5):
    k = ksize if ksize % 2 == 1 else ksize + 1
    return cv2.GaussianBlur(gray, (k, k), 0)


def gradient_polar(gray):
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    magnitude = np.sqrt(gx * gx + gy * gy)

    direction = (np.degrees(np.arctan2(gy, gx)) + 180) % 180

    return magnitude, direction


def visualize_direction(magnitude, direction):
    h, w = magnitude.shape
    hsv = np.zeros((h, w, 3), dtype=np.uint8)

    hsv[..., 0] = direction.astype(np.uint8)
    hsv[..., 1] = 255
    hsv[..., 2] = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def quantize_direction(direction, n_bins=4):
    bin_width = 180.0 / n_bins
    return ((direction + bin_width / 2) // bin_width).astype(np.int32) % n_bins


def make_hatching_texture(shape, angle_deg, spacing=6, thickness=1):
    h, w = shape
    texture = np.full((h, w), 255, dtype=np.uint8)

    angle_rad = np.radians(angle_deg)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

    diag = int(np.hypot(h, w))

    for offset in range(-diag, diag, spacing):
        cx = w / 2 - sin_a * offset
        cy = h / 2 + cos_a * offset
        x1 = int(cx - cos_a * diag)
        y1 = int(cy - sin_a * diag)
        x2 = int(cx + cos_a * diag)
        y2 = int(cy + sin_a * diag)
        cv2.line(texture, (x1, y1), (x2, y2), 0, thickness)

    return texture


def run(img, smoothing=5, spacing=6, n_bins=4, threshold=30):
    gray = to_grayscale(img)

    blurred = smooth(gray, smoothing)

    magnitude, direction = gradient_polar(blurred)

    edge_orientation = (direction + 90) % 180

    quantized = quantize_direction(edge_orientation, n_bins=n_bins)

    h, w = gray.shape
    bin_angles = [(i + 0.5) * (180.0 / n_bins) for i in range(n_bins)]
    textures = [make_hatching_texture((h, w), a, spacing=spacing) for a in bin_angles]

    mag_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    edge_mask = mag_norm > threshold

    result = np.full((h, w), 255, dtype=np.uint8)
    for i, tex in enumerate(textures):
        bin_mask = (quantized == i) & edge_mask
        result[bin_mask] = tex[bin_mask]

    return {
        "original": img,
        "grayscale": gray,
        "blurred": blurred,
        "magnitude": mag_norm,
        "direction_viz": visualize_direction(magnitude, direction),
        "quantized": ((quantized.astype(np.float32) + 0.5) * (255 / n_bins)).astype(np.uint8),
        "edge_mask": edge_mask.astype(np.uint8) * 255,
        "hatched": result,
        "n_bins": n_bins,
        "spacing": spacing,
        "threshold": threshold,
        "smoothing": smoothing,
    }
