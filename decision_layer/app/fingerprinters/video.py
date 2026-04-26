from __future__ import annotations

import hashlib
import math
import os

import cv2
import numpy as np

from .image import ImageFingerprinter


class VideoFingerprinter:
    """Robust video fingerprinting with randomized multi-profile segment hashing.

    Defense-in-depth features:
    - randomized deterministic sampling positions (seeded by secret salt)
    - multiple sampling profiles per segment
    - segment-level hashes for coverage-aware matching
    - low-information/blank frame suppression
    - compact aggregate hashes for backward compatibility
    """

    def __init__(
        self,
        frames_to_sample: int = 16,
        sampling_profiles: int = 3,
        segment_duration_sec: float = 10.0,
        blank_std_threshold: float = 6.0,
        blank_laplacian_threshold: float = 8.0,
    ) -> None:
        self.frames_to_sample = frames_to_sample
        self.sampling_profiles = max(int(sampling_profiles), 1)
        self.segment_duration_sec = max(float(segment_duration_sec), 1.0)
        self.blank_std_threshold = float(blank_std_threshold)
        self.blank_laplacian_threshold = float(blank_laplacian_threshold)
        self.sampling_secret = os.getenv("VIDEO_SAMPLING_SECRET", "omniaegis-video-seed")
        self.image_fingerprinter = ImageFingerprinter()

    @staticmethod
    def _stable_seed(*parts: object) -> int:
        payload = "|".join(str(p) for p in parts).encode("utf-8")
        digest = hashlib.sha256(payload).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    @staticmethod
    def _majority_hash(hash_rows: list[np.ndarray]) -> np.ndarray:
        bits_matrix = np.vstack([np.unpackbits(h) for h in hash_rows])
        majority_bits = (bits_matrix.mean(axis=0) >= 0.5).astype(np.uint8)
        return np.packbits(majority_bits)

    def _sample_positions(
        self,
        *,
        segment_start: int,
        segment_end: int,
        total_frames: int,
        fps: float,
        profile_id: int,
    ) -> np.ndarray:
        if total_frames <= 0:
            raise ValueError("Video has no readable frames")

        if segment_end < segment_start:
            return np.array([], dtype=int)

        candidates = np.arange(segment_start, segment_end + 1, dtype=int)
        if candidates.size == 0:
            return candidates

        sample_count = min(self.frames_to_sample, int(candidates.size))
        if sample_count <= 0:
            return np.array([], dtype=int)

        seed = self._stable_seed(
            self.sampling_secret,
            total_frames,
            int(round(fps * 1000.0)),
            segment_start,
            segment_end,
            profile_id,
        )
        rng = np.random.default_rng(seed)

        if sample_count >= candidates.size:
            return candidates

        selection = rng.choice(candidates.size, size=sample_count, replace=False)
        return np.sort(candidates[selection])

    def _is_low_information_frame(self, frame: np.ndarray) -> bool:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        std = float(np.std(gray))
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        mean = float(np.mean(gray))

        if std < self.blank_std_threshold and lap_var < self.blank_laplacian_threshold:
            return True

        # Near-solid black/white frame guard.
        if std < self.blank_std_threshold and (mean < 6.0 or mean > 249.0):
            return True

        return False

    def fingerprint(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Invalid or corrupt video file")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_hashes_hex: list[str] = []
            segment_hash_records: list[dict] = []
            profile_aggregate_records: list[dict] = []
            profile_segment_hashes: dict[int, list[np.ndarray]] = {p: [] for p in range(self.sampling_profiles)}

            decoded_frames = 0
            blank_frames = 0
            usable_frames = 0

            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if not np.isfinite(fps) or fps <= 1e-6:
                fps = 25.0

            if total_frames <= 0:
                raise ValueError("Video has no readable frames")

            segment_span = max(int(round(self.segment_duration_sec * fps)), 1)
            segment_count = int(math.ceil(total_frames / segment_span))

            for segment_idx in range(segment_count):
                start_frame = segment_idx * segment_span
                end_frame = min(total_frames - 1, ((segment_idx + 1) * segment_span) - 1)

                for profile_id in range(self.sampling_profiles):
                    positions = self._sample_positions(
                        segment_start=start_frame,
                        segment_end=end_frame,
                        total_frames=total_frames,
                        fps=fps,
                        profile_id=profile_id,
                    )

                    sampled_hashes: list[np.ndarray] = []
                    for pos in positions:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
                        ok, frame = cap.read()
                        if not ok or frame is None:
                            continue

                        decoded_frames += 1
                        if self._is_low_information_frame(frame):
                            blank_frames += 1
                            continue

                        usable_frames += 1
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        fp = self.image_fingerprinter.fingerprint(gray)
                        frame_hashes_hex.append(fp["hash_hex"])
                        sampled_hashes.append(fp["hash_bytes"])

                    if not sampled_hashes:
                        continue

                    segment_hash = self._majority_hash(sampled_hashes)
                    profile_segment_hashes[profile_id].append(segment_hash)

                    segment_hash_records.append(
                        {
                            "profile_id": profile_id,
                            "segment_idx": segment_idx,
                            "segment_start_sec": float(start_frame / fps),
                            "segment_end_sec": float((end_frame + 1) / fps),
                            "hash_hex": segment_hash.tobytes().hex(),
                            "hash_bytes": segment_hash,
                        }
                    )

            if not segment_hash_records:
                raise ValueError("No valid non-blank frames could be decoded")

            for profile_id, hashes in profile_segment_hashes.items():
                if not hashes:
                    continue
                profile_hash = self._majority_hash(hashes)
                profile_aggregate_records.append(
                    {
                        "profile_id": profile_id,
                        "hash_hex": profile_hash.tobytes().hex(),
                        "hash_bytes": profile_hash,
                    }
                )

            if not profile_aggregate_records:
                raise ValueError("Failed to generate stable profile aggregate hashes")

            aggregate_bytes = self._majority_hash([p["hash_bytes"] for p in profile_aggregate_records])
            aggregate_bits = np.unpackbits(aggregate_bytes).astype(np.uint8)
            blank_ratio = float(blank_frames / max(decoded_frames, 1))
            usable_ratio = float(usable_frames / max(decoded_frames, 1))

            return {
                "frames_sampled": len(frame_hashes_hex),
                "frame_hashes": frame_hashes_hex,
                "segment_count": segment_count,
                "sampling_profiles": self.sampling_profiles,
                "segment_duration_sec": self.segment_duration_sec,
                "segment_hash_records": segment_hash_records,
                "profile_aggregate_records": profile_aggregate_records,
                "aggregate_hash_hex": aggregate_bytes.tobytes().hex(),
                "aggregate_hash_bits": "".join(aggregate_bits.astype(str)),
                "aggregate_hash_bytes": aggregate_bytes,
                "hash_size_bits": 64,
                "quality": {
                    "decoded_frames": int(decoded_frames),
                    "usable_frames": int(usable_frames),
                    "blank_or_lowinfo_frames": int(blank_frames),
                    "blank_ratio": blank_ratio,
                    "usable_ratio": usable_ratio,
                },
            }
        finally:
            cap.release()
