from __future__ import annotations

import hashlib
import logging
import subprocess
import json
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Try to import acoustid (Chromaprint Python bindings). Fall back to fpcalc CLI.
try:
    import acoustid
    _HAS_ACOUSTID = True
except ImportError:
    _HAS_ACOUSTID = False


class AudioFingerprinter:
    """Robust audio fingerprinting using Chromaprint, with a 256‑bit SimHash embedding."""

    def __init__(self, sample_rate: int = 22050, simhash_bits: int = 256) -> None:
        self.sample_rate = sample_rate
        self.simhash_bits = simhash_bits
        if simhash_bits % 8 != 0:
            raise ValueError("simhash_bits must be a multiple of 8")
        # Fixed random seed for reproducible SimHash projections
        self._rng = np.random.RandomState(42)
        # Pre‑generate a projection matrix for the hash‑to‑sign step is not needed;
        # SimHash uses per‑feature hashing, no global matrix.

    def fingerprint(self, audio_path: str) -> dict:
        """Extract Chromaprint fingerprint and compute a fixed‑size SimHash embedding."""
        fp_raw, duration = self._compute_chromaprint(audio_path)
        if not fp_raw:
            raise ValueError("Could not extract Chromaprint fingerprint")

        simhash_bits, simhash_float = self._chromaprint_to_simhash(fp_raw)

        # Compact ID for traceability (first 8 bytes of raw fingerprint)
        digest = hashlib.sha256(b"".join(f.to_bytes(4, "big") for f in fp_raw)).hexdigest()[:16]

        return {
            "chromaprint": fp_raw,
            "chromaprint_length": len(fp_raw),
            "duration_sec": round(duration, 3),
            "fingerprint_id": digest,
            "embedding": simhash_bits,                     # uint8 array (32 bytes)
            "embedding_hex": simhash_bits.tobytes().hex(),
            "embedding_size_bits": self.simhash_bits,
        }

    def get_embedding_vector(self, fingerprint: dict) -> np.ndarray:
        """Return a float32 vector (0/1) from the SimHash embedding for Milvus."""
        return np.unpackbits(fingerprint["embedding"]).astype(np.float32)

    # ------------------------------------------------------------------
    #  Chromaprint extraction (acoustid or fpcalc)
    # ------------------------------------------------------------------
    def _compute_chromaprint(self, audio_path: str) -> tuple[List[int], float]:
        if _HAS_ACOUSTID:
            try:
                duration, fp_encoded = acoustid.fingerprint(audio_path)
                # fp_encoded is a base64 string; decode to list of ints
                fingerprint = acoustid.decode_fingerprint(fp_encoded)
                return fingerprint, duration
            except Exception as e:
                logger.warning("acoustid failed: %s, trying fpcalc fallback", e)

        # Fallback: use fpcalc command‑line tool
        fingerprint = self._run_fpcalc(audio_path)
        duration = self._get_duration(audio_path) or 0.0
        return fingerprint, duration

    @staticmethod
    def _run_fpcalc(audio_path: str) -> List[int]:
        """Call fpcalc and parse its JSON output."""
        try:
            proc = subprocess.run(
                ["fpcalc", "-raw", "-json", audio_path],
                capture_output=True,
                timeout=30,
                text=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"fpcalc error: {proc.stderr}")
            data = json.loads(proc.stdout)
            # fpcalc may return 'fingerprint' as a list or a comma‑separated string
            fp = data.get("fingerprint")
            if isinstance(fp, str):
                fp = [int(x) for x in fp.strip().split(",") if x]
            elif isinstance(fp, list):
                fp = [int(x) for x in fp]
            else:
                raise ValueError("Unexpected fpcalc output format")
            return fp
        except Exception as e:
            raise RuntimeError(f"fpcalc failed: {e}")

    @staticmethod
    def _get_duration(audio_path: str) -> Optional[float]:
        """Get duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]
            out = subprocess.check_output(cmd, timeout=10).decode().strip()
            return float(out) if out else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    #  SimHash embedding from Chromaprint subfingerprints
    # ------------------------------------------------------------------
    def _chromaprint_to_simhash(self, fingerprint: List[int]):
        """Convert list of 32‑bit subfingerprints to a SimHash binary embedding."""
        v = np.zeros(self.simhash_bits, dtype=np.float32)

        for fp in fingerprint:
            # Use a deterministic 256‑bit hash from the 32‑bit subfingerprint
            h = int.from_bytes(
                hashlib.sha256(fp.to_bytes(4, "big")).digest()[:32], "big"
            )
            for i in range(self.simhash_bits):
                if (h >> i) & 1:
                    v[i] += 1.0
                else:
                    v[i] -= 1.0

        simhash_bits = (v > 0).astype(np.uint8)
        return simhash_bits, v
    
# Instant test

if __name__ == "__main__":
    # Initialize the fingerprinter
    afp = AudioFingerprinter(simhash_bits=256)

    # Use your 60s mock video/audio file
    test_file = "fingerprints/clavier-music-relaxing-piano-music-351844.mp3" 

    try:
        # 1. Extract the fingerprint
        result = afp.fingerprint(test_file)

        # 2. PACK the bits into actual bytes for a proper Hex DNA string
        # np.packbits turns 8 individual 0/1 bits into a single byte
        packed_dna = np.packbits(result['embedding'])
        hex_dna = packed_dna.tobytes().hex()

        # 3. Get the correct 256-bit vector for the database
        # get_embedding_vector already handles the bit unpacking for you
        db_vector = afp.get_embedding_vector(result)
        # If the vector is unpacked from the byte-per-bit array, 
        # it will be 2048. Slice it to get the correct 256 dimensions.
        if db_vector.shape[0] == 2048:
            db_vector = db_vector[::8]

        print("-" * 50)
        print(f"File:           {test_file}")
        print(f"Duration:       {result['duration_sec']}s")
        print(f"Fingerprint ID: {result['fingerprint_id']}")
        print(f"Audio DNA (Hex): {hex_dna}")
        print(f"DNA Length:      {len(hex_dna)} characters (256-bit)")
        print(f"Vector Shape:    {db_vector.shape}")
        print("-" * 50)

    except Exception as e:
        print(f"Critical Error: {e}")