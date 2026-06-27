# devlang/img/__init__.py — Image / vision stubs

def imread(path):
    return {"type": "image", "path": str(path), "status": "loaded", "width": 640, "height": 480}


def imwrite(path, img):
    return f"Saved image to {path}"


def blur(img, k):
    if isinstance(img, dict):
        return {**img, "status": f"blurred({k})"}
    return img


def grayscale(img):
    if isinstance(img, dict):
        return {**img, "status": "grayscale"}
    return img


def resize(img, w, h):
    if isinstance(img, dict):
        return {**img, "status": f"resized({w}x{h})", "width": int(w), "height": int(h)}
    return img


def rotate(img, angle):
    if isinstance(img, dict):
        return {**img, "status": f"rotated({angle}deg)"}
    return img


def threshold(img, val):
    if isinstance(img, dict):
        return {**img, "status": f"threshold({val})"}
    return img


def canny(img):
    if isinstance(img, dict):
        return {**img, "status": "edges(canny)"}
    return img
