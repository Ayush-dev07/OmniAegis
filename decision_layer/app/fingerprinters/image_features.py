"""Image feature extraction pipeline for content registration.

Extracts rich visual features using ResNet50 backbone and stores
normalized embeddings in Qdrant for similarity search and content matching.
"""

from __future__ import annotations

from io import BytesIO

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import transforms
from torchvision.models import ResNet50_Weights, resnet50


class ImageFeatureExtractor:
    """Extract deep visual features from images using ResNet50.

    Features:
    - 2048-dimensional backbone features → 512-dimensional learned projection
    - L2 normalization for cosine similarity in vector databases
    - Deterministic, reproducible embeddings
    - CPU-optimized inference path

    Contract:
    - Input: RGB image bytes
    - Output: Normalized 512-dimensional float32 embedding
    """

    def __init__(self, feature_dim: int = 512) -> None:
        """Initialize feature extractor.

        Args:
            feature_dim: Output embedding dimension. Default 512.
        """
        self.feature_dim = feature_dim
        self.device = torch.device("cpu")

        # ResNet50 backbone (ImageNet1K v2 weights)
        weights = ResNet50_Weights.IMAGENET1K_V2
        backbone = resnet50(weights=weights)

        # Remove classification head, keep feature extraction layers
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1]).to(self.device)
        self.feature_extractor.eval()

        # Learned projection: 2048 (ResNet50 features) → feature_dim
        self.projection = nn.Linear(2048, feature_dim, bias=False).to(self.device)
        # Orthogonal initialization for stable variance preservation
        rng_state = torch.random.get_rng_state()
        torch.manual_seed(42)
        nn.init.orthogonal_(self.projection.weight)
        torch.random.set_rng_state(rng_state)
        self.projection.eval()

        # Immutable preprocessing pipeline
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def _load_rgb_image_from_bytes(self, content: bytes) -> Image.Image:
        """Load and convert image bytes to RGB PIL Image."""
        try:
            image = Image.open(BytesIO(content)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError("Invalid or corrupt image file") from exc
        return image

    def _embed_image(self, image: Image.Image) -> np.ndarray:
        """Extract features from a PIL Image and return normalized embedding.

        Args:
            image: PIL Image in RGB mode

        Returns:
            Normalized 512-dimensional float32 embedding
        """
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # Extract 2048-dimensional features
            features = self.feature_extractor(tensor).squeeze()  # Shape: (2048,)
            # Project to feature_dim (512)
            embedding = self.projection(features)  # Shape: (512,)

        # Convert to numpy and normalize
        embedding_np = embedding.cpu().numpy().astype(np.float32)
        norm = np.linalg.norm(embedding_np) + 1e-8
        normalized_embedding = embedding_np / norm

        return normalized_embedding

    def embed_from_bytes(self, content: bytes) -> dict:
        """Extract embedding from image bytes.

        Args:
            content: Image file bytes

        Returns:
            Dict with keys:
                - embedding: (512,) normalized float32 array
                - embedding_dim: 512
        """
        try:
            image = self._load_rgb_image_from_bytes(content)
            embedding = self._embed_image(image)
            return {
                "embedding": embedding,
                "embedding_dim": int(self.feature_dim),
            }
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Image feature extraction failed: {exc}") from exc

    def embed_from_file(self, file_path: str) -> dict:
        """Extract embedding from image file.

        Args:
            file_path: Path to image file

        Returns:
            Dict with keys:
                - embedding: (512,) normalized float32 array
                - embedding_dim: 512
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return self.embed_from_bytes(content)
        except FileNotFoundError as exc:
            raise ValueError(f"Image file not found: {file_path}") from exc
        except (OSError, ValueError) as exc:
            raise ValueError(f"Failed to read image file: {exc}") from exc

    def embed_pil_image(self, image: Image.Image) -> dict:
        """Extract embedding from PIL Image.

        Args:
            image: PIL Image in RGB mode

        Returns:
            Dict with keys:
                - embedding: (512,) normalized float32 array
                - embedding_dim: 512
        """
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")
            embedding = self._embed_image(image)
            return {
                "embedding": embedding,
                "embedding_dim": int(self.feature_dim),
            }
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Image feature extraction failed: {exc}") from exc
