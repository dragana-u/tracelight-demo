import cv2
import numpy as np


def to_grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def smooth(gray, ksize=5):
    k = ksize if ksize % 2 == 1 else ksize + 1
    return cv2.GaussianBlur(gray, (k, k), 0)


def sobel(gray, ksize=3):
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)

    magnitude = cv2.magnitude(grad_x, grad_y)
    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

    return grad_x, grad_y, magnitude.astype(np.uint8)


def laplacian(gray, ksize=3):
    k = ksize if ksize % 2 == 1 else ksize + 1

    lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=k)

    return cv2.convertScaleAbs(lap)


def canny(gray, low=50, high=150):
    return cv2.Canny(gray, low, high)


def run(img, method="Sobel", ksize=3, low=50, high=150, smoothing=5):
    gray = to_grayscale(img)

    blurred = smooth(gray, smoothing)

    result = {
        "original": img,
        "grayscale": gray,
        "blurred": blurred,
        "method": method,
        "smoothing": smoothing,
    }

    if method == "Sobel":
        grad_x, grad_y, edges = sobel(blurred, ksize=ksize)
        result["grad_x"] = cv2.convertScaleAbs(grad_x)
        result["grad_y"] = cv2.convertScaleAbs(grad_y)
        result["edges"] = edges
        result["ksize"] = ksize

    elif method == "Laplacian":
        result["edges"] = laplacian(blurred, ksize=ksize)
        result["ksize"] = ksize

    elif method == "Canny":
        result["edges"] = canny(blurred, low=low, high=high)
        result["low"] = low
        result["high"] = high

    return result
