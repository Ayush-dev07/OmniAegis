from __future__ import annotations

import cv2
import numpy as np


class ImageFingerprinter:
    """256‑bit perceptual hash (pHash) for near‑duplicate image detection.

    - Output: 256‑bit fingerprint packed in 32 bytes.
    - Low‑latency: all operations are vectorized NumPy/OpenCV.
    """

    def __init__(self, hash_size: int = 16, highfreq_factor: int = 4) -> None:
        if hash_size % 8 != 0:
            raise ValueError("hash_size must be a multiple of 8")
        self.hash_size = hash_size
        self.highfreq_factor = highfreq_factor
        self.target_size = self.hash_size * self.highfreq_factor
        self._bits = self.hash_size * self.hash_size  # 256 for default

    def fingerprint_from_bytes(self, content: bytes) -> dict:
        arr = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Invalid or corrupt image file")
        return self.fingerprint(image)

    def fingerprint(self, gray_image: np.ndarray) -> dict:
        if gray_image is None or gray_image.size == 0:
            raise ValueError("Empty image data")

        if gray_image.ndim == 3:
            gray_image = cv2.cvtColor(gray_image, cv2.COLOR_BGR2GRAY)

        resized = cv2.resize(
            gray_image,
            (self.target_size, self.target_size),
            interpolation=cv2.INTER_AREA,
        )

        dct = cv2.dct(np.float32(resized))
        low_freq = dct[: self.hash_size, : self.hash_size]

        median = np.median(low_freq)
        bits = (low_freq > median).astype(np.uint8).reshape(-1)

        packed = np.packbits(bits)
        return {
            "hash_hex": packed.tobytes().hex(),
            "hash_bits": "".join(bits.astype(str)),
            "hash_bytes": packed,
            "hash_size_bits": self._bits,
        }

    def to_vector(self, fingerprint: dict) -> np.ndarray:
        """Convert fingerprint to a float32 vector (0/1) for Milvus."""
        bits = np.frombuffer(fingerprint["hash_bytes"], dtype=np.uint8)
        return np.unpackbits(bits).astype(np.float32)
    
#(Instant test)

if __name__ == "__main__":
    # 1. Initialize the fingerprinter
    fingerprinter = ImageFingerprinter()

    # 2. Provide the path to an image file
    image_path = "fingerprints/pud.jpg"  # Replace with your actual image filename

    try:
        # 3. Read the file as bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 4. Generate the fingerprint
        result = fingerprinter.fingerprint_from_bytes(image_bytes)

        # 5. Print the output
        print(f"Fingerprint for {image_path}:")
        print(f"Hex Hash:  {result['hash_hex']}")
        print(f"Bits:      {result['hash_bits']}")
        print(f"Byte Size: {len(result['hash_bytes'])} bytes")

    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")