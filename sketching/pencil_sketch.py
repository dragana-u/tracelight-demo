import cv2
import numpy as np


def to_grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def invert(gray):
    return 255 - gray


def gaussian_blur(img, radius):
    k = radius if radius % 2 == 1 else radius + 1
    return cv2.GaussianBlur(img, (k, k), 0)


def color_dodge(gray, blurred):
    gray_f = gray.astype(np.float32)
    blur_f = blurred.astype(np.float32)
    result = gray_f * 255.0 / (255.0 - blur_f + 1e-6)
    return np.clip(result, 0, 255).astype(np.uint8)


def run(img, blur_radius=21, intensity=1.0):
    gray = to_grayscale(img)

    inverted = invert(gray)

    blurred = gaussian_blur(inverted, blur_radius)

    sketch = color_dodge(gray, blurred)

    if intensity < 1.0:
        sketch = cv2.addWeighted(sketch, intensity, gray, 1.0 - intensity, 0)

    return {
        "original": img,
        "grayscale": gray,
        "inverted": inverted,
        "blurred": blurred,
        "sketch": sketch,
    }
