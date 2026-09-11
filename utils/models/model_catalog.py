from collections.abc import Callable
from typing import Any

import torch.nn as nn

from . import pean
from . import pean_resnet


ModelFactory = Callable[..., nn.Module]


class ModelCatalog:
    """Registry/factory for the project's neural-network architectures."""

    def __init__(self) -> None:
        self._models: dict[str, ModelFactory] = {
            "pean_tiny": pean.pean_tiny,
            "pean_small": pean.pean_small,
            "pean_medium": pean.pean_medium,
            "pean_large": pean.pean_large,
            "pean_xlarge": pean.pean_xlarge,
            "pean_resnet18": pean_resnet.pean_resnet18,
            "pean_resnet34": pean_resnet.pean_resnet34,
            "pean_resnet50": pean_resnet.pean_resnet50,
            "pean_resnet101": pean_resnet.pean_resnet101,
            "pean_resnet152": pean_resnet.pean_resnet152,
            "pean_resnext50_32x4d": pean_resnet.pean_resnext50_32x4d,
            "pean_resnext101_32x8d": pean_resnet.pean_resnext101_32x8d,
            "pean_wide_resnet50_2": pean_resnet.pean_wide_resnet50_2,
            "pean_wide_resnet101_2": pean_resnet.pean_wide_resnet101_2,
        }

    def available_models(self) -> list[str]:
        return sorted(self._models)

    def create(self, name: str, **kwargs: Any) -> nn.Module:
        try:
            factory = self._models[name]
        except KeyError as exc:
            available = ", ".join(self.available_models())
            raise ValueError(
                f"Unknown model '{name}'. Available models: {available}"
            ) from exc

        return factory(**kwargs)
