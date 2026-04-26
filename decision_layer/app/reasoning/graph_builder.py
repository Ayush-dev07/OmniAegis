from __future__ import annotations

from datetime import date, datetime
import hashlib
from typing import Any, Iterable

import numpy as np
import torch
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected


class GraphBuilder:
    """Builds on-the-fly heterogeneous subgraphs for reasoning.

    Node types:
    - Asset (512-d embedding + rights metadata features)
    - Creator (verified, tenure, registry footprint, trust)
    - Licensee (license status, jurisdiction, active licenses)

    Edge types:
    - Asset -> Creator: created_by
    - Asset -> Licensee: licensed_to
    - Asset -> Asset: similar_to (weighted by semantic similarity)
    - Asset -> Asset: flagged_with (weighted, stronger negative signal)
    """

    def __init__(self, flagged_edge_boost: float = 1.5, graph_db: Any | None = None) -> None:
        self.flagged_edge_boost = flagged_edge_boost
        self._to_undirected = ToUndirected(merge=False)
        self.graph_db = graph_db
        self.asset_feature_dim = 520  # 512 embedding + 8 metadata dims
        self.creator_feature_dim = 6
        self.licensee_feature_dim = 4

    @staticmethod
    def _normalize_tenure(tenure_months: float) -> float:
        # Assumes 10 years as soft max for normalization.
        return float(np.clip(tenure_months / 120.0, 0.0, 1.0))

    @staticmethod
    def _normalize_count(value: float, soft_max: float) -> float:
        return float(np.clip(float(value) / max(float(soft_max), 1.0), 0.0, 1.0))

    @staticmethod
    def _to_bool01(value: Any, default: float = 0.0) -> float:
        if value is None:
            return float(default)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return 1.0
        if text in {"0", "false", "no", "n", "off"}:
            return 0.0
        try:
            return 1.0 if float(text) > 0 else 0.0
        except Exception:
            return float(default)

    @staticmethod
    def _content_type_one_hot(content_type: str) -> list[float]:
        key = str(content_type or "").strip().lower()
        order = ["image", "video", "audio", "document"]
        return [1.0 if key == item else 0.0 for item in order]

    @staticmethod
    def _hash_bucket_norm(value: str, buckets: int = 97) -> float:
        if not value:
            return 0.0
        digest = hashlib.sha1(value.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], byteorder="big", signed=False) % buckets
        return float(bucket / max(buckets - 1, 1))

    @staticmethod
    def _parse_date_ymd(value: Any) -> date | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None

        # Accept common ISO-like forms: YYYY-MM-DD or full ISO datetime.
        try:
            return date.fromisoformat(text[:10])
        except Exception:
            pass

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except Exception:
            return None

    @staticmethod
    def _territory_allows(license_territory: Any, requested_territory: Any) -> bool:
        lic = str(license_territory or "").strip().upper()
        req = str(requested_territory or "").strip().upper()

        if not req:
            return True
        if not lic:
            return True
        if lic in {"GLOBAL", "WORLD", "WORLDWIDE", "ALL", "*"}:
            return True

        tokens = {
            part.strip().upper()
            for part in lic.replace(";", ",").replace("|", ",").split(",")
            if part.strip()
        }
        return req in tokens

    def _effective_license_terms(self, metadata: dict[str, Any]) -> tuple[float, float]:
        # Base values (legacy-compatible defaults).
        base_status = float(np.clip(float(metadata.get("license_status", 0.0)), 0.0, 1.0))
        base_active = self._to_bool01(metadata.get("license_active", base_status > 0.5)) > 0.5

        expires_on = self._parse_date_ymd(metadata.get("license_expires_at"))
        is_expired = bool(expires_on is not None and expires_on < date.today())

        requested_territory = metadata.get("requested_territory", metadata.get("_requested_territory", ""))
        territory_allowed = self._territory_allows(metadata.get("license_territory", ""), requested_territory)

        derivative_allowed = self._to_bool01(metadata.get("license_derivative_allowed", False), default=0.0) > 0.5
        derivative_request = self._to_bool01(
            metadata.get("is_derivative", metadata.get("derivative_request", metadata.get("_is_derivative_request", False))),
            default=0.0,
        ) > 0.5
        derivative_permitted = derivative_allowed or (not derivative_request)

        effective_active = base_active and (not is_expired) and territory_allowed and derivative_permitted
        effective_status = base_status if effective_active else 0.0
        return float(effective_status), float(1.0 if effective_active else 0.0)

    @staticmethod
    def _metadata_from_result(result: Any) -> tuple[str, float, dict[str, Any]]:
        if isinstance(result, dict):
            asset_id = str(result.get("asset_id", ""))
            similarity = float(result.get("score", 0.0))
            metadata = dict(result.get("metadata", {}))
            return asset_id, similarity, metadata

        asset_id = str(getattr(result, "asset_id", ""))
        similarity = float(getattr(result, "distance_or_similarity", 0.0))
        metadata = dict(getattr(result, "metadata", {}) or {})
        return asset_id, similarity, metadata

    @staticmethod
    def _safe_embedding(metadata: dict[str, Any], fallback: np.ndarray, similarity: float) -> np.ndarray:
        candidate = metadata.get("semantic_embedding")
        if candidate is not None:
            arr = np.asarray(candidate, dtype=np.float32).reshape(-1)
            if arr.shape[0] == 512:
                return arr

        # Fallback: scaled proxy vector if neighbor embedding is not available in metadata.
        scale = float(np.clip((similarity + 1.0) / 2.0, 0.0, 1.0))
        return (fallback * scale).astype(np.float32)

    def _asset_feature_vector(
        self,
        embedding_512: np.ndarray,
        metadata: dict[str, Any],
        similarity: float,
    ) -> np.ndarray:
        content_type = str(metadata.get("content_type", metadata.get("modality", "image")) or "image")
        content_type_oh = self._content_type_one_hot(content_type)

        protected_work = self._to_bool01(metadata.get("protected_work", False))
        creator_verified = self._to_bool01(metadata.get("creator_verified", False))
        license_active = self._to_bool01(metadata.get("license_active", metadata.get("license_status", 0.0) > 0.5))
        is_flagged = self._to_bool01(metadata.get("is_flagged", False))

        extra = np.asarray(
            [
                *content_type_oh,
                protected_work,
                creator_verified,
                license_active,
                float(np.clip(similarity, 0.0, 1.0)),
            ],
            dtype=np.float32,
        )
        return np.concatenate([embedding_512.astype(np.float32), extra], axis=0)

    def _creator_feature_vector(self, metadata: dict[str, Any]) -> list[float]:
        return [
            self._to_bool01(metadata.get("creator_verified", False)),
            self._normalize_tenure(float(metadata.get("creator_tenure_months", 12.0))),
            self._normalize_count(float(metadata.get("creator_registered_works", 0)), soft_max=1000.0),
            self._normalize_count(float(metadata.get("creator_active_licenses", 0)), soft_max=1000.0),
            float(np.clip(float(metadata.get("creator_trust_score", 0.5)), 0.0, 1.0)),
            self._to_bool01(metadata.get("protected_work", False)),
        ]

    def _licensee_feature_vector(self, metadata: dict[str, Any]) -> list[float]:
        jurisdiction = str(metadata.get("licensee_jurisdiction", metadata.get("license_jurisdiction", "")) or "")
        effective_status, effective_active = self._effective_license_terms(metadata)
        return [
            effective_status,
            self._hash_bucket_norm(jurisdiction),
            self._normalize_count(float(metadata.get("licensee_active_license_count", 0)), soft_max=10000.0),
            effective_active,
        ]

    def build_subgraph(
        self,
        query_embedding: np.ndarray,
        qdrant_results: Iterable[Any],
        query_metadata: dict[str, Any] | None = None,
    ) -> HeteroData:
        query_metadata = query_metadata or {}

        query_vec = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        if query_vec.shape[0] != 512:
            raise ValueError("Query embedding must be 512-dimensional")

        asset_ids: list[str] = ["__query__"]
        query_asset_metadata = {
            "content_type": query_metadata.get("content_type", query_metadata.get("modality", "image")),
            "protected_work": query_metadata.get("protected_work", False),
            "creator_verified": query_metadata.get("creator_verified", False),
            "license_active": query_metadata.get("license_active", False),
            "is_flagged": query_metadata.get("is_flagged", False),
        }

        asset_features: list[np.ndarray] = [self._asset_feature_vector(query_vec, query_asset_metadata, similarity=1.0)]

        creator_ids: list[str] = []
        creator_features: list[list[float]] = []

        licensee_ids: list[str] = []
        licensee_features: list[list[float]] = []

        created_edges: list[list[int]] = []
        created_attr: list[list[float]] = []

        licensed_edges: list[list[int]] = []
        licensed_attr: list[list[float]] = []

        similar_edges: list[list[int]] = []
        similar_attr: list[list[float]] = []

        flagged_edges: list[list[int]] = []
        flagged_attr: list[list[float]] = []

        creator_index: dict[str, int] = {}
        licensee_index: dict[str, int] = {}

        def upsert_creator(creator_id: str, trust_score: float, tenure_months: float) -> int:
            if creator_id in creator_index:
                return creator_index[creator_id]
            idx = len(creator_ids)
            creator_index[creator_id] = idx
            creator_ids.append(creator_id)
            creator_features.append(
                self._creator_feature_vector(
                    {
                        "creator_trust_score": trust_score,
                        "creator_tenure_months": tenure_months,
                        "creator_verified": query_metadata.get("creator_verified", False),
                        "creator_registered_works": query_metadata.get("creator_registered_works", 0),
                        "creator_active_licenses": query_metadata.get("creator_active_licenses", 0),
                        "protected_work": query_metadata.get("protected_work", False),
                    }
                )
            )
            return idx

        def upsert_licensee(licensee_id: str, status: float) -> int:
            if licensee_id in licensee_index:
                return licensee_index[licensee_id]
            idx = len(licensee_ids)
            licensee_index[licensee_id] = idx
            licensee_ids.append(licensee_id)
            licensee_features.append(
                self._licensee_feature_vector(
                    {
                        "license_status": status,
                        "licensee_jurisdiction": query_metadata.get("licensee_jurisdiction", ""),
                        "licensee_active_license_count": query_metadata.get("licensee_active_license_count", 0),
                        "license_active": query_metadata.get("license_active", False),
                        "license_expires_at": query_metadata.get("license_expires_at"),
                        "license_territory": query_metadata.get("license_territory", ""),
                        "license_derivative_allowed": query_metadata.get("license_derivative_allowed", False),
                        "requested_territory": query_metadata.get("requested_territory", ""),
                        "is_derivative": query_metadata.get(
                            "is_derivative",
                            query_metadata.get("derivative_request", False),
                        ),
                    }
                )
            )
            return idx

        # Attach query creator/license info if available.
        if "creator_id" in query_metadata:
            c_idx = upsert_creator(
                str(query_metadata.get("creator_id")),
                float(query_metadata.get("creator_trust_score", 0.5)),
                float(query_metadata.get("creator_tenure_months", 12.0)),
            )
            created_edges.append([0, c_idx])
            created_attr.append([0.3])

        if "licensee_id" in query_metadata:
            l_idx = upsert_licensee(
                str(query_metadata.get("licensee_id")),
                float(query_metadata.get("license_status", 0.0)),
            )
            licensed_edges.append([0, l_idx])
            licensed_attr.append([1.0])

        # Self-loop similar edge keeps query node in relational channel.
        similar_edges.append([0, 0])
        similar_attr.append([1.0])

        result_records: list[tuple[str, float, dict[str, Any]]] = []
        for result in qdrant_results:
            neighbor_asset_id, similarity, metadata = self._metadata_from_result(result)
            if not neighbor_asset_id:
                continue
            result_records.append((neighbor_asset_id, similarity, metadata))

        if self.graph_db is not None:
            query_asset_id = str(query_metadata.get("asset_id", "__query__"))
            try:
                self.graph_db.upsert_asset_context(
                    asset_id=query_asset_id,
                    metadata={
                        **query_metadata,
                        "modality": query_metadata.get("modality", "image"),
                    },
                    neighbors=[
                        {
                            "asset_id": aid,
                            "similarity": sim,
                            "is_flagged": bool(meta.get("is_flagged", False)),
                            "modality": meta.get("modality"),
                            "flagged_weight": float(meta.get("flagged_weight", self.flagged_edge_boost)),
                        }
                        for aid, sim, meta in result_records
                    ],
                )
                neighborhood = self.graph_db.fetch_asset_neighborhood(asset_id=query_asset_id, limit_assets=64)
                neo_records: list[tuple[str, float, dict[str, Any]]] = []
                for n in neighborhood.get("neighbors", []):
                    n_asset_id = str(n.get("asset_id", ""))
                    if not n_asset_id:
                        continue
                    neo_records.append((n_asset_id, float(n.get("similarity", 0.0)), dict(n)))
                if neo_records:
                    result_records = neo_records
            except Exception:
                pass

        for neighbor_asset_id, similarity, metadata in result_records:
            n_idx = len(asset_ids)
            asset_ids.append(neighbor_asset_id)
            neighbor_embedding = self._safe_embedding(metadata, query_vec, similarity)
            asset_features.append(self._asset_feature_vector(neighbor_embedding, metadata, similarity))

            sim_w = float(np.clip(similarity, 0.0, 1.0))
            similar_edges.append([0, n_idx])
            similar_attr.append([sim_w])

            if bool(metadata.get("is_flagged", False)):
                flagged_edges.append([0, n_idx])
                flagged_attr.append([self.flagged_edge_boost])

            creator_id = metadata.get("creator_id")
            if creator_id:
                c_id = str(creator_id)
                if c_id in creator_index:
                    c_idx = creator_index[c_id]
                else:
                    c_idx = len(creator_ids)
                    creator_index[c_id] = c_idx
                    creator_ids.append(c_id)
                    creator_features.append(self._creator_feature_vector(metadata))
                created_edges.append([n_idx, c_idx])
                created_attr.append([0.3])

            licensee_id = metadata.get("licensee_id")
            if licensee_id:
                l_id = str(licensee_id)
                if l_id in licensee_index:
                    l_idx = licensee_index[l_id]
                else:
                    l_idx = len(licensee_ids)
                    licensee_index[l_id] = l_idx
                    licensee_ids.append(l_id)
                    licensee_features.append(
                        self._licensee_feature_vector(
                            {
                                **metadata,
                                "_requested_territory": query_metadata.get("requested_territory", ""),
                                "_is_derivative_request": query_metadata.get(
                                    "is_derivative",
                                    query_metadata.get("derivative_request", False),
                                ),
                            }
                        )
                    )
                licensed_edges.append([n_idx, l_idx])
                licensed_attr.append([1.0])

        data = HeteroData()

        data["Asset"].x = torch.tensor(np.vstack(asset_features), dtype=torch.float32)
        data["Asset"].node_ids = asset_ids
        data["Asset"].query_index = torch.tensor([0], dtype=torch.long)

        if creator_features:
            data["Creator"].x = torch.tensor(np.asarray(creator_features, dtype=np.float32), dtype=torch.float32)
            data["Creator"].node_ids = creator_ids
        else:
            data["Creator"].x = torch.zeros((1, self.creator_feature_dim), dtype=torch.float32)
            data["Creator"].node_ids = ["__dummy_creator__"]

        if licensee_features:
            data["Licensee"].x = torch.tensor(np.asarray(licensee_features, dtype=np.float32), dtype=torch.float32)
            data["Licensee"].node_ids = licensee_ids
        else:
            data["Licensee"].x = torch.zeros((1, self.licensee_feature_dim), dtype=torch.float32)
            data["Licensee"].node_ids = ["__dummy_licensee__"]

        if not created_edges:
            created_edges = [[0, 0]]
            created_attr = [[0.0]]
        if not licensed_edges:
            licensed_edges = [[0, 0]]
            licensed_attr = [[0.0]]
        if not flagged_edges:
            flagged_edges = [[0, 0]]
            flagged_attr = [[0.0]]

        data[("Asset", "created_by", "Creator")].edge_index = torch.tensor(created_edges, dtype=torch.long).t().contiguous()
        data[("Asset", "created_by", "Creator")].edge_attr = torch.tensor(created_attr, dtype=torch.float32)

        data[("Asset", "licensed_to", "Licensee")].edge_index = torch.tensor(licensed_edges, dtype=torch.long).t().contiguous()
        data[("Asset", "licensed_to", "Licensee")].edge_attr = torch.tensor(licensed_attr, dtype=torch.float32)

        data[("Asset", "similar_to", "Asset")].edge_index = torch.tensor(similar_edges, dtype=torch.long).t().contiguous()
        data[("Asset", "similar_to", "Asset")].edge_attr = torch.tensor(similar_attr, dtype=torch.float32)

        data[("Asset", "flagged_with", "Asset")].edge_index = torch.tensor(flagged_edges, dtype=torch.long).t().contiguous()
        data[("Asset", "flagged_with", "Asset")].edge_attr = torch.tensor(flagged_attr, dtype=torch.float32)

        # Add reverse relations so `Asset` nodes can receive creator/licensee signals.
        data = self._to_undirected(data)
        return data
