from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from decision_layer.app.config import QdrantClientSingleton, load_qdrant_settings
    from decision_layer.services.graph_db import GraphDBService
except ModuleNotFoundError:  # pragma: no cover
    from app.config import QdrantClientSingleton, load_qdrant_settings
    from services.graph_db import GraphDBService


@dataclass
class BackfillStats:
    scanned_points: int = 0
    upserted_assets: int = 0
    skipped_assets: int = 0


def _get_collections(qdrant_client: Any) -> set[str]:
    return {c.name for c in qdrant_client.get_collections().collections}


def _safe_vector(point: Any) -> list[float] | None:
    vec = getattr(point, "vector", None)
    if vec is None:
        return None
    if isinstance(vec, dict):
        # Named vectors mode: pick the first vector.
        try:
            first_key = next(iter(vec.keys()))
            vec = vec[first_key]
        except Exception:
            return None
    try:
        arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    except Exception:
        return None
    if arr.size == 0:
        return None
    return arr.astype(np.float32).tolist()


def _iter_collection_points(qdrant_client: Any, collection_name: str, page_size: int = 256) -> list[Any]:
    points: list[Any] = []
    offset = None
    while True:
        batch, next_offset = qdrant_client.scroll(
            collection_name=collection_name,
            limit=page_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not batch:
            break
        points.extend(batch)
        if next_offset is None:
            break
        offset = next_offset
    return points


def _similar_neighbors(
    qdrant_client: Any,
    collection_name: str,
    query_vector: list[float] | None,
    *,
    self_asset_id: str,
    threshold: float,
    limit: int = 8,
) -> list[dict[str, Any]]:
    if query_vector is None:
        return []

    try:
        if hasattr(qdrant_client, "query_points"):
            response = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=max(limit + 1, 4),
                with_payload=True,
                with_vectors=False,
            )
            points = list(response.points)
        else:
            points = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=max(limit + 1, 4),
                with_payload=True,
                with_vectors=False,
            )
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for p in points:
        payload = dict(getattr(p, "payload", {}) or {})
        asset_id = str(payload.get("asset_id") or getattr(p, "id", ""))
        if not asset_id or asset_id == self_asset_id:
            continue

        score = float(getattr(p, "score", 0.0))
        if score < threshold:
            continue

        out.append(
            {
                "asset_id": asset_id,
                "similarity": score,
                "modality": payload.get("modality"),
                "is_flagged": bool(payload.get("is_flagged", False)),
                "flagged_weight": float(payload.get("flagged_weight", 1.5)),
                "model_name": f"{collection_name}_backfill",
                "model_version": "1",
                "threshold": threshold,
                "match_context": "backfill",
                "updated_at": int(time.time() * 1000),
                "evidence_source": payload.get("flagged_evidence_source", "historical_case"),
                "case_id": payload.get("flagged_case_id"),
                "confidence": float(payload.get("flagged_confidence", 1.0)),
            }
        )
        if len(out) >= limit:
            break

    return out


def _normalized_rights_context(
    *,
    collection_name: str,
    asset_id: str,
    payload: dict[str, Any],
    vector: list[float] | None,
) -> dict[str, Any]:
    modality_by_collection = {
        "image_assets": "image",
        "video_assets": "video",
        "audio_assets": "audio",
        "semantic_assets": str(payload.get("modality", "image") or "image"),
    }
    modality = modality_by_collection.get(collection_name, str(payload.get("modality", "image") or "image"))

    if collection_name == "semantic_assets":
        fingerprint_kind = "semantic_embedding"
    elif collection_name == "video_assets":
        fingerprint_kind = str(payload.get("fingerprint_kind", "video_aggregate"))
    elif collection_name == "audio_assets":
        fingerprint_kind = "landmark_histogram"
    else:
        fingerprint_kind = "phash64"

    fingerprint_hash = (
        payload.get("fingerprint_hash")
        or payload.get("hash_hex")
        or payload.get("aggregate_hash_hex")
        or payload.get("fingerprint_id")
    )

    ctx = {
        "schema_version": int(payload.get("schema_version", 2)),
        "modality": modality,
        "content_type": str(payload.get("content_type", modality) or modality),
        "source": payload.get("source"),
        "filename": payload.get("filename"),
        "protected_work": bool(payload.get("protected_work", True)),
        "registered_at": payload.get("registered_at"),
        "embedding_vector": vector if collection_name in {"semantic_assets", "audio_assets"} else None,
        "fingerprint_hash": fingerprint_hash,
        "fingerprint_kind": fingerprint_kind,
        "is_flagged": bool(payload.get("is_flagged", False)),
        "creator_id": payload.get("creator_id"),
        "creator_trust_score": float(payload.get("creator_trust_score", 0.5)),
        "creator_tenure_months": float(payload.get("creator_tenure_months", 12.0)),
        "creator_verified": bool(payload.get("creator_verified", False)),
        "creator_registered_works": int(payload.get("creator_registered_works", 0)),
        "creator_active_licenses": int(payload.get("creator_active_licenses", 0)),
        "licensee_id": payload.get("licensee_id"),
        "licensee_jurisdiction": str(payload.get("licensee_jurisdiction", "") or ""),
        "licensee_active_license_count": int(payload.get("licensee_active_license_count", 0)),
        "license_status": float(payload.get("license_status", 0.0)),
        "license_type": str(payload.get("license_type", "") or ""),
        "license_expires_at": str(payload.get("license_expires_at", "") or ""),
        "license_territory": str(payload.get("license_territory", "") or ""),
        "license_jurisdiction": str(payload.get("license_jurisdiction", "") or ""),
        "license_derivative_allowed": bool(payload.get("license_derivative_allowed", False)),
        "license_commercial_use": bool(payload.get("license_commercial_use", False)),
        "license_active": bool(payload.get("license_active", False)),
        "creator": dict(payload.get("creator") or {}),
        "licensee": dict(payload.get("licensee") or {}),
        "license_terms": dict(payload.get("license_terms") or {}),
    }

    # Keep required identity stable.
    _ = asset_id
    return ctx


def backfill_rights_graph(
    *,
    dry_run: bool,
    include_collections: list[str] | None = None,
) -> BackfillStats:
    settings = load_qdrant_settings()
    qdrant_client = QdrantClientSingleton.get_client(settings)

    graph_db: GraphDBService | None = None
    try:
        if not dry_run:
            graph_db = GraphDBService.from_env()
            graph_db.run_migrations()

        available = _get_collections(qdrant_client)
        default_collections = ["semantic_assets", "image_assets", "video_assets", "audio_assets"]
        selected = include_collections or default_collections
        selected = [c for c in selected if c in available]

        stats = BackfillStats()
        seen_assets: set[tuple[str, str]] = set()

        threshold_by_collection = {
            "semantic_assets": 0.80,
            "video_assets": 0.75,
            "audio_assets": 0.70,
            "image_assets": 0.90,
        }

        for collection_name in selected:
            points = _iter_collection_points(qdrant_client, collection_name)
            stats.scanned_points += len(points)

            for point in points:
                payload = dict(getattr(point, "payload", {}) or {})
                asset_id = str(payload.get("asset_id") or getattr(point, "id", ""))
                if not asset_id:
                    stats.skipped_assets += 1
                    continue

                key = (collection_name, asset_id)
                if key in seen_assets:
                    # Prefer single upsert per collection x asset.
                    continue
                seen_assets.add(key)

                vector = _safe_vector(point)
                rights_context = _normalized_rights_context(
                    collection_name=collection_name,
                    asset_id=asset_id,
                    payload=payload,
                    vector=vector,
                )

                neighbors = _similar_neighbors(
                    qdrant_client,
                    collection_name,
                    vector,
                    self_asset_id=asset_id,
                    threshold=threshold_by_collection.get(collection_name, 0.8),
                    limit=8,
                )

                if dry_run:
                    stats.upserted_assets += 1
                    continue

                if graph_db is None:
                    raise RuntimeError("GraphDB service is not initialized")

                graph_db.upsert_asset_context(asset_id=asset_id, metadata=rights_context, neighbors=neighbors)
                stats.upserted_assets += 1

        return stats
    finally:
        if graph_db is not None:
            graph_db.close()
        QdrantClientSingleton.close_client()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill Neo4j rights-ecosystem schema from Qdrant payloads")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and compute backfill actions without writing to Neo4j",
    )
    parser.add_argument(
        "--collections",
        nargs="*",
        default=None,
        help="Optional list of Qdrant collections to process",
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    stats = backfill_rights_graph(dry_run=bool(args.dry_run), include_collections=args.collections)
    print(
        "Backfill completed:",
        {
            "dry_run": bool(args.dry_run),
            "scanned_points": stats.scanned_points,
            "upserted_assets": stats.upserted_assets,
            "skipped_assets": stats.skipped_assets,
        },
    )


if __name__ == "__main__":
    main()
