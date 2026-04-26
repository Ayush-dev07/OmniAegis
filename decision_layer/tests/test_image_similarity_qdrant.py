from __future__ import annotations

from io import BytesIO
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest
from PIL import Image, ImageDraw


# Add decision_layer to path for direct module imports.
DECISION_LAYER_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

cv2 = pytest.importorskip("cv2")
qdrant_client = pytest.importorskip("qdrant_client")

_IMAGE_MODULE_PATH = DECISION_LAYER_PATH / "app" / "fingerprinters" / "image.py"
_IMAGE_SPEC = importlib.util.spec_from_file_location("image_fingerprinter_module", _IMAGE_MODULE_PATH)
assert _IMAGE_SPEC is not None and _IMAGE_SPEC.loader is not None
_IMAGE_MODULE = importlib.util.module_from_spec(_IMAGE_SPEC)
_IMAGE_SPEC.loader.exec_module(_IMAGE_MODULE)
ImageFingerprinter = _IMAGE_MODULE.ImageFingerprinter

from app.registry.manager import RegistryManager


def _make_test_image(
    *,
    accent_shift: int = 0,
    accent_color: tuple[int, int, int] = (20, 20, 220),
    pattern: str = "square",
) -> bytes:
    """Create a compact RGB test image as in-memory PNG bytes."""

    image = Image.new("RGB", (128, 128), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)

    # Deterministic content with a small shift to simulate near-duplicate inputs.
    if pattern == "square":
        draw.rectangle((28 + accent_shift, 28, 100 + accent_shift, 100), fill=accent_color)
        draw.ellipse((44 + accent_shift, 44, 84 + accent_shift, 84), fill=(250, 250, 250))
    elif pattern == "stripe":
        draw.rectangle((18, 18, 110, 46), fill=(40, 40, 40))
        draw.rectangle((18, 54, 110, 82), fill=(200, 200, 200))
        draw.rectangle((18, 90, 110, 110), fill=accent_color)
    else:
        raise ValueError(f"Unsupported pattern: {pattern}")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class _DeterministicSemanticEmbedder:
    """Lightweight 512D image embedder for end-to-end Qdrant integration tests."""

    embedding_dim = 512

    def embed_from_bytes(self, content: bytes) -> dict[str, np.ndarray | int]:
        image = Image.open(BytesIO(content)).convert("L")
        resized = image.resize((32, 16), Image.Resampling.BILINEAR)
        vector = np.asarray(resized, dtype=np.float32).reshape(-1)
        vector = (vector - vector.mean()) / (vector.std() + 1e-6)
        norm = np.linalg.norm(vector) + 1e-6
        vector = (vector / norm).astype(np.float32)
        return {"embedding": vector, "embedding_dim": self.embedding_dim}


def _hamming_distance(bits_a: str, bits_b: str) -> int:
    return sum(ch_a != ch_b for ch_a, ch_b in zip(bits_a, bits_b, strict=True))


def test_image_similarity_and_qdrant_roundtrip(tmp_path: Path) -> None:
    """End-to-end image similarity and Qdrant persistence test."""

    image_fp = ImageFingerprinter()
    embedder = _DeterministicSemanticEmbedder()

    qdrant_path = tmp_path / "qdrant"
    client = qdrant_client.QdrantClient(path=str(qdrant_path))
    registry = RegistryManager(
        audio_dim=8,
        semantic_dim=embedder.embedding_dim,
        qdrant_client=client,
        semantic_collection_name="semantic_assets_test",
    )

    try:
        base_content = _make_test_image(accent_shift=0, accent_color=(20, 20, 220))
        near_duplicate_content = _make_test_image(accent_shift=2, accent_color=(24, 24, 224))
        different_content = _make_test_image(pattern="stripe", accent_color=(220, 40, 40))

        base_hash = image_fp.fingerprint_from_bytes(base_content)
        near_hash = image_fp.fingerprint_from_bytes(near_duplicate_content)
        different_hash = image_fp.fingerprint_from_bytes(different_content)

        # Perceptual hash should place the near-duplicate closer than the unrelated image.
        assert _hamming_distance(base_hash["hash_bits"], near_hash["hash_bits"]) <= _hamming_distance(
            base_hash["hash_bits"], different_hash["hash_bits"]
        )

        registry.register_image(
            asset_id="asset-base",
            hash_bytes=base_hash["hash_bytes"],
            metadata={"modality": "image", "filename": "base.png"},
        )
        registry.register_image(
            asset_id="asset-different",
            hash_bytes=different_hash["hash_bytes"],
            metadata={"modality": "image", "filename": "different.png"},
        )

        image_matches = registry.match_image(near_hash["hash_bytes"], top_k=2)
        assert image_matches, "Expected at least one pHash match"
        assert image_matches[0].asset_id == "asset-base"
        assert image_matches[0].confidence >= image_matches[-1].confidence

        base_embedding = embedder.embed_from_bytes(base_content)
        near_embedding = embedder.embed_from_bytes(near_duplicate_content)
        different_embedding = embedder.embed_from_bytes(different_content)

        registry.register_semantic(
            asset_id="asset-base",
            embedding=base_embedding["embedding"],
            metadata={"modality": "image", "source": "base.png", "semantic_embedding_dim": 512},
        )
        registry.register_semantic(
            asset_id="asset-different",
            embedding=different_embedding["embedding"],
            metadata={"modality": "image", "source": "different.png", "semantic_embedding_dim": 512},
        )

        semantic_matches = registry.match_semantic(
            near_embedding["embedding"],
            top_k=2,
            modality_filter="image",
        )
        assert semantic_matches, "Expected at least one semantic match"
        assert semantic_matches[0].asset_id == "asset-base"
        assert semantic_matches[0].metadata["modality"] == "image"
        assert semantic_matches[0].metadata["source"] == "base.png"

        # Validate the vector is actually persisted in Qdrant and retrievable by collection query.
        points, _ = client.scroll(collection_name="semantic_assets_test", limit=10, with_payload=True)
        stored_asset_ids = {str(point.payload.get("asset_id")) for point in points if point.payload}
        assert stored_asset_ids == {"asset-base", "asset-different"}
    finally:
        client.close()
