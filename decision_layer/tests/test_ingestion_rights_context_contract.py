from __future__ import annotations

import hashlib
import importlib
import json
import sys
import types
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from fastapi import UploadFile


DECISION_LAYER_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

qdrant_client = pytest.importorskip("qdrant_client")

from app.reasoning.graph_builder import GraphBuilder
from app.reasoning.model import RightsGNN
from app.registry.manager import RegistryManager


class _FakeImageFingerprinter:
    def fingerprint_from_bytes(self, content: bytes) -> dict[str, Any]:
        digest = hashlib.sha256(content).digest()
        hash_bytes = np.frombuffer(digest[:8], dtype=np.uint8).copy()
        hash_bits = "".join(np.unpackbits(hash_bytes).astype(str).tolist())
        return {
            "hash_hex": hash_bytes.tobytes().hex(),
            "hash_bits": hash_bits,
            "hash_bytes": hash_bytes,
            "hash_size_bits": 64,
        }


class _FakeSemanticEmbedder:
    def __init__(self, embedding_dim: int = 512) -> None:
        self.embedding_dim = int(embedding_dim)

    @staticmethod
    def _embedding_from_bytes(content: bytes) -> np.ndarray:
        digest = hashlib.sha256(content).digest()
        tiled = (digest * ((512 // len(digest)) + 1))[:512]
        vec = np.frombuffer(tiled, dtype=np.uint8).astype(np.float32)
        vec = (vec - vec.mean()) / (vec.std() + 1e-6)
        vec = vec / (np.linalg.norm(vec) + 1e-6)
        return vec.astype(np.float32)

    def embed_from_bytes(self, content: bytes) -> dict[str, Any]:
        emb = self._embedding_from_bytes(content)
        return {"embedding": emb, "embedding_dim": self.embedding_dim}


class _FakeVideoFingerprinter:
    def __init__(self, frames_to_sample: int = 16) -> None:
        self.frames_to_sample = frames_to_sample

    @staticmethod
    def _fingerprint_for_path(path: str) -> dict[str, Any]:
        content = Path(path).read_bytes()
        digest = hashlib.sha256(content).digest()
        aggregate_hash_bytes = np.frombuffer(digest[:8], dtype=np.uint8).copy()

        segment_hash_records = [
            {
                "profile_id": 0,
                "segment_idx": 0,
                "segment_start_sec": 0.0,
                "segment_end_sec": 1.0,
                "hash_hex": aggregate_hash_bytes.tobytes().hex(),
                "hash_bytes": aggregate_hash_bytes,
            },
            {
                "profile_id": 1,
                "segment_idx": 0,
                "segment_start_sec": 0.0,
                "segment_end_sec": 1.0,
                "hash_hex": aggregate_hash_bytes.tobytes().hex(),
                "hash_bytes": aggregate_hash_bytes,
            },
        ]

        return {
            "frames_sampled": 2,
            "frame_hashes": [aggregate_hash_bytes.tobytes().hex()],
            "sampling_profiles": 2,
            "segment_count": 1,
            "quality": {"blank_ratio": 0.0},
            "segment_hash_records": segment_hash_records,
            "aggregate_hash_hex": aggregate_hash_bytes.tobytes().hex(),
            "aggregate_hash_bits": "".join(np.unpackbits(aggregate_hash_bytes).astype(str).tolist()),
            "aggregate_hash_bytes": aggregate_hash_bytes,
            "hash_size_bits": 64,
        }

    def fingerprint(self, video_path: str) -> dict[str, Any]:
        return self._fingerprint_for_path(video_path)


class _FakeAudioFingerprinter:
    def __init__(self) -> None:
        self.embedding_dim = 8

    def fingerprint(self, audio_path: str) -> dict[str, Any]:
        content = Path(audio_path).read_bytes()
        digest = hashlib.sha256(content).digest()
        arr = np.frombuffer(digest[: self.embedding_dim], dtype=np.uint8).astype(np.float32)
        emb = arr / (np.linalg.norm(arr) + 1e-6)
        fingerprint_id = hashlib.sha1(content).hexdigest()[:16]
        return {
            "embedding": emb.astype(np.float32),
            "embedding_dim": self.embedding_dim,
            "fingerprint_id": fingerprint_id,
            "top_landmarks": [],
        }


def _install_fingerprinter_stubs() -> None:
    fake_mod = types.ModuleType("app.fingerprinters")
    fake_mod.ImageFingerprinter = _FakeImageFingerprinter
    fake_mod.VideoFingerprinter = _FakeVideoFingerprinter
    fake_mod.AudioFingerprinter = _FakeAudioFingerprinter
    fake_mod.SemanticEmbedder = _FakeSemanticEmbedder
    sys.modules["app.fingerprinters"] = fake_mod
    sys.modules["decision_layer.app.fingerprinters"] = fake_mod


def _load_main_module() -> Any:
    _install_fingerprinter_stubs()
    if "decision_layer.app.main" in sys.modules:
        del sys.modules["decision_layer.app.main"]
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    try:
        return importlib.import_module("decision_layer.app.main")
    except ModuleNotFoundError:
        return importlib.import_module("app.main")


class _GraphDBSpy:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def upsert_asset_context(self, asset_id: str, metadata: dict[str, Any], neighbors: list[dict[str, Any]]) -> None:
        self.calls.append({"asset_id": asset_id, "metadata": metadata, "neighbors": neighbors})


@pytest.mark.asyncio
async def test_register_endpoints_rights_context_wiring_and_qdrant_matching(tmp_path: Path) -> None:
    main = _load_main_module()

    client = qdrant_client.QdrantClient(path=str(tmp_path / "qdrant_contract"))
    registry = RegistryManager(
        audio_dim=8,
        semantic_dim=512,
        qdrant_client=client,
        semantic_collection_name="semantic_assets_contract",
    )

    graph_spy = _GraphDBSpy()
    main.app.state.registry = registry
    main.app.state.graph_db = graph_spy

    # Seed records to guarantee pre-registration match hits and neighbor wiring.
    image_bytes = b"image-contract-payload"
    semantic_seed = main.semantic_fp.embed_from_bytes(image_bytes)
    registry.register_semantic(
        asset_id="seed-image",
        embedding=semantic_seed["embedding"],
        metadata={
            "modality": "image",
            "is_flagged": True,
            "flagged_weight": 1.9,
            "flagged_case_id": "case-123",
            "flagged_evidence_source": "historical_case",
            "flagged_confidence": 0.92,
        },
    )

    video_bytes = b"video-contract-payload"
    video_tmp = tmp_path / "seed_video.bin"
    video_tmp.write_bytes(video_bytes)
    video_seed = _FakeVideoFingerprinter._fingerprint_for_path(str(video_tmp))
    registry.register_video(
        asset_id="seed-video",
        hash_bytes=video_seed["aggregate_hash_bytes"],
        hash_records=video_seed["segment_hash_records"],
        metadata={
            "modality": "video",
            "is_flagged": True,
            "flagged_weight": 1.7,
            "flagged_case_id": "case-456",
            "flagged_evidence_source": "ops_review",
            "flagged_confidence": 0.88,
        },
    )

    audio_bytes = b"audio-contract-payload"
    audio_tmp = tmp_path / "seed_audio.bin"
    audio_tmp.write_bytes(audio_bytes)
    audio_seed = main.audio_fp.fingerprint(str(audio_tmp))
    registry.register_audio(
        asset_id="seed-audio",
        embedding=audio_seed["embedding"],
        metadata={
            "modality": "audio",
            "is_flagged": True,
            "flagged_weight": 1.6,
            "flagged_case_id": "case-789",
            "flagged_evidence_source": "audit_event",
            "flagged_confidence": 0.86,
        },
    )

    rights_ctx = {
        "schema_version": 2,
        "protected_work": True,
        "is_flagged": False,
        "creator": {
            "creator_id": "creator-001",
            "verified": True,
            "trust_score": 0.91,
            "tenure_months": 48,
            "registered_works": 123,
            "active_licenses": 27,
        },
        "licensee": {
            "licensee_id": "licensee-001",
            "jurisdiction": "US",
            "active_license_count": 9,
            "license_status": 1.0,
        },
        "license_terms": {
            "license_type": "sync",
            "expires_at": "2099-12-31",
            "territory": "US",
            "jurisdiction": "US",
            "derivative_allowed": True,
            "commercial_use": True,
            "active": True,
        },
    }

    image_resp = await main.fingerprint_image(
        file=UploadFile(filename="contract.png", file=BytesIO(image_bytes)),
        register=True,
        asset_id="asset-image-contract",
        source="pytest",
        rights_context_json=json.dumps(rights_ctx),
    )
    assert image_resp.registered is True
    assert image_resp.asset_id == "asset-image-contract"

    semantic_resp = await main.fingerprint_semantic_image(
        file=UploadFile(filename="contract-sem.png", file=BytesIO(image_bytes)),
        register=True,
        asset_id="asset-semantic-contract",
        source="pytest",
        rights_context_json=json.dumps(rights_ctx),
    )
    assert semantic_resp["registered"] is True
    assert semantic_resp["asset_id"] == "asset-semantic-contract"

    video_resp = await main.fingerprint_video(
        file=UploadFile(filename="contract.mp4", file=BytesIO(video_bytes)),
        register=True,
        asset_id="asset-video-contract",
        source="pytest",
        rights_context_json=json.dumps(rights_ctx),
    )
    assert video_resp.registered is True
    assert video_resp.asset_id == "asset-video-contract"

    audio_resp = await main.fingerprint_audio(
        file=UploadFile(filename="contract.wav", file=BytesIO(audio_bytes)),
        register=True,
        asset_id="asset-audio-contract",
        source="pytest",
        rights_context_json=json.dumps(rights_ctx),
    )
    assert audio_resp.registered is True
    assert audio_resp.asset_id == "asset-audio-contract"

    # Verify graph sync contracts: full rights metadata + edge/neighbor attributes.
    assert len(graph_spy.calls) == 4
    required_metadata_keys = {
        "modality",
        "content_type",
        "source",
        "filename",
        "protected_work",
        "schema_version",
        "embedding_vector",
        "fingerprint_hash",
        "fingerprint_kind",
        "creator_id",
        "creator_trust_score",
        "creator_tenure_months",
        "creator_verified",
        "creator_registered_works",
        "creator_active_licenses",
        "licensee_id",
        "licensee_jurisdiction",
        "licensee_active_license_count",
        "license_status",
        "license_type",
        "license_expires_at",
        "license_territory",
        "license_jurisdiction",
        "license_derivative_allowed",
        "license_commercial_use",
        "license_active",
    }
    required_neighbor_keys = {
        "asset_id",
        "similarity",
        "is_flagged",
        "modality",
        "flagged_weight",
        "model_name",
        "model_version",
        "threshold",
        "match_context",
        "updated_at",
        "evidence_source",
        "case_id",
        "confidence",
    }

    for call in graph_spy.calls:
        assert required_metadata_keys.issubset(call["metadata"].keys())
        assert call["neighbors"], "Expected pre-registration matching to produce at least one neighbor"
        assert required_neighbor_keys.issubset(call["neighbors"][0].keys())

    # Qdrant round-trip still works after endpoint registration.
    image_hash = main.image_fp.fingerprint_from_bytes(image_bytes)
    image_matches = registry.match_image(image_hash["hash_bytes"], top_k=8)
    assert any(m.asset_id == "asset-image-contract" for m in image_matches)

    semantic_matches = registry.match_semantic(semantic_seed["embedding"], top_k=8, modality_filter="image")
    assert any(m.asset_id == "asset-semantic-contract" for m in semantic_matches)

    video_matches = registry.match_video_robust(video_seed["segment_hash_records"], top_k=8)
    assert any(m.asset_id == "asset-video-contract" for m in video_matches)

    audio_matches = registry.match_audio(audio_seed["embedding"], top_k=8)
    assert any(m.asset_id == "asset-audio-contract" for m in audio_matches)

    client.close()


def test_policy_rules_flow_into_graph_features_and_model_inputs() -> None:
    builder = GraphBuilder(graph_db=None)
    model = RightsGNN()

    query_embedding = np.linspace(0.0, 1.0, 512, dtype=np.float32)
    query_metadata = {
        "asset_id": "query-policy-asset",
        "modality": "image",
        "content_type": "image",
        "protected_work": True,
        "creator_id": "creator-query",
        "creator_verified": True,
        "licensee_id": "licensee-query",
        "license_status": 1.0,
        "license_active": True,
        "requested_territory": "US",
        "is_derivative": True,
    }

    qdrant_results = [
        {
            "asset_id": "neighbor-policy-asset",
            "score": 0.93,
            "metadata": {
                "modality": "image",
                "content_type": "image",
                "protected_work": True,
                "creator_id": "creator-neighbor",
                "creator_verified": True,
                "creator_tenure_months": 30,
                "creator_registered_works": 17,
                "creator_active_licenses": 4,
                "creator_trust_score": 0.87,
                "licensee_id": "licensee-neighbor",
                "license_status": 1.0,
                "license_active": True,
                "licensee_jurisdiction": "US",
                "licensee_active_license_count": 2,
                # Policy rules that should deactivate the effective license features.
                "license_expires_at": "2001-01-01",
                "license_territory": "EU",
                "license_derivative_allowed": False,
                "semantic_embedding": np.linspace(1.0, 0.0, 512, dtype=np.float32).tolist(),
            },
        }
    ]

    data = builder.build_subgraph(
        query_embedding=query_embedding,
        qdrant_results=qdrant_results,
        query_metadata=query_metadata,
    )

    licensee_ids = list(getattr(data["Licensee"], "node_ids", []))
    assert "licensee-neighbor" in licensee_ids
    blocked_idx = licensee_ids.index("licensee-neighbor")

    # Licensee features = [effective_status, jurisdiction_hash, active_count_norm, effective_active]
    blocked_licensee_features = data["Licensee"].x[blocked_idx]
    assert float(blocked_licensee_features[0].item()) == 0.0
    assert float(blocked_licensee_features[3].item()) == 0.0

    x_dict = {k: v.x for k, v in data.node_items()}
    edge_index_dict = {k: v.edge_index for k, v in data.edge_items()}

    infringement_logit, attribution_logits, hidden = model(
        x_dict=x_dict,
        edge_index_dict=edge_index_dict,
        query_asset_index=0,
    )

    assert model.licensee_proj.in_features == int(data["Licensee"].x.shape[1])
    assert torch.isfinite(infringement_logit).item() is True
    assert attribution_logits.ndim == 1
    assert hidden["Asset"].shape[1] == model.out_dim
