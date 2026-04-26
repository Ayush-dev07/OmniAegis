from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import warnings

import numpy as np
import pytest
from PIL import Image, ImageDraw


warnings.filterwarnings(
    "ignore",
    message="builtin type SwigPyPacked has no __module__ attribute",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message="builtin type SwigPyObject has no __module__ attribute",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message="builtin type swigvarlink has no __module__ attribute",
    category=DeprecationWarning,
)


pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:builtin type SwigPyPacked has no __module__ attribute:DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:builtin type SwigPyObject has no __module__ attribute:DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:builtin type swigvarlink has no __module__ attribute:DeprecationWarning"
    ),
]


# Make imports robust regardless of where pytest is launched from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECISION_LAYER_PATH = PROJECT_ROOT / "decision_layer"

# Needed for `import decision_layer...`
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Needed for `import app...` (modules under decision_layer/app)
if str(DECISION_LAYER_PATH) not in sys.path:
    sys.path.insert(0, str(DECISION_LAYER_PATH))

pytest.importorskip("cv2")
qdrant_client = pytest.importorskip("qdrant_client")

try:
    from decision_layer.app.fingerprinters.image import ImageFingerprinter
    from decision_layer.app.registry.manager import RegistryManager
except ModuleNotFoundError:
    from decision_layer.app.fingerprinters.image import ImageFingerprinter
    from decision_layer.app.registry.manager import RegistryManager


def _make_test_image(
    *,
    accent_shift: int = 0,
    accent_color: tuple[int, int, int] = (25, 25, 210),
    pattern: str = "square",
) -> bytes:
    """Create deterministic RGB PNG bytes for similarity tests."""
    image = Image.new("RGB", (128, 128), color=(238, 238, 238))
    draw = ImageDraw.Draw(image)

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


class _DeterministicImageEmbedder:
    """Simple deterministic 512-D embedder for E2E semantic matching tests."""

    embedding_dim = 512

    def embed_from_bytes(self, content: bytes) -> np.ndarray:
        image = Image.open(BytesIO(content)).convert("L")
        # 32 x 16 -> 512 values
        resized = image.resize((32, 16), Image.Resampling.BILINEAR)
        vector = np.asarray(resized, dtype=np.float32).reshape(-1)
        vector = (vector - vector.mean()) / (vector.std() + 1e-6)
        vector = vector / (np.linalg.norm(vector) + 1e-6)
        return vector.astype(np.float32)


def _hamming_distance(bits_a: str, bits_b: str) -> int:
    return sum(a != b for a, b in zip(bits_a, bits_b, strict=True))


def test_image_similarity_and_qdrant_embedding_storage_e2e(tmp_path: Path) -> None:
    """End-to-end validation: image fingerprint similarity + Qdrant semantic storage/search."""
    fingerprinter = ImageFingerprinter()
    embedder = _DeterministicImageEmbedder()

    qdrant_data_dir = tmp_path / "qdrant_local"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=8,
        semantic_dim=embedder.embedding_dim,
        qdrant_client=client,
        semantic_collection_name="semantic_assets_e2e_test",
    )

    try:
        base_image = _make_test_image(accent_shift=0, accent_color=(25, 25, 210))
        near_dup_image = _make_test_image(accent_shift=2, accent_color=(28, 28, 214))
        different_image = _make_test_image(pattern="stripe", accent_color=(210, 40, 40))

        base_hash = fingerprinter.fingerprint_from_bytes(base_image)
        near_hash = fingerprinter.fingerprint_from_bytes(near_dup_image)
        different_hash = fingerprinter.fingerprint_from_bytes(different_image)

        # Perceptual hash should rank near duplicate as more similar than unrelated image.
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

        base_embedding = embedder.embed_from_bytes(base_image)
        near_embedding = embedder.embed_from_bytes(near_dup_image)
        different_embedding = embedder.embed_from_bytes(different_image)

        assert base_embedding.shape == (512,)
        assert near_embedding.shape == (512,)

        registry.register_semantic(
            asset_id="asset-base",
            embedding=base_embedding,
            metadata={"modality": "image", "source": "base.png", "semantic_embedding_dim": 512},
        )
        registry.register_semantic(
            asset_id="asset-different",
            embedding=different_embedding,
            metadata={"modality": "image", "source": "different.png", "semantic_embedding_dim": 512},
        )

        semantic_matches = registry.match_semantic(
            near_embedding,
            top_k=2,
            modality_filter="image",
        )
        assert semantic_matches, "Expected at least one semantic match"
        assert semantic_matches[0].asset_id == "asset-base"
        assert semantic_matches[0].metadata.get("modality") == "image"
        assert semantic_matches[0].metadata.get("source") == "base.png"

        # Validate vectors are persisted in Qdrant.
        points, _ = client.scroll(
            collection_name="semantic_assets_e2e_test",
            limit=10,
            with_payload=True,
        )
        stored_asset_ids = {str(point.payload.get("asset_id")) for point in points if point.payload}
        assert stored_asset_ids == {"asset-base", "asset-different"}
    finally:
        client.close()


def test_image_piracy_detection_e2e(tmp_path: Path) -> None:
    """Test detecting pirated/copied images: register original, detect modified copy as infringing."""
    fingerprinter = ImageFingerprinter()
    embedder = _DeterministicImageEmbedder()

    qdrant_data_dir = tmp_path / "qdrant_piracy"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=8,
        semantic_dim=embedder.embedding_dim,
        qdrant_client=client,
        image_collection_name="copyrighted_images",
        semantic_collection_name="semantic_assets_piracy_test",
    )

    try:
        # Original copyrighted work
        original_image = _make_test_image(accent_shift=0, accent_color=(25, 25, 210))
        original_hash = fingerprinter.fingerprint_from_bytes(original_image)
        original_embedding = embedder.embed_from_bytes(original_image)

        registry.register_image(
            asset_id="copyrighted-original",
            hash_bytes=original_hash["hash_bytes"],
            metadata={
                "modality": "image",
                "filename": "copyrighted_artwork.png",
                "copyright_holder": "Artist_A",
                "registered_date": "2026-01-01",
                "type": "original",
            },
        )
        registry.register_semantic(
            asset_id="copyrighted-original",
            embedding=original_embedding,
            metadata={
                "modality": "image",
                "source": "copyrighted_artwork.png",
                "type": "original",
            },
        )

        # Pirated copy (small modifications to evade detection)
        pirated_copy_1 = _make_test_image(accent_shift=1, accent_color=(26, 26, 211))  # Minor color shift
        pirated_hash_1 = fingerprinter.fingerprint_from_bytes(pirated_copy_1)
        pirated_embedding_1 = embedder.embed_from_bytes(pirated_copy_1)

        # Pirated copy (more modifications)
        pirated_copy_2 = _make_test_image(accent_shift=3, accent_color=(30, 30, 215))  # Larger shift
        pirated_hash_2 = fingerprinter.fingerprint_from_bytes(pirated_copy_2)
        pirated_embedding_2 = embedder.embed_from_bytes(pirated_copy_2)

        # Detect pirated copy 1 via pHash (perceptual hash for quick detection)
        phash_matches_1 = registry.match_image(pirated_hash_1["hash_bytes"], top_k=1)
        assert phash_matches_1, "pHash should detect pirated copy (near-duplicate detection)"
        assert phash_matches_1[0].asset_id == "copyrighted-original"
        assert phash_matches_1[0].confidence > 0.5, "Confidence should indicate likely infringement"

        # Detect pirated copy 1 via semantic similarity (semantic matching)
        semantic_matches_1 = registry.match_semantic(
            pirated_embedding_1,
            top_k=1,
            modality_filter="image",
        )
        assert semantic_matches_1, "Semantic search should detect pirated copy"
        assert semantic_matches_1[0].asset_id == "copyrighted-original"
        assert semantic_matches_1[0].confidence > 0.5

        # Detect pirated copy 2 via both methods
        phash_matches_2 = registry.match_image(pirated_hash_2["hash_bytes"], top_k=1)
        assert phash_matches_2, "pHash should detect even with more modifications"
        assert phash_matches_2[0].asset_id == "copyrighted-original"

        semantic_matches_2 = registry.match_semantic(pirated_embedding_2, top_k=1, modality_filter="image")
        assert semantic_matches_2, "Semantic similarity should detect modified copies"
        assert semantic_matches_2[0].asset_id == "copyrighted-original"

        # Verify registered original is in database
        points, _ = client.scroll(collection_name="copyrighted_images", limit=10, with_payload=True)
        copyright_holder = points[0].payload.get("copyright_holder") if points else None
        assert copyright_holder == "Artist_A", "Original copyright metadata should be preserved"
    finally:
        client.close()
