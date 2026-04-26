from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import warnings

import cv2
import numpy as np
import pytest

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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECISION_LAYER_PATH = PROJECT_ROOT / "decision_layer"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(DECISION_LAYER_PATH) not in sys.path:
    sys.path.insert(0, str(DECISION_LAYER_PATH))

pytest.importorskip("cv2")
qdrant_client = pytest.importorskip("qdrant_client")

try:
    from decision_layer.app.fingerprinters.video import VideoFingerprinter
    from decision_layer.app.registry.manager import RegistryManager
except ModuleNotFoundError:
    from decision_layer.app.fingerprinters.video import VideoFingerprinter
    from decision_layer.app.registry.manager import RegistryManager


def _create_test_video(tmp_path: Path, frames: int = 32, pattern: str = "square") -> str:
    """Create a deterministic test video with specified frames and pattern."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    video_path = str(tmp_path / f"test_{pattern}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_path, fourcc, 20.0, (256, 256))

    if writer is None or not writer.isOpened():
        raise ValueError("Failed to open VideoWriter")

    try:
        for frame_idx in range(frames):
            frame = np.ones((256, 256, 3), dtype=np.uint8) * 240

            if pattern == "square":
                offset = (frame_idx % 10) * 5
                cv2.rectangle(frame, (50 + offset, 50), (200 + offset, 200), (25, 25, 210), -1)
                cv2.circle(frame, (125 + offset, 125), 30, (250, 250, 250), -1)
            elif pattern == "stripe":
                stripe_height = 256 // 3
                cv2.rectangle(frame, (0, 0), (256, stripe_height), (40, 40, 40), -1)
                cv2.rectangle(
                    frame, (0, stripe_height), (256, 2 * stripe_height), (200, 200, 200), -1
                )
                cv2.rectangle(
                    frame,
                    (0, 2 * stripe_height),
                    (256, 256),
                    (210, 40, 40),
                    -1,
                )
            else:
                raise ValueError(f"Unsupported pattern: {pattern}")

            writer.write(frame)
    finally:
        writer.release()

    return video_path


def test_video_similarity_and_qdrant_storage_e2e(tmp_path: Path) -> None:
    """End-to-end validation: video fingerprint extraction and Qdrant storage/search."""
    fingerprinter = VideoFingerprinter(frames_to_sample=8)

    qdrant_data_dir = tmp_path / "qdrant_video"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=96,
        semantic_dim=512,
        qdrant_client=client,
        video_collection_name="video_assets_e2e_test",
    )

    try:
        base_video = _create_test_video(tmp_path, frames=32, pattern="square")
        variant_dir = tmp_path / "variant"
        variant_dir.mkdir(parents=True, exist_ok=True)
        near_dup_video = _create_test_video(variant_dir, frames=32, pattern="square")
        different_video = _create_test_video(tmp_path, frames=32, pattern="stripe")

        assert Path(base_video).exists()
        assert Path(near_dup_video).exists()
        assert Path(different_video).exists()

        base_fp = fingerprinter.fingerprint(base_video)
        near_fp = fingerprinter.fingerprint(near_dup_video)
        different_fp = fingerprinter.fingerprint(different_video)

        assert base_fp["aggregate_hash_bytes"].shape == (8,)
        assert base_fp["frames_sampled"] > 0
        assert near_fp["aggregate_hash_bytes"].shape == (8,)
        assert different_fp["aggregate_hash_bytes"].shape == (8,)

        registry.register_video(
            asset_id="video-base",
            hash_bytes=base_fp["aggregate_hash_bytes"],
            metadata={"modality": "video", "filename": "base.mp4", "pattern": "square"},
        )
        registry.register_video(
            asset_id="video-different",
            hash_bytes=different_fp["aggregate_hash_bytes"],
            metadata={"modality": "video", "filename": "different.mp4", "pattern": "stripe"},
        )

        matches = registry.match_video(near_fp["aggregate_hash_bytes"], top_k=2)
        assert matches, "Expected at least one video match"
        assert matches[0].asset_id == "video-base"
        assert matches[0].confidence > 0.5

        points, _ = client.scroll(
            collection_name="video_assets_e2e_test",
            limit=10,
            with_payload=True,
        )
        stored_asset_ids = {str(point.payload.get("asset_id")) for point in points if point.payload}
        assert stored_asset_ids == {"video-base", "video-different"}
    finally:
        client.close()


def test_video_piracy_detection_e2e(tmp_path: Path) -> None:
    """Test detecting pirated/copied videos: register original, detect modified copy as infringing."""
    fingerprinter = VideoFingerprinter(frames_to_sample=8)

    qdrant_data_dir = tmp_path / "qdrant_video_piracy"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=96,
        semantic_dim=512,
        qdrant_client=client,
        video_collection_name="copyrighted_videos",
    )

    try:
        # Original copyrighted video
        original_video = _create_test_video(tmp_path, frames=32, pattern="square")
        original_fp = fingerprinter.fingerprint(original_video)

        registry.register_video(
            asset_id="copyrighted-video-original",
            hash_bytes=original_fp["aggregate_hash_bytes"],
            metadata={
                "modality": "video",
                "filename": "copyrighted_film.mp4",
                "copyright_holder": "Studio_X",
                "registered_date": "2026-01-01",
                "type": "original",
                "frames_sampled": original_fp["frames_sampled"],
            },
        )

        # Pirated copy (same pattern, slight variation in frames)
        pirated_dir = tmp_path / "pirated"
        pirated_dir.mkdir(parents=True, exist_ok=True)
        pirated_video = _create_test_video(pirated_dir, frames=30, pattern="square")  # Slightly different frame count
        pirated_fp = fingerprinter.fingerprint(pirated_video)

        # Detect pirated video via fingerprint matching
        matches = registry.match_video(pirated_fp["aggregate_hash_bytes"], top_k=1)
        assert matches, "Video fingerprinting should detect pirated copy"
        assert matches[0].asset_id == "copyrighted-video-original"
        assert matches[0].confidence > 0.5, "Confidence indicates likely copyright infringement"
        assert matches[0].metadata.get("copyright_holder") == "Studio_X"
    finally:
        client.close()


def test_video_persistence_across_clients(tmp_path: Path) -> None:
    """Verify video data persists in Qdrant across client reconnections."""
    fingerprinter = VideoFingerprinter(frames_to_sample=4)
    qdrant_data_dir = tmp_path / "qdrant_persist"

    video_path = _create_test_video(tmp_path, frames=16, pattern="square")
    fp = fingerprinter.fingerprint(video_path)

    client1 = qdrant_client.QdrantClient(path=str(qdrant_data_dir))
    registry1 = RegistryManager(
        audio_dim=96,
        qdrant_client=client1,
        video_collection_name="video_persist_test",
    )

    registry1.register_video(
        asset_id="persist-video",
        hash_bytes=fp["aggregate_hash_bytes"],
        metadata={"modality": "video", "source": "test", "persistent": True},
    )
    client1.close()

    client2 = qdrant_client.QdrantClient(path=str(qdrant_data_dir))
    registry2 = RegistryManager(
        audio_dim=96,
        qdrant_client=client2,
        video_collection_name="video_persist_test",
    )

    matches = registry2.match_video(fp["aggregate_hash_bytes"], top_k=1)
    assert matches, "Video should persist in Qdrant after reconnection"
    assert matches[0].asset_id == "persist-video"
    assert matches[0].metadata.get("persistent") is True

    client2.close()
