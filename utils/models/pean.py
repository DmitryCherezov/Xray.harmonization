from collections.abc import Sequence

import torch.nn as nn
from torch import Tensor

from .evidence import AggregationType, EvidenceAggregator, EvidenceToLogit


class ConvBlock(nn.Module):
    """Conv2d -> BatchNorm2d -> ReLU."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
    ) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                stride=stride,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.block(x)


class PEAN(nn.Module):
    """
    PEAN evidence-based binary-classification network.

    Input -> convolutional backbone -> 1-channel evidence map -> ReLU
          -> GAP/Top-K aggregation -> EvidenceToLogit -> binary logit.

    The returned tensor has shape [batch, 1] and is intended for
    BCEWithLogitsLoss. Sigmoid is deliberately not applied in forward().
    """

    def __init__(
        self,
        channels: Sequence[int],
        blocks_per_stage: Sequence[int],
        in_channels: int = 3,
        aggregation: AggregationType = "gap",
        top_k: int = 10,
        evidence_threshold: float = 0.5,
        eps: float = 1e-6,
    ) -> None:
        super().__init__()

        if len(channels) != len(blocks_per_stage):
            raise ValueError(
                "'channels' and 'blocks_per_stage' must have the same length."
            )
        if not channels:
            raise ValueError("'channels' cannot be empty.")
        if in_channels <= 0:
            raise ValueError("'in_channels' must be greater than 0.")

        self.backbone = self._make_backbone(
            in_channels,
            channels,
            blocks_per_stage,
        )
        self.evidence_conv = nn.Conv2d(
            channels[-1],
            1,
            kernel_size=1,
            bias=True,
        )
        self.evidence_relu = nn.ReLU(inplace=False)
        self.aggregator = EvidenceAggregator(
            aggregation=aggregation,
            top_k=top_k,
        )
        self.evidence_to_logit = EvidenceToLogit(
            threshold=evidence_threshold,
            eps=eps,
        )

    @staticmethod
    def _make_backbone(
        in_channels: int,
        channels: Sequence[int],
        blocks_per_stage: Sequence[int],
    ) -> nn.Sequential:
        layers: list[nn.Module] = []
        current_channels = in_channels

        for stage_channels, number_of_blocks in zip(
            channels,
            blocks_per_stage,
            strict=True,
        ):
            if number_of_blocks <= 0:
                raise ValueError("Each stage must contain at least one block.")

            layers.append(
                ConvBlock(
                    current_channels,
                    stage_channels,
                    stride=2,
                )
            )
            current_channels = stage_channels

            for _ in range(number_of_blocks - 1):
                layers.append(
                    ConvBlock(
                        current_channels,
                        stage_channels,
                        stride=1,
                    )
                )

        return nn.Sequential(*layers)

    def extract_features(self, x: Tensor) -> Tensor:
        return self.backbone(x)

    def activation_map(self, x: Tensor) -> Tensor:
        return self.evidence_relu(
            self.evidence_conv(self.extract_features(x))
        )

    def evidence_score(self, x: Tensor) -> Tensor:
        return self.aggregator(self.activation_map(x))

    def forward(self, x: Tensor) -> Tensor:
        return self.evidence_to_logit(self.evidence_score(x))

    def num_parameters(self, trainable_only: bool = True) -> int:
        parameters = self.parameters()
        if trainable_only:
            return sum(p.numel() for p in parameters if p.requires_grad)
        return sum(p.numel() for p in parameters)


# Presets are calibrated for the default in_channels=3.
# Their trainable parameter counts are exactly the stated targets.
def pean_tiny(**kwargs) -> PEAN:
    """PEAN Tiny: 50,000 trainable parameters with in_channels=3."""
    return PEAN(
        channels=(11, 24, 42, 100),
        blocks_per_stage=(1, 1, 1, 1),
        **kwargs,
    )


def pean_small(**kwargs) -> PEAN:
    """PEAN Small: 98,000 trainable parameters with in_channels=3."""
    return PEAN(
        channels=(15, 31, 61, 138),
        blocks_per_stage=(1, 1, 1, 1),
        **kwargs,
    )


def pean_medium(**kwargs) -> PEAN:
    """PEAN Medium: 200,000 trainable parameters with in_channels=3."""
    return PEAN(
        channels=(24, 38, 78, 155),
        blocks_per_stage=(1, 1, 2, 1),
        **kwargs,
    )


def pean_large(**kwargs) -> PEAN:
    """PEAN Large: 500,000 trainable parameters with in_channels=3."""
    return PEAN(
        channels=(20, 47, 97, 180),
        blocks_per_stage=(1, 1, 1, 2),
        **kwargs,
    )


def pean_xlarge(**kwargs) -> PEAN:
    """PEAN XLarge: 1,000,000 trainable parameters with in_channels=3."""
    return PEAN(
        channels=(27, 63, 149, 250),
        blocks_per_stage=(1, 1, 1, 2),
        **kwargs,
    )
