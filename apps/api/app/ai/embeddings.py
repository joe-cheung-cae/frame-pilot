from PIL import Image
import imagehash
import numpy as np


def image_embedding(image: Image.Image) -> list[float]:
    perceptual_hash = imagehash.phash(image.convert("RGB"), hash_size=8)
    hash_bits = [1.0 if char == "1" else 0.0 for char in bin(int(str(perceptual_hash), 16))[2:].zfill(64)]
    sample = image.convert("RGB").resize((8, 8))
    values = np.asarray(sample, dtype=np.float32).reshape(-1)
    values = np.concatenate([np.asarray(hash_bits, dtype=np.float32), values])
    norm = float(np.linalg.norm(values))
    if norm == 0:
        return [0.0 for _ in values]
    return (values / norm).round(6).tolist()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    a = np.asarray(left, dtype=np.float32)
    b = np.asarray(right, dtype=np.float32)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)
