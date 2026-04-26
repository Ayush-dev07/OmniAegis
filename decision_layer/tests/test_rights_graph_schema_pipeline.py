from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


DECISION_LAYER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

from app.reasoning.graph_builder import GraphBuilder


class _MockResult:
    def __init__(self, asset_id: str, score: float, metadata: dict):
        self.asset_id = asset_id
        self.distance_or_similarity = score
        self.metadata = metadata


def test_graph_builder_rights_schema_feature_shapes() -> None:
    builder = GraphBuilder(flagged_edge_boost=1.7, graph_db=None)

    query_embedding = np.linspace(0.0, 1.0, 512, dtype=np.float32)
    query_metadata = {
        "asset_id": "asset_query",
        "modality": "video",
        "content_type": "video",
        "protected_work": True,
        "creator_id": "creator_q",
        "creator_verified": True,
        "creator_tenure_months": 48,
        "creator_registered_works": 12,
        "creator_active_licenses": 7,
        "creator_trust_score": 0.88,
        "licensee_id": "licensee_q",
        "license_status": 1.0,
        "license_active": True,
        "licensee_jurisdiction": "IN",
        "licensee_active_license_count": 4,
    }

    neighbor_embedding = np.linspace(1.0, 0.0, 512, dtype=np.float32).tolist()
    results = [
        _MockResult(
            asset_id="asset_neighbor",
            score=0.91,
            metadata={
                "modality": "video",
                "content_type": "video",
                "protected_work": True,
                "is_flagged": True,
                "creator_id": "creator_1",
                "creator_verified": True,
                "creator_trust_score": 0.93,
                "creator_tenure_months": 62,
                "creator_registered_works": 33,
                "creator_active_licenses": 21,
                "licensee_id": "licensee_1",
                "license_status": 1.0,
                "license_active": True,
                "licensee_jurisdiction": "US",
                "licensee_active_license_count": 14,
                "semantic_embedding": neighbor_embedding,
            },
        )
    ]

    data = builder.build_subgraph(query_embedding=query_embedding, qdrant_results=results, query_metadata=query_metadata)

    assert data["Asset"].x.shape[1] == 520
    assert data["Creator"].x.shape[1] == 6
    assert data["Licensee"].x.shape[1] == 4

    # Query node content type one-hot for `video` => [0, 1, 0, 0].
    query_asset = data["Asset"].x[0].detach().cpu().numpy()
    assert query_asset[512] == 0.0  # image
    assert query_asset[513] == 1.0  # video
    assert query_asset[514] == 0.0  # audio
    assert query_asset[515] == 0.0  # document

    # Protected and verified flags should be set on query features.
    assert query_asset[516] == 1.0
    assert query_asset[517] == 1.0

    # Ensure key rights relations exist.
    assert ("Asset", "created_by", "Creator") in data.edge_types
    assert ("Asset", "licensed_to", "Licensee") in data.edge_types
    assert ("Asset", "similar_to", "Asset") in data.edge_types
    assert ("Asset", "flagged_with", "Asset") in data.edge_types


def test_graph_builder_document_content_type_support() -> None:
    builder = GraphBuilder(graph_db=None)

    query_embedding = np.ones(512, dtype=np.float32)
    data = builder.build_subgraph(
        query_embedding=query_embedding,
        qdrant_results=[],
        query_metadata={
            "asset_id": "doc_asset",
            "modality": "document",
            "content_type": "document",
            "protected_work": True,
        },
    )

    query_asset = data["Asset"].x[0].detach().cpu().numpy()
    # one-hot [image, video, audio, document]
    assert query_asset[512] == 0.0
    assert query_asset[513] == 0.0
    assert query_asset[514] == 0.0
    assert query_asset[515] == 1.0
