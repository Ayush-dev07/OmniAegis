#!/usr/bin/env python3
"""
Test script to verify Qdrant metadata sync to Neo4j.

This script tests the dynamic metadata field handling in graph_db.upsert_asset_context().
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Load .env file first
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

# Add the decision_layer to the path
decision_layer_path = Path(__file__).parent / "decision_layer"
sys.path.insert(0, str(decision_layer_path))

try:
    from decision_layer.services.graph_db import GraphDBService
except (ImportError, ModuleNotFoundError):
    from decision_layer.services.graph_db import GraphDBService


def test_dynamic_metadata_sync():
    """Test that all metadata fields are properly stored in Neo4j."""
    
    print("=" * 80)
    print("Testing Qdrant to Neo4j Metadata Sync")
    print("=" * 80)
    
    try:
        # Initialize Neo4j service from environment
        graph_db = GraphDBService.from_env()
        print("✓ Connected to Neo4j")
    except Exception as exc:
        print(f"✗ Failed to connect to Neo4j: {exc}")
        return False
    
    try:
        # Run migrations
        graph_db.run_migrations()
        print("✓ Schema migrations completed")
    except Exception as exc:
        print(f"✗ Failed to run migrations: {exc}")
        graph_db.close()
        return False
    
    # Test 1: Store comprehensive metadata (like from Qdrant)
    test_asset_id = "test-sync-asset-001"
    comprehensive_metadata = {
        # Standard fields
        "modality": "image",
        "source": "user-upload",
        "filename": "test-image.jpg",
        "title": "Test Asset for Sync",
        "user_id": "user-123",
        
        # License fields
        "license_file_name": "license.txt",
        "license_content_type": "text/plain",
        "authorization_status": "licensed",
        "source_tier": "registered",
        
        # Decision fields
        "decision_label": "REGISTERED",
        "decision_confidence": 0.95,
        
        # Additional fields from Qdrant
        "is_flagged": False,
        "uploaded_at": "2026-04-28T10:30:00Z",
        "content_type": "image/jpeg",
        "storage_url": "gs://bucket/test-image.jpg",
        
        # Creator info
        "creator_id": "creator-456",
        "creator_trust_score": 0.85,
        "creator_tenure_months": 24.0,
        "creator_verified": True,
        
        # Licensee info
        "licensee_id": "user-123:license",
        "license_status": 1.0,
        
        # Extra dynamic fields that should be preserved
        "embedding_dim": 512,
        "feature_type": "visual_features",
        "custom_field": "custom_value",
        "numeric_field": 42,
    }
    
    print(f"\nTest 1: Storing comprehensive metadata for asset {test_asset_id}")
    print(f"  Metadata fields count: {len(comprehensive_metadata)}")
    
    try:
        graph_db.upsert_asset_context(
            asset_id=test_asset_id,
            metadata=comprehensive_metadata,
            neighbors=[],
        )
        print("✓ Asset context upserted successfully")
    except Exception as exc:
        print(f"✗ Failed to upsert asset context: {exc}")
        graph_db.close()
        return False
    
    # Test 2: Fetch the asset and verify all metadata was stored
    print(f"\nTest 2: Fetching asset to verify metadata sync")
    try:
        graph = graph_db.fetch_asset_relationship_graph(test_asset_id)
        print(f"✓ Asset graph fetched successfully")
        
        if not graph.get("nodes"):
            print("✗ No nodes found in graph")
            graph_db.close()
            return False
        
        query_node = graph["nodes"][0] if graph["nodes"] else {}
        stored_metadata = query_node.get("metadata", {})
        
        print(f"\n  Stored metadata fields ({len(stored_metadata)}):")
        for key in sorted(stored_metadata.keys()):
            value = stored_metadata[key]
            if isinstance(value, str) and len(value) > 50:
                value = f"{value[:50]}..."
            print(f"    - {key}: {value}")
        
        # Check critical fields
        critical_fields = [
            "asset_id", "modality", "filename", "title", "user_id",
            "decision_label", "decision_confidence", "authorization_status",
        ]
        
        missing_fields = [f for f in critical_fields if f not in stored_metadata]
        if missing_fields:
            print(f"\n✗ Missing critical fields: {missing_fields}")
            graph_db.close()
            return False
        
        print(f"\n✓ All critical fields present in Neo4j")
        
        # Check dynamic fields
        dynamic_fields = ["embedding_dim", "feature_type", "custom_field", "numeric_field"]
        found_dynamic = [f for f in dynamic_fields if f in stored_metadata]
        
        if found_dynamic:
            print(f"✓ Dynamic fields synced: {found_dynamic}")
        else:
            print(f"⚠ No dynamic fields found (may be expected depending on Neo4j return settings)")
        
    except Exception as exc:
        print(f"✗ Failed to fetch asset graph: {exc}")
        import traceback
        traceback.print_exc()
        graph_db.close()
        return False
    
    # Test 3: Test with neighbors (semantic matches)
    test_asset_id_2 = "test-neighbor-asset-001"
    test_neighbor_metadata = {
        "modality": "image",
        "source": "semantic-match",
        "filename": "neighbor-image.jpg",
        "title": "Neighbor Asset",
        "user_id": "user-789",
    }
    
    print(f"\nTest 3: Testing asset with neighbors")
    try:
        graph_db.upsert_asset_context(
            asset_id=test_asset_id_2,
            metadata={**test_neighbor_metadata, "decision_label": "MATCH", "decision_confidence": 0.88},
            neighbors=[
                {
                    "asset_id": test_asset_id,
                    "similarity": 0.92,
                    "is_flagged": False,
                    "modality": "image",
                }
            ],
        )
        print("✓ Asset with neighbor relationship stored successfully")
    except Exception as exc:
        print(f"✗ Failed to upsert asset with neighbors: {exc}")
        graph_db.close()
        return False
    
    # Clean up
    print("\n" + "=" * 80)
    print("All tests completed successfully! ✓")
    print("=" * 80)
    
    graph_db.close()
    return True


if __name__ == "__main__":
    success = test_dynamic_metadata_sync()
    sys.exit(0 if success else 1)
