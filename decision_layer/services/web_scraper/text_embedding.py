from __future__ import annotations

import hashlib
import re

import numpy as np


class TextEmbeddingEncoder:
	"""Deterministic 512-d text embedder for scraped web content.

	This is intentionally lightweight so scraped pages can be compared in the
	existing semantic Qdrant collection without adding a new heavyweight NLP
	dependency.
	"""

	def __init__(self, embedding_dim: int = 512) -> None:
		if embedding_dim < 32:
			raise ValueError("embedding_dim must be at least 32")
		self.embedding_dim = embedding_dim
		self._token_pattern = re.compile(r"[A-Za-z0-9_']+")

	@staticmethod
	def _token_hash(token: str) -> int:
		return int.from_bytes(hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()[:8], "big")

	def embed_text(self, text: str) -> np.ndarray:
		clean = (text or "").strip().lower()
		vec = np.zeros(self.embedding_dim, dtype=np.float32)
		if not clean:
			return vec

		tokens = self._token_pattern.findall(clean)
		if not tokens:
			tokens = clean.split()

		for index, token in enumerate(tokens):
			h = self._token_hash(token)
			bucket = h % self.embedding_dim
			sign = 1.0 if (h >> 8) & 1 else -1.0
			weight = 1.0 + min(index, 32) * 0.015
			vec[bucket] += sign * weight

		for n in (2, 3):
			if len(tokens) < n:
				continue
			for i in range(len(tokens) - n + 1):
				ngram = " ".join(tokens[i : i + n])
				h = self._token_hash(ngram)
				bucket = h % self.embedding_dim
				sign = 1.0 if (h >> 9) & 1 else -1.0
				vec[bucket] += sign * 0.5

		norm = float(np.linalg.norm(vec))
		if norm > 0.0:
			vec /= norm
		return vec.astype(np.float32)
