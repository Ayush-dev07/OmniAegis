from __future__ import annotations

import subprocess
import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

#from .image import ImageFingerprinter

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

logger = logging.getLogger(__name__)


class VideoFingerprinter:
    """Segment‑based video fingerprinting using ffmpeg and 256‑bit pHash."""

    def __init__(
        self,
        frames_to_sample: int = 16,            # kept for backwards compatibility (whole video)
        hash_size: int = 16,                   # 256‑bit pHash
        segment_duration: float = 10.0,        # seconds
        step_duration: float = 2.0,            # overlap step
        frame_interval: float = 0.5,           # time between sampled frames inside a segment
    ) -> None:
        self.frames_to_sample = frames_to_sample
        self.image_fingerprinter = ImageFingerprinter(hash_size=hash_size)
        self.segment_duration = segment_duration
        self.step_duration = step_duration
        self.frame_interval = frame_interval

    # ------------------------------------------------------------------
    #  FFmpeg‑based accurate frame grab
    # ------------------------------------------------------------------
    def _grab_frame_at_time(self, video_path: str, time_sec: float) -> Optional[np.ndarray]:
        """Return a gray‑scale frame at exactly *time_sec* using ffmpeg seek."""
        try:
            cmd = [
                "ffmpeg",
                "-ss", str(time_sec),      # fast seek (before -i)
                "-i", video_path,
                "-vframes", "1",
                "-f", "image2pipe",
                "-vcodec", "mjpeg",
                "-q:v", "2",               # high quality
                "-loglevel", "error",
                "-",
            ]
            proc = subprocess.run(cmd, capture_output=True, timeout=10)
            if proc.returncode != 0 or not proc.stdout:
                logger.warning("ffmpeg failed at t=%.2f: %s", time_sec, proc.stderr.decode(errors="ignore"))
                return None
            arr = np.frombuffer(proc.stdout, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            return img
        except Exception as e:
            logger.warning("Exception grabbing frame at %.2f: %s", time_sec, e)
            return None

    # ------------------------------------------------------------------
    #  Segment fingerprinting
    # ------------------------------------------------------------------
    def fingerprint_segments(self, video_path: str) -> dict:
        """Return fingerprints for sliding segments of the video."""
        duration = self._get_video_duration(video_path)
        if duration is None or duration <= 0:
            raise ValueError("Cannot determine video duration")

        segments = []
        start = 0.0
        while start + self.segment_duration <= duration:
            end = start + self.segment_duration
            seg_hash = self._hash_segment(video_path, start, end)
            segments.append({
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "hash_hex": seg_hash["hash_hex"],
                "hash_bytes": seg_hash["hash_bytes"],
                "hash_size_bits": seg_hash["hash_size_bits"],
                "num_frames_sampled": seg_hash["num_frames"],
            })
            start += self.step_duration

        # Last partial segment if step leaves a tail
        if start < duration:
            seg_hash = self._hash_segment(video_path, start, duration)
            segments.append({
                "start_sec": round(start, 2),
                "end_sec": round(duration, 2),
                "hash_hex": seg_hash["hash_hex"],
                "hash_bytes": seg_hash["hash_bytes"],
                "hash_size_bits": seg_hash["hash_size_bits"],
                "num_frames_sampled": seg_hash["num_frames"],
            })

        return {
            "video_path": video_path,
            "duration_sec": duration,
            "segment_duration": self.segment_duration,
            "step_duration": self.step_duration,
            "frame_interval": self.frame_interval,
            "segments": segments,
        }

    def _hash_segment(self, video_path: str, t_start: float, t_end: float) -> dict:
        """Compute 256‑bit aggregate hash for a single time segment."""
        times = np.arange(t_start, t_end, self.frame_interval)
        frame_hashes_bytes = []

        for t in times:
            frame = self._grab_frame_at_time(video_path, t)
            if frame is None:
                continue
            fp = self.image_fingerprinter.fingerprint(frame)
            frame_hashes_bytes.append(fp["hash_bytes"])

        if not frame_hashes_bytes:
            raise RuntimeError(f"No valid frames in segment [{t_start:.1f}-{t_end:.1f}]")

        # Majority vote across frame hashes
        bits_matrix = np.vstack([np.unpackbits(h) for h in frame_hashes_bytes])
        majority_bits = (bits_matrix.mean(axis=0) >= 0.5).astype(np.uint8)
        aggregate_bytes = np.packbits(majority_bits)

        return {
            "hash_hex": aggregate_bytes.tobytes().hex(),
            "hash_bytes": aggregate_bytes,
            "hash_size_bits": self.image_fingerprinter._bits,
            "num_frames": len(frame_hashes_bytes),
        }

    @staticmethod
    def _get_video_duration(video_path: str) -> Optional[float]:
        """Obtain duration in seconds via ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
            out = subprocess.check_output(cmd, timeout=10).decode().strip()
            return float(out) if out else None
        except Exception as e:
            logger.warning("ffprobe failed: %s", e)
            return None

    # ------------------------------------------------------------------
    #  Legacy: whole‑video fingerprint (preserved for backwards compat)
    # ------------------------------------------------------------------
    def fingerprint(self, video_path: str) -> dict:
        """Original full‑video fingerprint using evenly spaced frames (deprecated)."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Invalid or corrupt video file")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            positions = self._safe_frame_positions(total_frames)

            frame_hashes_hex: list[str] = []
            frame_hash_bytes: list[np.ndarray] = []

            for pos in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                fp = self.image_fingerprinter.fingerprint(gray)
                frame_hashes_hex.append(fp["hash_hex"])
                frame_hash_bytes.append(fp["hash_bytes"])

            if not frame_hash_bytes:
                raise ValueError("No valid frames could be decoded")

            bits_matrix = np.vstack([np.unpackbits(h) for h in frame_hash_bytes])
            majority_bits = (bits_matrix.mean(axis=0) >= 0.5).astype(np.uint8)
            aggregate_bytes = np.packbits(majority_bits)

            return {
                "frames_sampled": len(frame_hashes_hex),
                "frame_hashes": frame_hashes_hex,
                "aggregate_hash_hex": aggregate_bytes.tobytes().hex(),
                "aggregate_hash_bits": "".join(majority_bits.astype(str)),
                "aggregate_hash_bytes": aggregate_bytes,
                "hash_size_bits": self.image_fingerprinter._bits,
            }
        finally:
            cap.release()

    def _safe_frame_positions(self, total_frames: int) -> np.ndarray:
        if total_frames <= 0:
            raise ValueError("Video has no readable frames")
        if total_frames < self.frames_to_sample:
            return np.linspace(0, total_frames - 1, total_frames, dtype=int)
        return np.linspace(0, total_frames - 1, self.frames_to_sample, dtype=int)
    
# Instant test

if __name__ == "__main__":
    # 1. Initialize with specific segment parameters
    # This will create a fingerprint every 2 seconds for a 10-second window
    video_tool = VideoFingerprinter(
        segment_duration=10.0, 
        step_duration=2.0, 
        hash_size=16  # This produces a 256-bit hash
    )

    video_file_path = "initial_matching_phase/fingerprints/6145681-uhd_2160_3840_24fps.mp4"

    try:
        # 2. Use the NEW segment-based method
        print(f"Analyzing segments for: {video_file_path}...")
        results = video_tool.fingerprint_segments(video_file_path)

        # 3. Print the video overview
        print("-" * 40)
        print(f"Total Duration: {results['duration_sec']} seconds")
        print(f"Total Segments Created: {len(results['segments'])}")
        print("-" * 40)

        # 4. Print details for the first few segments
        for i, seg in enumerate(results['segments'][:3]):
            print(f"Segment {i} ({seg['start_sec']}s - {seg['end_sec']}s):")
            print(f"  Hex Hash: {seg['hash_hex']}")
            print(f"  Frames sampled in this window: {seg['num_frames_sampled']}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        print("Note: Ensure 'ffmpeg' and 'ffprobe' are installed on your system.")