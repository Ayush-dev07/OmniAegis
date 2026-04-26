"""Adversarial robustness CI/CD gate test suite.

Validates model resilience against adversarial attacks:
- Stage 1: Clean accuracy > FGSM accuracy (sanity check)
- Stage 2: PGD adversarial accuracy > 60% (robustness threshold)
- Stage 3: Whitelist flip rate < 15% (graph attack defense)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import torch.nn as nn


# Add decision_layer to path
DECISION_LAYER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(DECISION_LAYER_PATH))

from app.adversarial_attacks import FGSM, PGD
from app.graph_attack_simulator import GraphAttackSimulator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_classifier() -> nn.Module:
    """Create a simple CNN classifier for testing.

    Returns a 2-class classifier that processes 3x32x32 images.
    """

    class SimpleCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
            self.fc1 = nn.Linear(32 * 8 * 8, 64)
            self.fc2 = nn.Linear(64, 2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = torch.relu(self.conv1(x))
            x = torch.max_pool2d(x, 2)
            x = torch.relu(self.conv2(x))
            x = torch.max_pool2d(x, 2)
            x = x.view(x.size(0), -1)
            x = torch.relu(self.fc1(x))
            x = self.fc2(x)
            return x

    model = SimpleCNN()
    model.eval()
    return model


@pytest.fixture
def test_data() -> tuple[torch.Tensor, torch.Tensor]:
    """Generate synthetic test data.

    Returns:
        Tuple of (images, labels) with 100 samples, 50 per class.
    """
    torch.manual_seed(42)
    x = torch.randn(100, 3, 32, 32) * 0.5 + 0.5  # Normalized to ~[0, 1]
    x = torch.clamp(x, 0, 1)
    y = torch.cat([torch.zeros(50, dtype=torch.long), torch.ones(50, dtype=torch.long)])
    return x, y


@pytest.fixture
def loss_fn() -> nn.Module:
    """Cross-entropy loss for classification."""
    return nn.CrossEntropyLoss()


@pytest.fixture
def mock_graph_db() -> dict[str, Any]:
    """Mock Neo4j graph database."""
    return {
        "nodes": {
            "whitelist_1": {"type": "whitelist"},
            "whitelist_2": {"type": "whitelist"},
            "asset_1": {"type": "asset", "status": "infringing"},
        },
        "relationships": {
            "asset_1->INFERRED_FROM->evidence_1": {"confidence": 0.85},
        },
    }


# ============================================================================
# Stage 1: Clean vs. FGSM Accuracy
# ============================================================================


class TestStage1CleanVsFGSM:
    """Stage 1: Validate clean accuracy exceeds FGSM adversarial accuracy."""

    def test_clean_accuracy_baseline(
        self, simple_classifier: nn.Module, test_data: tuple[torch.Tensor, torch.Tensor]
    ) -> None:
        """Test that model achieves meaningful accuracy on clean data."""
        x, y = test_data
        with torch.no_grad():
            output = simple_classifier(x)
            pred = output.argmax(dim=1)
            accuracy = (pred == y).float().mean().item()

        assert accuracy > 0.3, f"Clean accuracy ({accuracy:.2%}) too low"

    def test_fgsm_attack_reduces_accuracy(
        self,
        simple_classifier: nn.Module,
        test_data: tuple[torch.Tensor, torch.Tensor],
        loss_fn: nn.Module,
    ) -> None:
        """Test that FGSM attack reduces model accuracy."""
        x, y = test_data

        # Evaluate clean accuracy
        with torch.no_grad():
            output_clean = simple_classifier(x)
            pred_clean = output_clean.argmax(dim=1)
            clean_accuracy = (pred_clean == y).float().mean().item()

        # Generate FGSM adversarial examples
        fgsm = FGSM(epsilon=0.03)
        x_adv = fgsm(simple_classifier, x, y, loss_fn)

        # Evaluate adversarial accuracy
        with torch.no_grad():
            output_adv = simple_classifier(x_adv)
            pred_adv = output_adv.argmax(dim=1)
            adv_accuracy = (pred_adv == y).float().mean().item()

        # FGSM should reduce accuracy
        assert (
            clean_accuracy > adv_accuracy
        ), f"FGSM failed: clean={clean_accuracy:.2%}, adv={adv_accuracy:.2%}"

        # Store metrics for reporting
        pytest.stage1_metrics = {
            "clean_accuracy": clean_accuracy,
            "fgsm_accuracy": adv_accuracy,
            "accuracy_drop": clean_accuracy - adv_accuracy,
        }


# ============================================================================
# Stage 2: PGD Adversarial Accuracy Threshold
# ============================================================================


class TestStage2PGDRobustness:
    """Stage 2: Validate PGD adversarial accuracy > 60% (robustness gate)."""

    def test_pgd_attack_and_robustness(
        self,
        simple_classifier: nn.Module,
        test_data: tuple[torch.Tensor, torch.Tensor],
        loss_fn: nn.Module,
    ) -> None:
        """Test PGD-20 attack with 5 restarts and measure adversarial accuracy.

        This gate ensures the model maintains reasonable accuracy under
        strong adversarial perturbations (epsilon=0.03, 20 steps, 5 restarts).
        """
        x, y = test_data

        pgd = PGD(epsilon=0.03, alpha=0.003, num_steps=20, num_restarts=5)

        # Generate PGD adversarial examples (process in batch to avoid OOM)
        x_adv_all = []
        for i in range(0, len(x), 16):
            x_batch = x[i : i + 16]
            y_batch = y[i : i + 16]
            x_adv_batch = pgd(simple_classifier, x_batch, y_batch, loss_fn)
            x_adv_all.append(x_adv_batch)

        x_adv = torch.cat(x_adv_all, dim=0)

        # Evaluate adversarial accuracy
        with torch.no_grad():
            output_adv = simple_classifier(x_adv)
            pred_adv = output_adv.argmax(dim=1)
            pgd_accuracy = (pred_adv == y).float().mean().item()

        # GATE: PGD accuracy must exceed 60%
        pytest.stage2_metrics = {
            "pgd_accuracy": pgd_accuracy,
            "pgd_threshold": 0.60,
            "passed": pgd_accuracy > 0.60,
        }

        assert pgd_accuracy > 0.60, f"PGD robustness gate FAILED: {pgd_accuracy:.2%} <= 60%"


# ============================================================================
# Stage 3: Whitelist Flip Rate (Graph Attacks)
# ============================================================================


class TestStage3WhitelistFlipRate:
    """Stage 3: Validate whitelist flip rate < 15% under graph attacks."""

    def test_fake_licensing_attack_defense(self, mock_graph_db: dict[str, Any]) -> None:
        """Test defense against Fake Licensing graph attack.

        An asset should maintain enforcement (confidence < 0.65) even when
        attacked with false LICENSED_TO edges.
        """
        simulator = GraphAttackSimulator(mock_graph_db)

        # Simulate attack on high-confidence infringing asset
        result = simulator.simulate_fake_licensing_attack(
            asset_id="asset_1",
            target_whitelist_nodes=["whitelist_1", "whitelist_2"],
            confidence_before=0.85,
        )

        # Check defense effectiveness
        defense_check = simulator.check_defense_resistance(result)

        assert not defense_check["defense_resistant"], (
            f"Fake licensing attack succeeded (should be defended): "
            f"post_attack_confidence={result.confidence_after:.3f}"
        )

    def test_cooccurrence_flooding_attack_defense(
        self, mock_graph_db: dict[str, Any]
    ) -> None:
        """Test defense against Co-occurrence Flooding graph attack.

        Whitelist assets should be protected from false co-occurrence edges
        (confidence should remain < enforcement threshold).
        """
        simulator = GraphAttackSimulator(mock_graph_db)

        # Simulate attack with 100 fake similar assets
        result = simulator.simulate_cooccurrence_flooding_attack(
            asset_id="asset_1", num_fake_similar_assets=100, confidence_before=0.85
        )

        defense_check = simulator.check_defense_resistance(result)

        assert not defense_check["defense_resistant"], (
            f"Co-occurrence flooding attack succeeded: "
            f"post_attack_confidence={result.confidence_after:.3f}"
        )

    def test_whitelist_flip_rate_under_attacks(
        self, mock_graph_db: dict[str, Any]
    ) -> None:
        """Test whitelist flip rate (infringing becoming whitelist) < 15%.

        Whitelist flip = % of assets that change from infringing to whitelist
        after graph attacks. This should be < 15% to pass the gate.
        """
        simulator = GraphAttackSimulator(mock_graph_db)

        # Simulate multiple attacks
        num_tests = 20
        flips = 0

        for i in range(num_tests):
            # Alternate between attack types
            if i % 2 == 0:
                result = simulator.simulate_fake_licensing_attack(
                    asset_id=f"asset_{i}",
                    target_whitelist_nodes=["whitelist_1", "whitelist_2"],
                    confidence_before=0.80,
                )
            else:
                result = simulator.simulate_cooccurrence_flooding_attack(
                    asset_id=f"asset_{i}",
                    num_fake_similar_assets=50,
                    confidence_before=0.80,
                )

            # Flip occurs if confidence drops below 0.65 (enforcement threshold)
            if result.success:
                flips += 1

        flip_rate = flips / num_tests if num_tests > 0 else 0.0

        # GATE: Whitelist flip rate must be < 15%
        pytest.stage3_metrics = {
            "whitelist_flip_rate": flip_rate,
            "flip_threshold": 0.15,
            "flips": flips,
            "total_tests": num_tests,
            "passed": flip_rate < 0.15,
        }

        assert flip_rate < 0.15, (
            f"Whitelist flip rate gate FAILED: {flip_rate:.2%} >= 15% "
            f"({flips}/{num_tests} flips)"
        )


# ============================================================================
# Test Execution & Reporting
# ============================================================================


def pytest_configure(config):
    """Initialize metrics storage."""
    pytest.stage1_metrics = {}
    pytest.stage2_metrics = {}
    pytest.stage3_metrics = {}


def pytest_sessionfinish(session, exitstatus):
    """Report results at session end."""
    if exitstatus != 0:
        # Generate JSON failure report
        report = {
            "status": "FAILED",
            "exit_code": exitstatus,
            "stage_results": {
                "stage_1_clean_vs_fgsm": getattr(pytest, "stage1_metrics", {}),
                "stage_2_pgd_robustness": getattr(pytest, "stage2_metrics", {}),
                "stage_3_whitelist_flip": getattr(pytest, "stage3_metrics", {}),
            },
            "failed_gates": [
                "stage_2_pgd_robustness"
                if not getattr(pytest.stage2_metrics, "passed", True)
                else None,
                "stage_3_whitelist_flip"
                if not getattr(pytest.stage3_metrics, "passed", True)
                else None,
            ],
        }
        report["failed_gates"] = [g for g in report["failed_gates"] if g]

        # Write JSON report
        report_file = Path(__file__).parent / "adv_ci_gate_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n❌ Adversarial CI Gate FAILED\nReport: {report_file}")


__all__ = [
    "TestStage1CleanVsFGSM",
    "TestStage2PGDRobustness",
    "TestStage3WhitelistFlipRate",
]
