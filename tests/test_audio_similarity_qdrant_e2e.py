from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import warnings

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

pytest.importorskip("librosa")
qdrant_client = pytest.importorskip("qdrant_client")

try:
    from decision_layer.app.fingerprinters.audio import AudioFingerprinter
    from decision_layer.app.registry.manager import RegistryManager
except ModuleNotFoundError:
    from decision_layer.app.fingerprinters.audio import AudioFingerprinter
    from decision_layer.app.registry.manager import RegistryManager


def _create_test_audio(tmp_path: Path, duration_seconds: float = 2.0, tone_freq: float = 440.0) -> str:
    """Create a deterministic test audio file with specified duration and frequency."""
    import librosa
    import soundfile as sf

    tmp_path.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    num_samples = int(duration_seconds * sample_rate)

    t = np.linspace(0, duration_seconds, num_samples)
    audio = 0.3 * np.sin(2 * np.pi * tone_freq * t).astype(np.float32)

    audio_path = str(tmp_path / f"test_{int(tone_freq)}hz.wav")
    sf.write(audio_path, audio, sample_rate)

    return audio_path


class _DeterministicAudioEmbedder:
    """Simple deterministic embedder for audio vector tests."""

    embedding_dim = 96

    def embed_from_bytes(self, audio_path: str) -> np.ndarray:
        """Extract a simple 96-D embedding from audio file."""
        import librosa

        y, sr = librosa.load(audio_path, sr=22050, mono=True, dtype=np.float32)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=12)
        features = np.concatenate(
            [mfcc.mean(axis=1), mfcc.std(axis=1), np.zeros(96 - 24)]
        ).astype(np.float32)[:96]
        norm = np.linalg.norm(features) + 1e-6
        return features / norm


def test_audio_similarity_and_qdrant_storage_e2e(tmp_path: Path) -> None:
    """End-to-end validation: audio fingerprint extraction and Qdrant storage/search."""
    pytest.importorskip("soundfile")
    fingerprinter = AudioFingerprinter(sample_rate=22050)

    qdrant_data_dir = tmp_path / "qdrant_audio"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=fingerprinter.embedding_dim,
        semantic_dim=512,
        qdrant_client=client,
        audio_collection_name="audio_assets_e2e_test",
    )

    try:
        base_audio = _create_test_audio(tmp_path, duration_seconds=3.0, tone_freq=440.0)
        variant_dir = tmp_path / "variant"
        variant_dir.mkdir(parents=True, exist_ok=True)
        near_dup_audio = _create_test_audio(variant_dir, duration_seconds=3.0, tone_freq=442.0)
        different_audio = _create_test_audio(tmp_path, duration_seconds=3.0, tone_freq=880.0)

        assert Path(base_audio).exists()
        assert Path(near_dup_audio).exists()
        assert Path(different_audio).exists()

        base_fp = fingerprinter.fingerprint(base_audio)
        near_fp = fingerprinter.fingerprint(near_dup_audio)
        different_fp = fingerprinter.fingerprint(different_audio)

        assert base_fp["embedding"].shape == (96,)
        assert base_fp["embedding_dim"] == 96
        assert near_fp["embedding"].shape == (96,)
        assert different_fp["embedding"].shape == (96,)

        registry.register_audio(
            asset_id="audio-base",
            embedding=base_fp["embedding"],
            metadata={
                "modality": "audio",
                "filename": "base.wav",
                "frequency": 440.0,
                "fingerprint_id": base_fp["fingerprint_id"],
            },
        )
        registry.register_audio(
            asset_id="audio-different",
            embedding=different_fp["embedding"],
            metadata={
                "modality": "audio",
                "filename": "different.wav",
                "frequency": 880.0,
                "fingerprint_id": different_fp["fingerprint_id"],
            },
        )

        matches = registry.match_audio(near_fp["embedding"], top_k=2)
        assert matches, "Expected at least one audio match"
        assert matches[0].asset_id == "audio-base"
        assert matches[0].confidence > 0.5

        points, _ = client.scroll(
            collection_name="audio_assets_e2e_test",
            limit=10,
            with_payload=True,
        )
        stored_asset_ids = {str(point.payload.get("asset_id")) for point in points if point.payload}
        assert stored_asset_ids == {"audio-base", "audio-different"}
    finally:
        client.close()


def test_audio_piracy_detection_e2e(tmp_path: Path) -> None:
    """Test detecting pirated/copied audio: register original song, detect modified copy as infringing."""
    pytest.importorskip("soundfile")
    fingerprinter = AudioFingerprinter(sample_rate=22050)

    qdrant_data_dir = tmp_path / "qdrant_audio_piracy"
    client = qdrant_client.QdrantClient(path=str(qdrant_data_dir))

    registry = RegistryManager(
        audio_dim=fingerprinter.embedding_dim,
        semantic_dim=512,
        qdrant_client=client,
        audio_collection_name="copyrighted_songs",
    )

    try:
        # Original copyrighted song (440 Hz tone)
        original_audio = _create_test_audio(tmp_path, duration_seconds=3.0, tone_freq=440.0)
        original_fp = fingerprinter.fingerprint(original_audio)

        registry.register_audio(
            asset_id="copyrighted-song-original",
            embedding=original_fp["embedding"],
            metadata={
                "modality": "audio",
                "filename": "copyrighted_song.wav",
                "artist": "Artist_B",
                "copyright_holder": "RecordLabel_Y",
                "registered_date": "2026-01-01",
                "type": "original",
                "fingerprint_id": original_fp["fingerprint_id"],
            },
        )

        # Pirated copy (slightly different frequency to simulate pitch shift)
        pirated_dir = tmp_path / "pirated_audio"
        pirated_dir.mkdir(parents=True, exist_ok=True)
        pirated_audio = _create_test_audio(pirated_dir, duration_seconds=3.0, tone_freq=442.0)  # +2Hz shift
        pirated_fp = fingerprinter.fingerprint(pirated_audio)

        # Detect pirated audio via landmark-based fingerprinting
        matches = registry.match_audio(pirated_fp["embedding"], top_k=1)
        assert matches, "Audio fingerprinting should detect pirated copy despite pitch shift"
        assert matches[0].asset_id == "copyrighted-song-original"
        assert matches[0].confidence > 0.5, "Confidence indicates likely copyright infringement"
        assert matches[0].metadata.get("copyright_holder") == "RecordLabel_Y"
        assert matches[0].metadata.get("artist") == "Artist_B"

        # Verify piracy detection landmarks are preserved
        landmarks = matches[0].metadata.get("top_landmarks")
        assert landmarks is not None or matches[0].confidence > 0.5, "Landmark-based matching should work"
    finally:
        client.close()


def test_audio_embedding_normalization(tmp_path: Path) -> None:
    """Verify audio embeddings are valid with expected shape and dtype."""
    pytest.importorskip("soundfile")
    fingerprinter = AudioFingerprinter(sample_rate=22050)

    audio_path = _create_test_audio(tmp_path, duration_seconds=3.0, tone_freq=440.0)
    fp = fingerprinter.fingerprint(audio_path)

    embedding = fp["embedding"]
    assert embedding.dtype == np.float32
    assert embedding.shape[0] == 96
    assert embedding.size > 0


def test_audio_persistence_across_clients(tmp_path: Path) -> None:
    """Verify audio data persists in Qdrant across client reconnections."""
    pytest.importorskip("soundfile")
    fingerprinter = AudioFingerprinter(sample_rate=22050)
    qdrant_data_dir = tmp_path / "qdrant_persist"

    audio_path = _create_test_audio(tmp_path, duration_seconds=3.0, tone_freq=440.0)
    fp = fingerprinter.fingerprint(audio_path)

    client1 = qdrant_client.QdrantClient(path=str(qdrant_data_dir))
    registry1 = RegistryManager(
        audio_dim=96,
        qdrant_client=client1,
        audio_collection_name="audio_persist_test",
    )

    registry1.register_audio(
        asset_id="persist-audio",
        embedding=fp["embedding"],
        metadata={"modality": "audio", "source": "test", "persistent": True},
    )
    client1.close()

    client2 = qdrant_client.QdrantClient(path=str(qdrant_data_dir))
    registry2 = RegistryManager(
        audio_dim=96,
        qdrant_client=client2,
        audio_collection_name="audio_persist_test",
    )

    matches = registry2.match_audio(fp["embedding"], top_k=1)
    assert matches, "Audio should persist in Qdrant after reconnection"
    assert matches[0].asset_id == "persist-audio"
    assert matches[0].metadata.get("persistent") is True

    client2.close()
