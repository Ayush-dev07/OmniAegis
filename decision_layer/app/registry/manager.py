from __future__ import annotations

from dataclasses import dataclass
import hashlib
from threading import Lock
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


@dataclass
class MatchResult:
    asset_id: str
    confidence: float
    distance_or_similarity: float
    metadata: dict[str, Any]


class RegistryManager:
    """Qdrant-backed registry for real-time matching and long-term retrieval.

    - Image/Video: 64D binary fingerprint vectors stored in Qdrant.
    - Audio: normalized embedding vectors stored in Qdrant.
    - Semantic image vectors: normalized embeddings stored in Qdrant.
    - Video robust mode: stores segment+profile points for coverage-aware matching.
    """

    def __init__(
        self,
        audio_dim: int,
        semantic_dim: int = 512,
        qdrant_client: QdrantClient | None = None,
        image_collection_name: str = "image_assets",
        video_collection_name: str = "video_assets",
        audio_collection_name: str = "audio_assets",
        semantic_collection_name: str = "semantic_assets",
        hnsw_m: int = 16,
        hnsw_ef_construct: int = 128,
    ) -> None:
        self._lock = Lock()

        self.image_dim = 64
        self.video_dim = 64
        self.audio_dim = audio_dim
        self.semantic_dim = semantic_dim
        self.qdrant = qdrant_client
        self.image_collection_name = image_collection_name
        self.video_collection_name = video_collection_name
        self.audio_collection_name = audio_collection_name
        self.semantic_collection_name = semantic_collection_name
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construct = hnsw_ef_construct

        self.semantic_ids: list[str] = []

        self.metadata_store: dict[str, dict[str, Any]] = {}

        if self.qdrant is not None:
            self._ensure_collection(self.image_collection_name, self.image_dim)
            self._ensure_collection(self.video_collection_name, self.video_dim)
            self._ensure_collection(self.audio_collection_name, self.audio_dim)
            self._ensure_semantic_collection()

    def _ensure_collection(self, collection_name: str, vector_size: int) -> None:
        if self.qdrant is None:
            return

        existing = {c.name for c in self.qdrant.get_collections().collections}
        if collection_name in existing:
            return

        self.qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
                on_disk=True,
            ),
            hnsw_config=qmodels.HnswConfigDiff(
                m=self.hnsw_m,
                ef_construct=self.hnsw_ef_construct,
                on_disk=True,
            ),
        )

    def _ensure_semantic_collection(self) -> None:
        self._ensure_collection(self.semantic_collection_name, self.semantic_dim)

    @staticmethod
    def _to_binary_row(hash_bytes: np.ndarray) -> np.ndarray:
        row = np.asarray(hash_bytes, dtype=np.uint8).reshape(1, -1)
        if row.shape[1] != 8:
            raise ValueError("Binary fingerprint must be exactly 64 bits (8 bytes)")
        return row

    @staticmethod
    def _normalize_rows(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8
        return vectors / norms

    @staticmethod
    def _binary_hash_to_vector(hash_bytes: np.ndarray) -> np.ndarray:
        row = np.asarray(hash_bytes, dtype=np.uint8).reshape(-1)
        if row.shape[0] != 8:
            raise ValueError("Binary fingerprint must be exactly 64 bits (8 bytes)")
        bits = np.unpackbits(row).astype(np.float32)
        return bits

    @staticmethod
    def _semantic_point_id(asset_id: str) -> int:
        """Return a deterministic integer point id compatible with local Qdrant.

        Local Qdrant strictly validates string ids as UUIDs. Using a stable int id
        avoids UUID requirements while preserving asset identity in payload.
        """
        digest = hashlib.sha1(asset_id.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    @staticmethod
    def _point_id(asset_id: str, collection_name: str, point_key: str = "") -> int:
        """Return deterministic point ids with per-record uniqueness."""
        digest = hashlib.sha1(f"{collection_name}:{asset_id}:{point_key}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    def register_image(self, asset_id: str, hash_bytes: np.ndarray, metadata: dict[str, Any]) -> None:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            vector = self._binary_hash_to_vector(hash_bytes)
            payload = {"asset_id": asset_id, **metadata}

            self.qdrant.upsert(
                collection_name=self.image_collection_name,
                points=[
                    qmodels.PointStruct(
                        id=self._point_id(asset_id, self.image_collection_name, "image_hash"),
                        vector=vector.tolist(),
                        payload=payload,
                    )
                ],
                wait=False,
            )

            existing = self.metadata_store.get(asset_id, {})
            self.metadata_store[asset_id] = {**existing, **metadata}

    def register_video(
        self,
        asset_id: str,
        hash_bytes: np.ndarray | None,
        metadata: dict[str, Any],
        hash_records: list[dict[str, Any]] | None = None,
    ) -> None:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            points: list[qmodels.PointStruct] = []

            if hash_records:
                for rec in hash_records:
                    rec_hash = rec.get("hash_bytes")
                    if rec_hash is None:
                        continue

                    vector = self._binary_hash_to_vector(np.asarray(rec_hash, dtype=np.uint8))
                    profile_id = int(rec.get("profile_id", -1))
                    segment_idx = int(rec.get("segment_idx", -1))
                    point_key = f"segment:{profile_id}:{segment_idx}"
                    rec_payload = {
                        "asset_id": asset_id,
                        "fingerprint_kind": "segment",
                        "profile_id": profile_id,
                        "segment_idx": segment_idx,
                        "segment_start_sec": float(rec.get("segment_start_sec", -1.0)),
                        "segment_end_sec": float(rec.get("segment_end_sec", -1.0)),
                        **metadata,
                    }
                    points.append(
                        qmodels.PointStruct(
                            id=self._point_id(asset_id, self.video_collection_name, point_key),
                            vector=vector.tolist(),
                            payload=rec_payload,
                        )
                    )

            if hash_bytes is not None:
                vector = self._binary_hash_to_vector(hash_bytes)
                payload = {
                    "asset_id": asset_id,
                    "fingerprint_kind": "aggregate",
                    "profile_id": -1,
                    "segment_idx": -1,
                    **metadata,
                }
                points.append(
                    qmodels.PointStruct(
                        id=self._point_id(asset_id, self.video_collection_name, "aggregate"),
                        vector=vector.tolist(),
                        payload=payload,
                    )
                )

            if not points:
                raise ValueError("No video fingerprints provided for registration")

            self.qdrant.upsert(
                collection_name=self.video_collection_name,
                points=points,
                wait=False,
            )

            existing = self.metadata_store.get(asset_id, {})
            self.metadata_store[asset_id] = {**existing, **metadata}

    def register_audio(self, asset_id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            row = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
            row = self._normalize_rows(row)

            payload = {"asset_id": asset_id, **metadata}

            self.qdrant.upsert(
                collection_name=self.audio_collection_name,
                points=[
                    qmodels.PointStruct(
                        id=self._point_id(asset_id, self.audio_collection_name, "audio_embedding"),
                        vector=row[0].tolist(),
                        payload=payload,
                    )
                ],
                wait=False,
            )

            existing = self.metadata_store.get(asset_id, {})
            self.metadata_store[asset_id] = {**existing, **metadata}

    def register_semantic(self, asset_id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            row = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
            row = self._normalize_rows(row)

            payload = {
                "asset_id": asset_id,
                **metadata,
            }

            self.qdrant.upsert(
                collection_name=self.semantic_collection_name,
                points=[
                    qmodels.PointStruct(
                        id=self._point_id(asset_id, self.semantic_collection_name, "semantic_embedding"),
                        vector=row[0].tolist(),
                        payload=payload,
                    )
                ],
                wait=False,
            )

            if asset_id not in self.semantic_ids:
                self.semantic_ids.append(asset_id)
            existing = self.metadata_store.get(asset_id, {})
            self.metadata_store[asset_id] = {**existing, **metadata}

    def match_image(self, hash_bytes: np.ndarray, top_k: int = 5) -> list[MatchResult]:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            query = self._binary_hash_to_vector(hash_bytes)

            response = self.qdrant.query_points(
                collection_name=self.image_collection_name,
                query=query.tolist(),
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            points = response.points

            results: list[MatchResult] = []
            for point in points:
                payload = dict(point.payload or {})
                asset_id = str(payload.get("asset_id") or point.id)
                score = float(point.score)
                confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
                results.append(
                    MatchResult(
                        asset_id=asset_id,
                        confidence=confidence,
                        distance_or_similarity=score,
                        metadata=payload,
                    )
                )
            return results

    def match_video(self, hash_bytes: np.ndarray, top_k: int = 5) -> list[MatchResult]:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            query = self._binary_hash_to_vector(hash_bytes)
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="fingerprint_kind",
                        match=qmodels.MatchValue(value="aggregate"),
                    )
                ]
            )

            response = self.qdrant.query_points(
                collection_name=self.video_collection_name,
                query=query.tolist(),
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            )
            points = response.points

            results: list[MatchResult] = []
            for point in points:
                payload = dict(point.payload or {})
                asset_id = str(payload.get("asset_id") or point.id)
                score = float(point.score)
                confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
                results.append(
                    MatchResult(
                        asset_id=asset_id,
                        confidence=confidence,
                        distance_or_similarity=score,
                        metadata=payload,
                    )
                )
            return results

    def match_video_robust(
        self,
        hash_records: list[dict[str, Any]],
        top_k: int = 5,
        per_record_limit: int = 6,
        min_profile_hits: int = 2,
        min_segment_coverage: float = 0.2,
    ) -> list[MatchResult]:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        if not hash_records:
            return []

        with self._lock:
            query_segments = {
                int(r.get("segment_idx", -1)) for r in hash_records if int(r.get("segment_idx", -1)) >= 0
            }
            query_profiles = {int(r.get("profile_id", -1)) for r in hash_records}

            candidate_stats: dict[str, dict[str, Any]] = {}

            for rec in hash_records:
                rec_hash = rec.get("hash_bytes")
                if rec_hash is None:
                    continue

                profile_id = int(rec.get("profile_id", -1))
                segment_idx = int(rec.get("segment_idx", -1))

                query_vector = self._binary_hash_to_vector(np.asarray(rec_hash, dtype=np.uint8))
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="fingerprint_kind",
                            match=qmodels.MatchValue(value="segment"),
                        ),
                        qmodels.FieldCondition(
                            key="profile_id",
                            match=qmodels.MatchValue(value=profile_id),
                        ),
                    ]
                )

                response = self.qdrant.query_points(
                    collection_name=self.video_collection_name,
                    query=query_vector.tolist(),
                    limit=max(per_record_limit, top_k),
                    query_filter=query_filter,
                    with_payload=True,
                    with_vectors=False,
                )

                best_by_asset: dict[str, tuple[float, dict[str, Any]]] = {}
                for point in response.points:
                    payload = dict(point.payload or {})
                    asset_id = str(payload.get("asset_id") or point.id)
                    score = float(point.score)
                    current = best_by_asset.get(asset_id)
                    if current is None or score > current[0]:
                        best_by_asset[asset_id] = (score, payload)

                for asset_id, (score, payload) in best_by_asset.items():
                    stats = candidate_stats.setdefault(
                        asset_id,
                        {
                            "score_sum": 0.0,
                            "hits": 0,
                            "matched_profiles": set(),
                            "matched_query_segments": set(),
                            "metadata": payload,
                        },
                    )
                    stats["score_sum"] += score
                    stats["hits"] += 1
                    stats["matched_profiles"].add(profile_id)
                    if segment_idx >= 0:
                        stats["matched_query_segments"].add(segment_idx)

            if not candidate_stats:
                return []

            total_segments = max(len(query_segments), 1)
            total_profiles = max(len(query_profiles), 1)

            scored: list[MatchResult] = []
            for asset_id, stats in candidate_stats.items():
                hit_count = int(stats["hits"])
                if hit_count <= 0:
                    continue

                avg_score = float(stats["score_sum"] / hit_count)
                avg_score_01 = max(0.0, min(1.0, (avg_score + 1.0) / 2.0))

                profile_hits = len(stats["matched_profiles"])
                segment_coverage = len(stats["matched_query_segments"]) / total_segments
                profile_coverage = profile_hits / total_profiles

                if total_profiles >= min_profile_hits and profile_hits < min_profile_hits:
                    continue
                if segment_coverage < min_segment_coverage:
                    continue

                confidence = (
                    0.55 * avg_score_01
                    + 0.30 * max(0.0, min(1.0, segment_coverage))
                    + 0.15 * max(0.0, min(1.0, profile_coverage))
                )
                confidence = max(0.0, min(1.0, confidence))

                metadata = dict(stats["metadata"])
                metadata.update(
                    {
                        "robust_profile_hits": profile_hits,
                        "robust_segment_coverage": float(segment_coverage),
                        "robust_profile_coverage": float(profile_coverage),
                        "robust_hit_count": hit_count,
                    }
                )

                scored.append(
                    MatchResult(
                        asset_id=asset_id,
                        confidence=confidence,
                        distance_or_similarity=avg_score,
                        metadata=metadata,
                    )
                )

            scored.sort(
                key=lambda r: (
                    float(r.confidence),
                    float(r.distance_or_similarity),
                ),
                reverse=True,
            )
            return scored[:top_k]

    @staticmethod
    def fuse_video_audio_matches(
        video_results: list[MatchResult],
        audio_results: list[MatchResult],
        top_k: int = 5,
        video_weight: float = 0.7,
        audio_weight: float = 0.3,
    ) -> list[MatchResult]:
        by_asset: dict[str, dict[str, Any]] = {}

        for vr in video_results:
            by_asset[vr.asset_id] = {
                "video": vr,
                "audio": None,
            }

        for ar in audio_results:
            bucket = by_asset.setdefault(ar.asset_id, {"video": None, "audio": None})
            bucket["audio"] = ar

        fused: list[MatchResult] = []
        for asset_id, bucket in by_asset.items():
            vr = bucket["video"]
            ar = bucket["audio"]

            video_conf = float(vr.confidence) if vr is not None else 0.0
            audio_conf = float(ar.confidence) if ar is not None else 0.0
            both_present = vr is not None and ar is not None

            confidence = (video_weight * video_conf) + (audio_weight * audio_conf)
            if both_present:
                confidence = min(1.0, confidence + 0.05)

            if vr is not None and ar is not None:
                score = (video_weight * float(vr.distance_or_similarity)) + (
                    audio_weight * float(ar.distance_or_similarity)
                )
                metadata = {
                    **vr.metadata,
                    "audio_match": ar.metadata,
                    "fusion": {
                        "method": "weighted_video_audio",
                        "video_weight": float(video_weight),
                        "audio_weight": float(audio_weight),
                        "video_confidence": video_conf,
                        "audio_confidence": audio_conf,
                    },
                }
            elif vr is not None:
                score = float(vr.distance_or_similarity)
                metadata = {
                    **vr.metadata,
                    "fusion": {
                        "method": "video_only",
                        "video_weight": float(video_weight),
                        "audio_weight": float(audio_weight),
                        "video_confidence": video_conf,
                        "audio_confidence": 0.0,
                    },
                }
            else:
                score = float(ar.distance_or_similarity)
                metadata = {
                    **ar.metadata,
                    "fusion": {
                        "method": "audio_only",
                        "video_weight": float(video_weight),
                        "audio_weight": float(audio_weight),
                        "video_confidence": 0.0,
                        "audio_confidence": audio_conf,
                    },
                }

            fused.append(
                MatchResult(
                    asset_id=asset_id,
                    confidence=max(0.0, min(1.0, confidence)),
                    distance_or_similarity=score,
                    metadata=metadata,
                )
            )

        fused.sort(
            key=lambda r: (
                float(r.confidence),
                float(r.distance_or_similarity),
            ),
            reverse=True,
        )
        return fused[:top_k]

    def match_audio(self, embedding: np.ndarray, top_k: int = 5) -> list[MatchResult]:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            query = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
            query = self._normalize_rows(query)

            response = self.qdrant.query_points(
                collection_name=self.audio_collection_name,
                query=query[0].tolist(),
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            points = response.points

            results: list[MatchResult] = []
            for point in points:
                payload = dict(point.payload or {})
                asset_id = str(payload.get("asset_id") or point.id)
                score = float(point.score)
                confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
                results.append(
                    MatchResult(
                        asset_id=asset_id,
                        confidence=confidence,
                        distance_or_similarity=score,
                        metadata=payload,
                    )
                )
            return results

    def match_semantic(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        modality_filter: str | None = None,
    ) -> list[MatchResult]:
        if self.qdrant is None:
            raise RuntimeError("Qdrant client is not initialized")

        with self._lock:
            query = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
            query = self._normalize_rows(query)

            query_filter = None
            if modality_filter:
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="modality",
                            match=qmodels.MatchValue(value=modality_filter),
                        )
                    ]
                )

            if hasattr(self.qdrant, "query_points"):
                response = self.qdrant.query_points(
                    collection_name=self.semantic_collection_name,
                    query=query[0].tolist(),
                    limit=top_k,
                    query_filter=query_filter,
                    with_payload=True,
                    with_vectors=False,
                )
                points = response.points
            else:
                points = self.qdrant.search(
                    collection_name=self.semantic_collection_name,
                    query_vector=query[0].tolist(),
                    limit=top_k,
                    query_filter=query_filter,
                    with_payload=True,
                    with_vectors=False,
                )

            results: list[MatchResult] = []
            for point in points:
                payload = dict(point.payload or {})
                asset_id = str(payload.get("asset_id") or point.id)
                score = float(point.score)
                confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
                results.append(
                    MatchResult(
                        asset_id=asset_id,
                        confidence=confidence,
                        distance_or_similarity=score,
                        metadata=payload,
                    )
                )
            return results
