from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase


class GraphDBService:
    """Neo4j wrapper with connection pooling and lightweight helpers."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str | None = None,
        max_connection_pool_size: int = 20,
    ) -> None:
        self.uri = uri
        self.database = database
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=max_connection_pool_size,
        )

    @staticmethod
    def _get_env_or_dotenv(key: str) -> str:
        direct = str(os.getenv(key, "")).strip()
        if direct:
            return direct

        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            return ""

        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                raw = line.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                if k.strip() != key:
                    continue
                return v.strip().strip('"').strip("'")
        except Exception:
            return ""

        return ""

    @classmethod
    def from_env(cls) -> GraphDBService:
        uri = cls._get_env_or_dotenv("NEO4J_URI")
        if not uri:
            raise ValueError("Missing NEO4J_URI. Use Aura URI format: neo4j+s://<db-id>.databases.neo4j.io")
        if uri.startswith("bolt://") or "localhost" in uri:
            raise ValueError("Local Neo4j URI is not supported. Configure Aura URI: neo4j+s://<db-id>.databases.neo4j.io")

        # Prefer shared settings key (`NEO4J_USERNAME`) with legacy fallback (`NEO4J_USER`).
        user = cls._get_env_or_dotenv("NEO4J_USERNAME") or cls._get_env_or_dotenv("NEO4J_USER")
        if not user:
            raise ValueError("Missing Neo4j username. Set NEO4J_USERNAME")

        password = cls._get_env_or_dotenv("NEO4J_PASSWORD")
        if not password:
            raise ValueError("Missing NEO4J_PASSWORD")

        database = cls._get_env_or_dotenv("NEO4J_DATABASE") or None
        pool_size = int(cls._get_env_or_dotenv("NEO4J_POOL_SIZE") or "20")
        return cls(uri=uri, user=user, password=password, database=database, max_connection_pool_size=pool_size)

    def close(self) -> None:
        self.driver.close()

    def run_migrations(self) -> None:
        queries = [
            "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE",
            "CREATE CONSTRAINT creator_id_unique IF NOT EXISTS FOR (c:Creator) REQUIRE c.creator_id IS UNIQUE",
            "CREATE CONSTRAINT licensee_id_unique IF NOT EXISTS FOR (l:Licensee) REQUIRE l.licensee_id IS UNIQUE",
            "CREATE INDEX asset_modality_idx IF NOT EXISTS FOR (a:Asset) ON (a.modality)",
            "CREATE INDEX asset_content_type_idx IF NOT EXISTS FOR (a:Asset) ON (a.content_type)",
            "CREATE INDEX asset_protected_work_idx IF NOT EXISTS FOR (a:Asset) ON (a.protected_work)",
            "CREATE INDEX creator_verified_idx IF NOT EXISTS FOR (c:Creator) ON (c.verified)",
            "CREATE INDEX licensee_jurisdiction_idx IF NOT EXISTS FOR (l:Licensee) ON (l.jurisdiction)",
            "CREATE INDEX license_active_idx IF NOT EXISTS FOR ()-[r:LICENSED_TO]-() ON (r.active)",
        ]
        with self.driver.session(database=self.database) as session:
            for q in queries:
                session.run(q)

    def upsert_asset_context(
        self,
        asset_id: str,
        metadata: dict[str, Any],
        neighbors: list[dict[str, Any]] | None = None,
    ) -> None:
        neighbors = neighbors or []

        creator = dict(metadata.get("creator") or {})
        licensee = dict(metadata.get("licensee") or {})
        license_terms = dict(metadata.get("license_terms") or {})

        creator_id = metadata.get("creator_id") or creator.get("creator_id")
        licensee_id = metadata.get("licensee_id") or licensee.get("licensee_id")

        creator_verified = bool(metadata.get("creator_verified", creator.get("verified", False)))
        creator_trust_score = float(metadata.get("creator_trust_score", creator.get("trust_score", 0.5)))
        creator_tenure_months = float(metadata.get("creator_tenure_months", creator.get("tenure_months", 12.0)))
        creator_registered_works = int(metadata.get("creator_registered_works", creator.get("registered_works", 0)))
        creator_active_licenses = int(metadata.get("creator_active_licenses", creator.get("active_licenses", 0)))

        license_status = float(metadata.get("license_status", licensee.get("license_status", 0.0)))
        licensee_jurisdiction = str(metadata.get("licensee_jurisdiction", licensee.get("jurisdiction", "")) or "")
        licensee_active_license_count = int(
            metadata.get("licensee_active_license_count", licensee.get("active_license_count", 0))
        )

        license_type = str(metadata.get("license_type", license_terms.get("license_type", "")) or "")
        license_expires_at = str(metadata.get("license_expires_at", license_terms.get("expires_at", "")) or "")
        license_territory = str(metadata.get("license_territory", license_terms.get("territory", "")) or "")
        license_jurisdiction = str(
            metadata.get("license_jurisdiction", license_terms.get("jurisdiction", licensee_jurisdiction)) or ""
        )
        license_derivative_allowed = bool(
            metadata.get("license_derivative_allowed", license_terms.get("derivative_allowed", False))
        )
        license_commercial_use = bool(metadata.get("license_commercial_use", license_terms.get("commercial_use", False)))
        license_active = bool(metadata.get("license_active", license_terms.get("active", False)))

        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MERGE (a:Asset {asset_id: $asset_id})
                SET a.modality = $modality,
                    a.content_type = $content_type,
                    a.source = $source,
                    a.filename = $filename,
                    a.is_flagged = $is_flagged,
                    a.protected_work = $protected_work,
                    a.embedding_vector = $embedding_vector,
                    a.fingerprint_hash = $fingerprint_hash,
                    a.fingerprint_kind = $fingerprint_kind,
                    a.registered_at = $registered_at,
                    a.schema_version = $schema_version
                """,
                asset_id=asset_id,
                modality=metadata.get("modality"),
                content_type=metadata.get("content_type", metadata.get("modality")),
                source=metadata.get("source"),
                filename=metadata.get("filename"),
                is_flagged=bool(metadata.get("is_flagged", False)),
                protected_work=bool(metadata.get("protected_work", False)),
                embedding_vector=metadata.get("embedding_vector"),
                fingerprint_hash=metadata.get("fingerprint_hash"),
                fingerprint_kind=metadata.get("fingerprint_kind"),
                registered_at=metadata.get("registered_at"),
                schema_version=int(metadata.get("schema_version", 1)),
            )

            if creator_id:
                session.run(
                    """
                    MERGE (c:Creator {creator_id: $creator_id})
                    SET c.trust_score = $trust_score,
                        c.tenure_months = $tenure_months,
                        c.verified = $verified,
                        c.registered_works = $registered_works,
                        c.active_licenses = $active_licenses
                    WITH c
                    MATCH (a:Asset {asset_id: $asset_id})
                    MERGE (a)-[:CREATED_BY]->(c)
                    """,
                    asset_id=asset_id,
                    creator_id=str(creator_id),
                    trust_score=creator_trust_score,
                    tenure_months=creator_tenure_months,
                    verified=creator_verified,
                    registered_works=creator_registered_works,
                    active_licenses=creator_active_licenses,
                )

            if licensee_id:
                session.run(
                    """
                    MERGE (l:Licensee {licensee_id: $licensee_id})
                    SET l.license_status = $license_status,
                        l.jurisdiction = $jurisdiction,
                        l.active_license_count = $active_license_count
                    WITH l
                    MATCH (a:Asset {asset_id: $asset_id})
                    MERGE (a)-[r:LICENSED_TO]->(l)
                    SET r.license_type = $license_type,
                        r.expires_at = $license_expires_at,
                        r.territory = $license_territory,
                        r.jurisdiction = $license_jurisdiction,
                        r.derivative_allowed = $license_derivative_allowed,
                        r.commercial_use = $license_commercial_use,
                        r.active = $license_active
                    """,
                    asset_id=asset_id,
                    licensee_id=str(licensee_id),
                    license_status=license_status,
                    jurisdiction=licensee_jurisdiction,
                    active_license_count=licensee_active_license_count,
                    license_type=license_type,
                    license_expires_at=license_expires_at,
                    license_territory=license_territory,
                    license_jurisdiction=license_jurisdiction,
                    license_derivative_allowed=license_derivative_allowed,
                    license_commercial_use=license_commercial_use,
                    license_active=license_active,
                )

            for n in neighbors:
                n_id = str(n.get("asset_id", ""))
                if not n_id:
                    continue
                session.run(
                    """
                    MERGE (n:Asset {asset_id: $neighbor_asset_id})
                    SET n.modality = coalesce($modality, n.modality)
                    WITH n
                    MATCH (a:Asset {asset_id: $asset_id})
                    MERGE (a)-[r:SIMILAR_TO]->(n)
                    SET r.weight = $weight,
                        r.model_name = $model_name,
                        r.model_version = $model_version,
                        r.threshold = $threshold,
                        r.match_context = $match_context,
                        r.updated_at = $updated_at
                    """,
                    asset_id=asset_id,
                    neighbor_asset_id=n_id,
                    modality=n.get("modality"),
                    weight=float(n.get("similarity", 0.0)),
                    model_name=n.get("model_name", "default"),
                    model_version=n.get("model_version", "1"),
                    threshold=float(n.get("threshold", 0.0)),
                    match_context=n.get("match_context", "ingestion"),
                    updated_at=n.get("updated_at"),
                )
                if bool(n.get("is_flagged", False)):
                    session.run(
                        """
                        MATCH (a:Asset {asset_id: $asset_id})
                        MATCH (n:Asset {asset_id: $neighbor_asset_id})
                        MERGE (a)-[f:FLAGGED_WITH]->(n)
                        SET f.weight = $weight,
                            f.evidence_source = $evidence_source,
                            f.case_id = $case_id,
                            f.timestamp_ms = $timestamp_ms,
                            f.confidence = $confidence
                        """,
                        asset_id=asset_id,
                        neighbor_asset_id=n_id,
                        weight=float(n.get("flagged_weight", 1.5)),
                        evidence_source=n.get("evidence_source", "unknown"),
                        case_id=n.get("case_id"),
                        timestamp_ms=n.get("timestamp_ms"),
                        confidence=float(n.get("confidence", 1.0)),
                    )

    def link_flagged_assets(
        self,
        asset_id: str,
        related_asset_id: str,
        confidence: float = 1.0,
        evidence_source: str = "enforcement_action",
        case_id: str | None = None,
        timestamp_ms: int | None = None,
        weight: float = 1.5,
    ) -> None:
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MERGE (a:Asset {asset_id: $asset_id})
                MERGE (b:Asset {asset_id: $related_asset_id})
                MERGE (a)-[f:FLAGGED_WITH]->(b)
                SET f.weight = $weight,
                    f.confidence = $confidence,
                    f.evidence_source = $evidence_source,
                    f.case_id = $case_id,
                    f.timestamp_ms = $timestamp_ms
                """,
                asset_id=asset_id,
                related_asset_id=related_asset_id,
                weight=float(weight),
                confidence=float(confidence),
                evidence_source=evidence_source,
                case_id=case_id,
                timestamp_ms=timestamp_ms,
            )

    def fetch_asset_neighborhood(self, asset_id: str, limit_assets: int = 64) -> dict[str, Any]:
        with self.driver.session(database=self.database) as session:
            records = session.run(
                """
                MATCH (q:Asset {asset_id: $asset_id})
                OPTIONAL MATCH (q)-[s:SIMILAR_TO]->(a1:Asset)
                OPTIONAL MATCH (a1)-[s2:SIMILAR_TO]->(a2:Asset)
                WITH q, collect(DISTINCT a1) + collect(DISTINCT a2) AS asset_nodes
                WITH q, [x IN asset_nodes WHERE x IS NOT NULL][..$limit_assets] AS assets

                UNWIND assets AS a
                OPTIONAL MATCH (a)-[:CREATED_BY]->(c:Creator)
                OPTIONAL MATCH (a)-[:LICENSED_TO]->(l:Licensee)
                OPTIONAL MATCH (q)-[sim:SIMILAR_TO]->(a)
                OPTIONAL MATCH (q)-[flg:FLAGGED_WITH]->(a)
                RETURN q.asset_id AS query_asset_id,
                       collect(DISTINCT {
                           asset_id: a.asset_id,
                           modality: a.modality,
                           content_type: a.content_type,
                           protected_work: coalesce(a.protected_work, false),
                           source: a.source,
                           filename: a.filename,
                           is_flagged: coalesce(a.is_flagged, false),
                           fingerprint_hash: a.fingerprint_hash,
                           fingerprint_kind: a.fingerprint_kind,
                           creator_id: c.creator_id,
                           creator_trust_score: coalesce(c.trust_score, 0.5),
                           creator_tenure_months: coalesce(c.tenure_months, 12.0),
                           creator_verified: coalesce(c.verified, false),
                           creator_registered_works: coalesce(c.registered_works, 0),
                           creator_active_licenses: coalesce(c.active_licenses, 0),
                           licensee_id: l.licensee_id,
                           licensee_jurisdiction: coalesce(l.jurisdiction, ''),
                           licensee_active_license_count: coalesce(l.active_license_count, 0),
                           license_status: coalesce(l.license_status, 0.0),
                           similarity: coalesce(sim.weight, 0.0),
                           similarity_threshold: coalesce(sim.threshold, 0.0),
                           similarity_model_name: coalesce(sim.model_name, 'default'),
                           license_type: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.license_type])[0], ''),
                           license_expires_at: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.expires_at])[0], ''),
                           license_territory: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.territory])[0], ''),
                           license_jurisdiction: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.jurisdiction])[0], ''),
                           license_derivative_allowed: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.derivative_allowed])[0], false),
                           license_commercial_use: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.commercial_use])[0], false),
                           license_active: coalesce(([(a)-[lic:LICENSED_TO]->(l) | lic.active])[0], false),
                           flagged_weight: coalesce(flg.weight, 0.0),
                           flagged_confidence: coalesce(flg.confidence, 0.0),
                           flagged_case_id: coalesce(flg.case_id, ''),
                           flagged_evidence_source: coalesce(flg.evidence_source, '')
                       }) AS neighbors
                """,
                asset_id=asset_id,
                limit_assets=limit_assets,
            )
            row = records.single()

        if row is None:
            return {"query_asset_id": asset_id, "neighbors": []}

        return {
            "query_asset_id": row["query_asset_id"],
            "neighbors": [n for n in (row["neighbors"] or []) if n.get("asset_id")],
        }
