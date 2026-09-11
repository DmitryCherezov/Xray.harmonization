from collections.abc import Callable, Sequence
from typing import Any

import torch.nn as nn
from torch import Tensor
from torch.hub import load_state_dict_from_url

from .evidence import AggregationType, EvidenceAggregator, EvidenceToLogit


__all__ = [
    "PEANResNet",
    "pean_resnet18",
    "pean_resnet34",
    "pean_resnet50",
    "pean_resnet101",
    "pean_resnet152",
    "pean_resnext50_32x4d",
    "pean_resnext101_32x8d",
    "pean_wide_resnet50_2",
    "pean_wide_resnet101_2",
]


MODEL_URLS = {
    "resnet18": "https://download.pytorch.org/models/resnet18-f37072fd.pth",
    "resnet34": "https://download.pytorch.org/models/resnet34-b627a593.pth",
    "resnet50": "https://download.pytorch.org/models/resnet50-0676ba61.pth",
    "resnet101": "https://download.pytorch.org/models/resnet101-63fe2227.pth",
    "resnet152": "https://download.pytorch.org/models/resnet152-394f9c45.pth",
    "resnext50_32x4d": "https://download.pytorch.org/models/resnext50_32x4d-7cdf4587.pth",
    "resnext101_32x8d": "https://download.pytorch.org/models/resnext101_32x8d-8ba56ff5.pth",
    "wide_resnet50_2": "https://download.pytorch.org/models/wide_resnet50_2-95faca4d.pth",
    "wide_resnet101_2": "https://download.pytorch.org/models/wide_resnet101_2-32ee1156.pth",
}


def conv3x3(
    in_planes: int,
    out_planes: int,
    stride: int = 1,
    groups: int = 1,
    dilation: int = 1,
) -> nn.Conv2d:
    return nn.Conv2d(
        in_planes,
        out_planes,
        kernel_size=3,
        stride=stride,
        padding=dilation,
        groups=groups,
        bias=False,
        dilation=dilation,
    )


def conv1x1(
    in_planes: int,
    out_planes: int,
    stride: int = 1,
) -> nn.Conv2d:
    return nn.Conv2d(
        in_planes,
        out_planes,
        kernel_size=1,
        stride=stride,
        bias=False,
    )


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(
        self,
        inplanes: int,
        planes: int,
        stride: int = 1,
        downsample: nn.Module | None = None,
        groups: int = 1,
        base_width: int = 64,
        dilation: int = 1,
        norm_layer: Callable[..., nn.Module] | None = None,
    ) -> None:
        super().__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        if groups != 1 or base_width != 64:
            raise ValueError("BasicBlock supports only groups=1 and base_width=64.")
        if dilation > 1:
            raise NotImplementedError("Dilation > 1 is not supported in BasicBlock.")

        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = norm_layer(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = norm_layer(planes)
        self.downsample = downsample

    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        return self.relu(out)


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(
        self,
        inplanes: int,
        planes: int,
        stride: int = 1,
        downsample: nn.Module | None = None,
        groups: int = 1,
        base_width: int = 64,
        dilation: int = 1,
        norm_layer: Callable[..., nn.Module] | None = None,
    ) -> None:
        super().__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d

        width = int(planes * (base_width / 64.0)) * groups

        self.conv1 = conv1x1(inplanes, width)
        self.bn1 = norm_layer(width)
        self.conv2 = conv3x3(width, width, stride, groups, dilation)
        self.bn2 = norm_layer(width)
        self.conv3 = conv1x1(width, planes * self.expansion)
        self.bn3 = norm_layer(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.relu(self.bn1(self.conv1(x)))
        out = self.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        return self.relu(out)


class PEANResNet(nn.Module):
    """
    The project's historical ResNet backbone with a PEAN evidence head.

    The backbone keeps the original custom downsampling layout:
        conv1(stride=1) -> maxpool -> layer1 -> layer2 -> maxpool
        -> layer3 -> maxpool -> layer4.

    The old classification/regression head is replaced by:
        1x1 evidence conv -> ReLU -> GAP/Top-K -> EvidenceToLogit.
    """

    def __init__(
        self,
        block: type[BasicBlock] | type[Bottleneck],
        layers: Sequence[int],
        in_channels: int = 3,
        aggregation: AggregationType = "gap",
        top_k: int = 10,
        evidence_threshold: float = 0.5,
        eps: float = 1e-6,
        zero_init_residual: bool = False,
        groups: int = 1,
        width_per_group: int = 64,
        norm_layer: Callable[..., nn.Module] | None = None,
    ) -> None:
        super().__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d

        self._norm_layer = norm_layer
        self.inplanes = 64
        self.dilation = 1
        self.groups = groups
        self.base_width = width_per_group

        self.conv1 = nn.Conv2d(
            in_channels,
            64,
            kernel_size=7,
            stride=1,
            padding=3,
            bias=False,
        )
        self.bn1 = norm_layer(64)
        self.relu = nn.ReLU(inplace=True)

        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.maxpool2 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.maxpool3 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=1)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=1)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=1)

        feature_channels = 512 * block.expansion
        self.evidence_conv = nn.Conv2d(
            feature_channels,
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

        self._initialize_weights()

        if zero_init_residual:
            for module in self.modules():
                if isinstance(module, Bottleneck):
                    nn.init.constant_(module.bn3.weight, 0)
                elif isinstance(module, BasicBlock):
                    nn.init.constant_(module.bn2.weight, 0)

    def _initialize_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(
                    module.weight,
                    mode="fan_out",
                    nonlinearity="relu",
                )
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, (nn.BatchNorm2d, nn.GroupNorm)):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)

    def _make_layer(
        self,
        block: type[BasicBlock] | type[Bottleneck],
        planes: int,
        blocks: int,
        stride: int = 1,
    ) -> nn.Sequential:
        norm_layer = self._norm_layer
        downsample = None

        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(self.inplanes, planes * block.expansion, stride),
                norm_layer(planes * block.expansion),
            )

        layers: list[nn.Module] = [
            block(
                self.inplanes,
                planes,
                stride,
                downsample,
                self.groups,
                self.base_width,
                self.dilation,
                norm_layer,
            )
        ]
        self.inplanes = planes * block.expansion

        for _ in range(1, blocks):
            layers.append(
                block(
                    self.inplanes,
                    planes,
                    groups=self.groups,
                    base_width=self.base_width,
                    dilation=self.dilation,
                    norm_layer=norm_layer,
                )
            )

        return nn.Sequential(*layers)

    def extract_features(self, x: Tensor) -> Tensor:
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.maxpool2(x)
        x = self.layer3(x)
        x = self.maxpool3(x)
        return self.layer4(x)

    def activation_map(self, x: Tensor) -> Tensor:
        return self.evidence_relu(
            self.evidence_conv(self.extract_features(x))
        )

    def evidence_score(self, x: Tensor) -> Tensor:
        return self.aggregator(self.activation_map(x))

    def forward(self, x: Tensor) -> Tensor:
        return self.evidence_to_logit(self.evidence_score(x))

    # Compatibility helpers for old analysis code.
    def get_img(self, x: Tensor) -> Tensor:
        return self.activation_map(x)

    def get_deep_features(self, x: Tensor) -> Tensor:
        return self.extract_features(x)

    def num_parameters(self, trainable_only: bool = True) -> int:
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())


def _load_pretrained_backbone(
    model: PEANResNet,
    arch: str,
    progress: bool,
) -> None:
    state_dict = load_state_dict_from_url(
        MODEL_URLS[arch],
        progress=progress,
    )

    # Torchvision's standard classifier is not part of PEANResNet.
    state_dict.pop("fc.weight", None)
    state_dict.pop("fc.bias", None)

    # Standard ImageNet ResNet uses three input channels. A different
    # PEANResNet input channel count cannot reuse conv1 weights directly.
    if model.conv1.weight.shape != state_dict["conv1.weight"].shape:
        state_dict.pop("conv1.weight")

    model.load_state_dict(state_dict, strict=False)


def _pean_resnet(
    arch: str,
    block: type[BasicBlock] | type[Bottleneck],
    layers: Sequence[int],
    pretrained: bool,
    progress: bool,
    **kwargs: Any,
) -> PEANResNet:
    model = PEANResNet(block, layers, **kwargs)
    if pretrained:
        _load_pretrained_backbone(model, arch, progress)
    return model


def pean_resnet18(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    return _pean_resnet("resnet18", BasicBlock, [2, 2, 2, 2], pretrained, progress, **kwargs)


def pean_resnet34(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    return _pean_resnet("resnet34", BasicBlock, [3, 4, 6, 3], pretrained, progress, **kwargs)


def pean_resnet50(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    return _pean_resnet("resnet50", Bottleneck, [3, 4, 6, 3], pretrained, progress, **kwargs)


def pean_resnet101(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    return _pean_resnet("resnet101", Bottleneck, [3, 4, 23, 3], pretrained, progress, **kwargs)


def pean_resnet152(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    return _pean_resnet("resnet152", Bottleneck, [3, 8, 36, 3], pretrained, progress, **kwargs)


def pean_resnext50_32x4d(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    kwargs["groups"] = 32
    kwargs["width_per_group"] = 4
    return _pean_resnet("resnext50_32x4d", Bottleneck, [3, 4, 6, 3], pretrained, progress, **kwargs)


def pean_resnext101_32x8d(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    kwargs["groups"] = 32
    kwargs["width_per_group"] = 8
    return _pean_resnet("resnext101_32x8d", Bottleneck, [3, 4, 23, 3], pretrained, progress, **kwargs)


def pean_wide_resnet50_2(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    kwargs["width_per_group"] = 128
    return _pean_resnet("wide_resnet50_2", Bottleneck, [3, 4, 6, 3], pretrained, progress, **kwargs)


def pean_wide_resnet101_2(pretrained: bool = False, progress: bool = True, **kwargs: Any) -> PEANResNet:
    kwargs["width_per_group"] = 128
    return _pean_resnet("wide_resnet101_2", Bottleneck, [3, 4, 23, 3], pretrained, progress, **kwargs)
