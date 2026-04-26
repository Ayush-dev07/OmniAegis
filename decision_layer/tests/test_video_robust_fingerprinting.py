"""Tests for robust video fingerprinting architecture.

Covers:
- deterministic randomized frame sampling
- segment/profile hash extraction + quality signals
- blank-frame resistance
- video+audio evidence fusion for original vs pirated matching
"""

from __future__ import annotations

import math
import sys
import wave
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest


# Add decision_layer to path
DECISION_LAYER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

from app.fingerprinters.audio import AudioFingerprinter
from app.fingerprinters.video import VideoFingerprinter
from app.registry.manager import RegistryManager


class _FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeCollectionsResponse:
    def __init__(self, names: list[str]) -> None:
        self.collections = [_FakeCollection(n) for n in names]


class _FakePoint:
    def __init__(self, pid: int, vector: list[float], payload: dict[str, Any], score: float = 0.0) -> None:
        self.id = pid
        self.vector = vector
        self.payload = payload
        self.score = score


class _FakeQueryResponse:
    def __init__(self, points: list[_FakePoint]) -> None:
        self.points = points


class FakeQdrantClient:
    """Minimal in-memory Qdrant stub for unit tests."""

    def __init__(self) -> None:
        self._collections: dict[str, dict[int, _FakePoint]] = {}

    def get_collections(self) -> _FakeCollectionsResponse:
        return _FakeCollectionsResponse(list(self._collections.keys()))

    def create_collection(self, collection_name: str, vectors_config=None, hnsw_config=None) -> None:
        _ = vectors_config, hnsw_config
        self._collections.setdefault(collection_name, {})

    def upsert(self, collection_name: str, points: list[Any], wait: bool = False) -> None:
        _ = wait
        bucket = self._collections.setdefault(collection_name, {})
        for p in points:
            pid = int(p.id)
            vector = [float(x) for x in p.vector]
            payload = dict(p.payload or {})
            bucket[pid] = _FakePoint(pid, vector, payload)

    @staticmethod
    def _get_match_value(field_condition: Any) -> Any:
        match = getattr(field_condition, "match", None)
        if match is None:
            return None
        value = getattr(match, "value", None)
        if value is not None:
            return value
        if isinstance(match, dict):
            return match.get("value")
        return None

    @staticmethod
    def _passes_filter(payload: dict[str, Any], query_filter: Any) -> bool:
        if query_filter is None:
            return True

        must = getattr(query_filter, "must", None)
        if must is None and isinstance(query_filter, dict):
            must = query_filter.get("must")
        if not must:
            return True

        for cond in must:
            key = getattr(cond, "key", None)
            if key is None and isinstance(cond, dict):
                key = cond.get("key")
            expected = FakeQdrantClient._get_match_value(cond)
            if payload.get(str(key)) != expected:
                return False
        return True

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
        return float(np.dot(a, b) / denom)

    def query_points(
        self,
        collection_name: str,
        query: list[float],
        limit: int,
        query_filter: Any = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> _FakeQueryResponse:
        _ = with_payload, with_vectors
        q = np.asarray(query, dtype=np.float32)

        bucket = self._collections.get(collection_name, {})
        scored: list[_FakePoint] = []

        for p in bucket.values():
            if not self._passes_filter(p.payload, query_filter):
                continue
            v = np.asarray(p.vector, dtype=np.float32)
            score = self._cosine(q, v)
            scored.append(_FakePoint(p.id, p.vector, dict(p.payload), score=score))

        scored.sort(key=lambda x: x.score, reverse=True)
        return _FakeQueryResponse(scored[:limit])


def _write_synthetic_video(
    path: Path,
    *,
    fps: int = 24,
    seconds: int = 8,
    blank_every_n: int | None = None,
    style: str = "original",
) -> None:
    width, height = 96, 96
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(path), fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError("Failed to initialize video writer for tests")

    total_frames = fps * seconds
    for i in range(total_frames):
        if blank_every_n is not None and blank_every_n > 0 and i % blank_every_n == 0:
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            writer.write(frame)
            continue

        frame = np.zeros((height, width, 3), dtype=np.uint8)

        t = i / max(total_frames, 1)
        if style == "original":
            x = int((width - 20) * (0.5 + 0.5 * math.sin(2 * math.pi * t)))
            y = int((height - 20) * (0.5 + 0.5 * math.cos(2 * math.pi * t)))
            frame[:, :, 1] = np.linspace(0, 180, width, dtype=np.uint8)[None, :]
            cv2.rectangle(frame, (x, y), (x + 20, y + 20), (255, 120, 40), -1)
            cv2.circle(frame, (width // 2, height // 2), 12, (40, 220, 220), 2)
        else:
            x = int((width - 24) * (0.5 + 0.5 * math.cos(4 * math.pi * t)))
            y = int((height - 24) * (0.5 + 0.5 * math.sin(4 * math.pi * t)))
            frame[:, :, 2] = np.linspace(200, 20, width, dtype=np.uint8)[None, :]
            cv2.rectangle(frame, (x, y), (x + 24, y + 24), (30, 240, 90), -1)
            cv2.line(frame, (0, i % height), (width - 1, (i * 3) % height), (250, 250, 250), 2)

        writer.write(frame)

    writer.release()


def _write_tone_wav(
    path: Path,
    *,
    freq_hz: float | list[float],
    duration_sec: float = 6.0,
    sr: int = 22050,
    noise_std: float = 0.0,
    seed: int = 7,
) -> None:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, duration_sec, int(sr * duration_sec), endpoint=False, dtype=np.float32)
    if isinstance(freq_hz, list):
        y = np.zeros_like(t)
        if len(freq_hz) == 0:
            raise ValueError("freq_hz list must not be empty")
        step = max(len(t) // len(freq_hz), 1)
        for idx, f in enumerate(freq_hz):
            start = idx * step
            end = len(t) if idx == len(freq_hz) - 1 else min((idx + 1) * step, len(t))
            seg_t = t[start:end]
            y[start:end] = 0.35 * np.sin(2.0 * np.pi * float(f) * seg_t)
    else:
        y = 0.35 * np.sin(2.0 * np.pi * float(freq_hz) * t)

    if noise_std > 0:
        y = y + rng.normal(0.0, noise_std, size=y.shape).astype(np.float32)
    y = np.clip(y, -1.0, 1.0)

    pcm = (y * 32767.0).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _write_noise_wav(path: Path, *, duration_sec: float = 6.0, sr: int = 22050, seed: int = 17) -> None:
    rng = np.random.default_rng(seed)
    y = rng.normal(0.0, 0.25, size=int(sr * duration_sec)).astype(np.float32)
    y = np.clip(y, -1.0, 1.0)
    pcm = (y * 32767.0).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


@pytest.fixture
def robust_video_fp(monkeypatch: pytest.MonkeyPatch) -> VideoFingerprinter:
    monkeypatch.setenv("VIDEO_SAMPLING_SECRET", "test-secret-a")
    return VideoFingerprinter(
        frames_to_sample=10,
        sampling_profiles=3,
        segment_duration_sec=2.0,
        blank_std_threshold=5.0,
        blank_laplacian_threshold=6.0,
    )


def test_randomized_deterministic_sampling_and_feature_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    robust_video_fp: VideoFingerprinter,
) -> None:
    original_path = tmp_path / "original.avi"
    _write_synthetic_video(original_path, fps=24, seconds=8, style="original")

    fp1 = robust_video_fp.fingerprint(str(original_path))
    fp2 = robust_video_fp.fingerprint(str(original_path))

    # Deterministic under same secret + same content.
    assert fp1["aggregate_hash_hex"] == fp2["aggregate_hash_hex"]
    fp1_segment_sig = sorted(
        (int(r["profile_id"]), int(r["segment_idx"]), str(r["hash_hex"]))
        for r in fp1["segment_hash_records"]
    )
    fp2_segment_sig = sorted(
        (int(r["profile_id"]), int(r["segment_idx"]), str(r["hash_hex"]))
        for r in fp2["segment_hash_records"]
    )
    assert fp1_segment_sig == fp2_segment_sig

    # New architecture fields should be present.
    assert fp1["sampling_profiles"] == 3
    assert fp1["segment_count"] >= 1
    assert len(fp1["segment_hash_records"]) > 0
    assert len(fp1["profile_aggregate_records"]) > 0
    assert 0.0 <= float(fp1["quality"]["blank_ratio"]) <= 1.0
    assert 0.0 <= float(fp1["quality"]["usable_ratio"]) <= 1.0

    # Different secret should alter randomized sampling pattern/signature.
    monkeypatch.setenv("VIDEO_SAMPLING_SECRET", "test-secret-b")
    changed_secret_fp = VideoFingerprinter(
        frames_to_sample=10,
        sampling_profiles=3,
        segment_duration_sec=2.0,
    )
    fp3 = changed_secret_fp.fingerprint(str(original_path))

    # Aggregates may occasionally collide under majority voting, so verify
    # randomized sampler positions directly across secrets.
    positions_a = robust_video_fp._sample_positions(
        segment_start=0,
        segment_end=95,
        total_frames=192,
        fps=24.0,
        profile_id=1,
    )
    positions_b = changed_secret_fp._sample_positions(
        segment_start=0,
        segment_end=95,
        total_frames=192,
        fps=24.0,
        profile_id=1,
    )
    assert not np.array_equal(positions_a, positions_b)

    # Ensure changed-secret fingerprinting still produces valid structured output.
    assert len(fp3["segment_hash_records"]) > 0


def test_video_audio_evidence_original_vs_pirated(
    tmp_path: Path,
    robust_video_fp: VideoFingerprinter,
) -> None:
    # Build original, pirated (blank-frame attacked), and unrelated videos.
    original_video = tmp_path / "original.avi"
    pirated_video = tmp_path / "pirated_blank_attack.avi"
    unrelated_video = tmp_path / "unrelated.avi"

    _write_synthetic_video(original_video, fps=24, seconds=8, style="original")
    _write_synthetic_video(
        pirated_video,
        fps=24,
        seconds=8,
        style="original",
        blank_every_n=6,
    )
    _write_synthetic_video(unrelated_video, fps=24, seconds=8, style="other")

    # Build audio evidence for original vs unrelated.
    original_audio = tmp_path / "original.wav"
    pirated_audio = tmp_path / "pirated.wav"
    unrelated_audio = tmp_path / "unrelated.wav"

    _write_tone_wav(original_audio, freq_hz=[440.0, 554.37, 659.25, 493.88], noise_std=0.001, seed=11)
    _write_tone_wav(pirated_audio, freq_hz=[440.0, 554.37, 659.25, 493.88], noise_std=0.003, seed=12)
    _write_noise_wav(unrelated_audio, seed=13)

    audio_fp = AudioFingerprinter()
    registry = RegistryManager(
        audio_dim=audio_fp.embedding_dim,
        semantic_dim=512,
        qdrant_client=FakeQdrantClient(),
    )

    orig_vid_fp = robust_video_fp.fingerprint(str(original_video))
    bad_vid_fp = robust_video_fp.fingerprint(str(unrelated_video))

    registry.register_video(
        asset_id="asset_original",
        hash_bytes=orig_vid_fp["aggregate_hash_bytes"],
        hash_records=orig_vid_fp["segment_hash_records"],
        metadata={"modality": "video", "filename": "original.avi"},
    )
    registry.register_video(
        asset_id="asset_unrelated",
        hash_bytes=bad_vid_fp["aggregate_hash_bytes"],
        hash_records=bad_vid_fp["segment_hash_records"],
        metadata={"modality": "video", "filename": "unrelated.avi"},
    )

    orig_audio_fp = audio_fp.fingerprint(str(original_audio))
    bad_audio_fp = audio_fp.fingerprint(str(unrelated_audio))

    registry.register_audio(
        asset_id="asset_original",
        embedding=orig_audio_fp["embedding"],
        metadata={
            "modality": "video_audio_track",
            "parent_modality": "video",
            "filename": "original.wav",
        },
    )
    registry.register_audio(
        asset_id="asset_unrelated",
        embedding=bad_audio_fp["embedding"],
        metadata={
            "modality": "video_audio_track",
            "parent_modality": "video",
            "filename": "unrelated.wav",
        },
    )

    # Query with pirated content: should match original strongly.
    pirated_vid_fp = robust_video_fp.fingerprint(str(pirated_video))
    pirated_audio_fp = audio_fp.fingerprint(str(pirated_audio))

    assert pirated_vid_fp["quality"]["blank_ratio"] > 0.0
    assert pirated_vid_fp["quality"]["usable_frames"] > 0

    video_results = registry.match_video_robust(
        pirated_vid_fp["segment_hash_records"],
        top_k=3,
        per_record_limit=4,
        min_profile_hits=2,
        min_segment_coverage=0.1,
    )
    assert len(video_results) >= 1
    assert video_results[0].asset_id == "asset_original"

    audio_results = registry.match_audio(pirated_audio_fp["embedding"], top_k=3)
    audio_results = [
        r
        for r in audio_results
        if str(r.metadata.get("parent_modality") or "") == "video"
        or str(r.metadata.get("modality") or "") == "video_audio_track"
    ]
    assert len(audio_results) >= 1
    assert audio_results[0].asset_id == "asset_original"

    fused = RegistryManager.fuse_video_audio_matches(video_results, audio_results, top_k=3)
    assert len(fused) >= 1
    assert fused[0].asset_id == "asset_original"

    # Evidence fusion should preserve/improve ranking confidence for original.
    top_video_conf = max(r.confidence for r in video_results if r.asset_id == "asset_original")
    top_fused_conf = max(r.confidence for r in fused if r.asset_id == "asset_original")
    assert top_fused_conf >= top_video_conf

    if len(fused) > 1:
        assert fused[0].confidence >= fused[1].confidence
