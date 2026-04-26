"""Unit tests for Stage-7 explainability utilities.

Covers:
- Visual explanation heatmap generation and region extraction.
- Graph SHAP explanation pathway over GNN-style outputs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.data import HeteroData


# Add decision_layer package root to path
DECISION_LAYER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

from app.reasoning.explainers import GraphExplainer, VisualExplainer


class _TinyFeatureExtractor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 4, kernel_size=1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(self.conv(x))


class _TinySemanticEmbedder:
    def __init__(self) -> None:
        self.feature_extractor = _TinyFeatureExtractor().eval()
        self.projection = nn.Linear(4, 8).eval()
        self.transform = None


class _DummyRightsModel(nn.Module):
    """Simple deterministic model compatible with GraphExplainer contract."""

    def forward(
        self,
        x_dict: dict[str, torch.Tensor],
        edge_index_dict: dict[tuple[str, str, str], torch.Tensor],
        query_asset_index: int = 0,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        _ = edge_index_dict

        query_asset = x_dict["Asset"][query_asset_index]
        creator_verified_signal = x_dict["Creator"][:, 0].mean()
        license_active_signal = x_dict["Licensee"][:, 0].mean()

        # Deterministic scalar logit used by SHAP black-box predictor.
        infringement_logit = (
            2.0 * creator_verified_signal
            + 1.5 * license_active_signal
            + 0.25 * query_asset[-1]
        ).view(())

        n_creators = max(1, x_dict["Creator"].shape[0])
        attribution_logits = torch.zeros(n_creators, dtype=torch.float32)
        return infringement_logit, attribution_logits, {}


def _build_test_subgraph(n_assets: int = 3) -> HeteroData:
    data = HeteroData()

    # Asset: 520 dims (512 embedding + 8 metadata), as expected by reasoning stack.
    asset_x = torch.zeros((n_assets, 520), dtype=torch.float32)
    asset_x[:, -1] = torch.tensor([1.0] + [0.6] * (n_assets - 1), dtype=torch.float32)
    data["Asset"].x = asset_x

    data["Creator"].x = torch.tensor(
        [
            [1.0, 0.7, 0.3, 0.2, 0.9, 1.0],
            [0.0, 0.4, 0.1, 0.1, 0.5, 0.0],
        ],
        dtype=torch.float32,
    )

    data["Licensee"].x = torch.tensor(
        [
            [1.0, 0.2, 0.3, 1.0],
            [0.0, 0.6, 0.1, 0.0],
        ],
        dtype=torch.float32,
    )

    # Query->neighbors similar edges including self-loop on query node 0.
    sim_targets = list(range(min(n_assets, 3)))
    data[("Asset", "similar_to", "Asset")].edge_index = torch.tensor(
        [[0] * len(sim_targets), sim_targets], dtype=torch.long
    )
    data[("Asset", "similar_to", "Asset")].edge_attr = torch.tensor(
        [[1.0], [0.8], [0.6]][: len(sim_targets)], dtype=torch.float32
    )

    # One flagged edge from query to first neighbor when available.
    flagged_dst = 1 if n_assets > 1 else 0
    data[("Asset", "flagged_with", "Asset")].edge_index = torch.tensor(
        [[0], [flagged_dst]], dtype=torch.long
    )
    data[("Asset", "flagged_with", "Asset")].edge_attr = torch.tensor([[1.5]], dtype=torch.float32)

    return data


def test_visual_explainer_generates_normalized_heatmap() -> None:
    torch.manual_seed(0)
    semantic_embedder = _TinySemanticEmbedder()
    explainer = VisualExplainer(semantic_embedder=semantic_embedder)

    image = torch.rand(3, 224, 224)
    heatmap = explainer.get_visual_explanation(image)

    assert heatmap.shape == (224, 224)
    assert heatmap.dtype == np.float32
    assert float(heatmap.min()) >= 0.0
    assert float(heatmap.max()) <= 1.0 + 1e-6


def test_visual_explainer_bounding_boxes_extract_regions() -> None:
    heatmap = np.zeros((224, 224), dtype=np.float32)
    heatmap[30:90, 40:120] = 0.95
    heatmap[130:190, 110:180] = 0.85

    boxes = VisualExplainer.heatmap_to_bounding_boxes(heatmap, top_k=3)

    assert len(boxes) >= 1
    for box in boxes:
        assert {"x", "y", "width", "height", "importance"}.issubset(box.keys())
        assert box["width"] > 0
        assert box["height"] > 0


def test_graph_explainer_shap_pipeline_returns_top_factors() -> None:
    np.random.seed(0)
    torch.manual_seed(0)

    model = _DummyRightsModel().eval()
    explainer = GraphExplainer(rights_model=model)

    subgraph = _build_test_subgraph(n_assets=3)
    factors = explainer.get_graph_explanation(subgraph)

    assert isinstance(factors, list)
    assert 1 <= len(factors) <= 5
    for item in factors:
        assert set(item.keys()) == {"factor", "shap_value"}
        assert isinstance(item["factor"], str)
        assert isinstance(item["shap_value"], float)

    # Model intentionally depends on creator_verified and license_active signals.
    factor_names = {item["factor"] for item in factors}
    assert {"creator_verified", "license_active"} & factor_names


def test_graph_explainer_feature_sampling_for_large_graphs() -> None:
    model = _DummyRightsModel().eval()
    explainer = GraphExplainer(rights_model=model, max_feature_sample=6)

    large_subgraph = _build_test_subgraph(n_assets=80)
    selected = explainer._selected_features(large_subgraph)

    assert len(selected) == 6
    assert selected == GraphExplainer._FEATURES_FULL[:6]
