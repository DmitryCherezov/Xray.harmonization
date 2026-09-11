from typing import Literal

import torch
import torch.nn as nn
from torch import Tensor


AggregationType = Literal["gap", "topk"]


class EvidenceAggregator(nn.Module):
    """Aggregate a positive spatial evidence map into one score per image."""

    def __init__(
        self,
        aggregation: AggregationType = "gap",
        top_k: int = 10,
    ) -> None:
        super().__init__()

        if aggregation not in {"gap", "topk"}:
            raise ValueError(
                f"Unknown aggregation '{aggregation}'. Expected 'gap' or 'topk'."
            )
        if top_k <= 0:
            raise ValueError("'top_k' must be greater than 0.")

        self.aggregation = aggregation
        self.top_k = top_k

    def forward(self, evidence: Tensor) -> Tensor:
        if evidence.ndim != 4 or evidence.shape[1] != 1:
            raise ValueError(
                "Evidence map must have shape [batch, 1, height, width]. "
                f"Received {tuple(evidence.shape)}."
            )

        if self.aggregation == "gap":
            return evidence.mean(dim=(-2, -1))

        flattened = evidence.flatten(start_dim=1)
        k = min(self.top_k, flattened.shape[1])
        return torch.topk(flattened, k=k, dim=1).values.mean(
            dim=1,
            keepdim=True,
        )


class EvidenceToLogit(nn.Module):
    """Convert a non-negative evidence score to a binary-classification logit."""

    def __init__(
        self,
        threshold: float = 0.5,
        eps: float = 1e-6,
    ) -> None:
        super().__init__()

        if threshold <= 0.0:
            raise ValueError("'threshold' must be greater than 0.")
        if eps <= 0.0:
            raise ValueError("'eps' must be greater than 0.")

        self.threshold = threshold
        self.eps = eps

    def forward(self, evidence_score: Tensor) -> Tensor:
        return torch.log(
            (evidence_score + self.eps)
            / (self.threshold + self.eps)
        )
