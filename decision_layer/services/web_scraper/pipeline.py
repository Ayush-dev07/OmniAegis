from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
	from decision_layer.app.reasoning.graph_builder import GraphBuilder
	from decision_layer.app.reasoning.reasoning_gate import DecisionLabel, ReasoningGate
	from decision_layer.app.registry import RegistryManager
except ModuleNotFoundError:  # pragma: no cover
	from app.reasoning.graph_builder import GraphBuilder
	from app.reasoning.reasoning_gate import DecisionLabel, ReasoningGate
	from app.registry import RegistryManager

from .text_embedding import TextEmbeddingEncoder


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebCandidateDecision:
	asset_id: str
	decision: str
	confidence: float
	infringement_probability: float
	semantic_matches: list[dict[str, Any]]
	query_metadata: dict[str, Any]
	reasoning: dict[str, float]


class WebCandidateProcessor:
	"""Wire web scraper output into semantic retrieval and graph authorization."""

	def __init__(self, registry: RegistryManager, graph_builder: GraphBuilder | None = None, reasoner: ReasoningGate | None = None) -> None:
		self.registry = registry
		self.graph_builder = graph_builder or GraphBuilder(graph_db=getattr(graph_builder, "graph_db", None))
		self.reasoner = reasoner or ReasoningGate(graph_builder=self.graph_builder)
		self.text_embedder = TextEmbeddingEncoder(embedding_dim=512)

	@staticmethod
	def _normalize_metadata(candidate: dict[str, Any]) -> dict[str, Any]:
		metadata = dict(candidate)
		raw_nested = metadata.get("metadata")
		if isinstance(raw_nested, str):
			try:
				nested = json.loads(raw_nested)
				if isinstance(nested, dict):
					metadata = {**nested, **metadata}
			except json.JSONDecodeError:
				pass
		elif isinstance(raw_nested, dict):
			metadata = {**raw_nested, **metadata}
		return metadata

	@staticmethod
	def _stringify_hits(keyword_hits: Any) -> dict[str, int]:
		if isinstance(keyword_hits, dict):
			out: dict[str, int] = {}
			for key, value in keyword_hits.items():
				try:
					out[str(key)] = int(value)
				except (TypeError, ValueError):
					continue
			return out
		return {}

	def _build_text(self, candidate: dict[str, Any]) -> str:
		parts = [
			str(candidate.get("title") or ""),
			str(candidate.get("excerpt") or ""),
			str(candidate.get("text") or ""),
			str(candidate.get("canonical_url") or candidate.get("url") or ""),
			str(candidate.get("source_url") or ""),
		]
		return "\n".join(part for part in parts if part)

	def _build_query_metadata(self, candidate: dict[str, Any], embedding: np.ndarray) -> dict[str, Any]:
		metadata = {
			"asset_id": str(candidate.get("asset_id") or candidate.get("content_digest") or candidate.get("canonical_url") or candidate.get("url") or "unknown"),
			"modality": "web",
			"source": candidate.get("source_url") or candidate.get("url"),
			"source_url": candidate.get("source_url") or candidate.get("url"),
			"canonical_url": candidate.get("canonical_url") or candidate.get("url"),
			"filename": candidate.get("title") or candidate.get("canonical_url") or candidate.get("url"),
			"content_type": candidate.get("content_type"),
			"source_tier": candidate.get("tier"),
			"crawl_depth": candidate.get("depth"),
			"keyword_hits": self._stringify_hits(candidate.get("keyword_hits")),
			"score": float(candidate.get("score", 0.0)),
			"status_code": int(candidate.get("status_code", 0) or 0),
			"content_digest": candidate.get("content_digest"),
			"semantic_embedding": embedding.astype(np.float32).tolist(),
			"is_flagged": False,
		}
		for key in ("creator_id", "licensee_id", "license_status", "creator_trust_score", "creator_tenure_months", "creator_verified"):
			if key in candidate and candidate.get(key) is not None:
				metadata[key] = candidate.get(key)
		return metadata

	def _decision_from_reasoning(self, reasoning: Any, source_tier: str | None) -> tuple[str, dict[str, float]]:
		probabilities = getattr(reasoning, "probabilities", None) or {}
		if hasattr(reasoning, "label"):
			label = reasoning.label
		else:
			label = DecisionLabel.AUTHORIZED

		if label == DecisionLabel.AUTHORIZED:
			return "allow", probabilities
		if label == DecisionLabel.INFRINGING:
			return "block", probabilities
		if source_tier == "tier_0":
			return "allow", probabilities
		return "hitl", probabilities

	@staticmethod
	def _authorization_status(decision: str, source_tier: str | None) -> str:
		if decision == "allow":
			return "authorized" if source_tier == "tier_0" else "allowed"
		if decision == "block":
			return "unauthorized"
		return "pending_review"

	def process_candidate(self, candidate: dict[str, Any], top_k: int = 10) -> WebCandidateDecision:
		normalized = self._normalize_metadata(candidate)
		text = self._build_text(normalized)
		embedding = self.text_embedder.embed_text(text)
		asset_id = str(normalized.get("asset_id") or normalized.get("content_digest") or normalized.get("canonical_url") or normalized.get("url") or "unknown")
		query_metadata = self._build_query_metadata(normalized, embedding)

		self.registry.register_semantic(asset_id=asset_id, embedding=embedding, metadata=query_metadata)
		semantic_matches = self.registry.match_semantic(
			embedding=embedding,
			top_k=top_k,
			modality_filter="web",
		)

		graph = self.graph_builder.build_subgraph(
			query_embedding=embedding,
			qdrant_results=semantic_matches,
			query_metadata=query_metadata,
		)
		reasoning = self.reasoner.reason_about_asset(
			asset_embedding=embedding,
			qdrant_results=semantic_matches,
			query_metadata=query_metadata,
		)

		decision, probabilities = self._decision_from_reasoning(reasoning, source_tier=str(normalized.get("tier") or ""))
		authorization_status = self._authorization_status(decision, source_tier=str(normalized.get("tier") or ""))
		query_metadata["decision"] = decision
		query_metadata["decision_label"] = getattr(getattr(reasoning, "label", None), "name", None)
		query_metadata["decision_confidence"] = float(reasoning.confidence)
		query_metadata["infringement_probability"] = float(
			probabilities.get("infringing", getattr(reasoning, "confidence", 0.0))
		)
		query_metadata["is_flagged"] = decision == "block"
		query_metadata["authorization_status"] = authorization_status
		query_metadata["reasoning_label"] = getattr(getattr(reasoning, "label", None), "name", None)

		if getattr(self.graph_builder, "graph_db", None) is not None:
			try:
				self.graph_builder.graph_db.upsert_asset_context(
					asset_id=asset_id,
					metadata=query_metadata,
					neighbors=[
						{
							"asset_id": m.asset_id,
							"similarity": m.distance_or_similarity,
							"is_flagged": bool(m.metadata.get("is_flagged", False)),
							"modality": m.metadata.get("modality"),
							"flagged_weight": float(m.metadata.get("flagged_weight", 1.5)),
						}
						for m in semantic_matches
					],
				)
			except Exception:
				logger.debug("Neo4j update failed for web asset_id=%s", asset_id)

		if self.registry.qdrant is not None:
			logger.debug("Web candidate graph built for asset_id=%s nodes=%s", asset_id, len(graph["Asset"].node_ids))

		return WebCandidateDecision(
			asset_id=asset_id,
			decision=decision,
			confidence=float(reasoning.confidence),
			infringement_probability=float(query_metadata["infringement_probability"]),
			semantic_matches=[m.metadata | {"asset_id": m.asset_id, "confidence": m.confidence, "score": m.distance_or_similarity} for m in semantic_matches],
			query_metadata=query_metadata,
			reasoning={
				"innocent": float(probabilities.get("innocent", 0.0)),
				"authorized": float(probabilities.get("authorized", 0.0)),
				"infringing": float(probabilities.get("infringing", 0.0)),
			},
		)
