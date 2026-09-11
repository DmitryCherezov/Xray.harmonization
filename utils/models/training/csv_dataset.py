from pathlib import Path
import random

import pandas as pd
import torch

from PIL import Image, ImageOps
from torch.utils.data import Dataset
from torchvision.transforms import Compose, ToTensor


class CsvImageDataset(Dataset):
    def __init__(
        self,
        csv_path: str | Path,
        data_root: str | Path,
        image_column: str = "filename",
        label_column: str = "label",
        transform=None,
        target_transform=None,
        channels: int = 3,
        balance_classes: bool = False,
        label_scale: float = 1.0,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.data_root = Path(data_root)

        self.data = pd.read_csv(self.csv_path)

        self.image_column = image_column
        self.label_column = label_column

        self.channels = channels
        self.balance_classes = balance_classes
        self.label_scale = label_scale

        self.transform = transform or Compose([
            ToTensor(),
        ])

        self.target_transform = target_transform

        self.pos_list: list[Path] = []
        self.neg_list: list[Path] = []

        if self.balance_classes:
            self._prepare_balanced_lists()

    def _resolve_path(
        self,
        image_path: str | Path,
    ) -> Path:
        path = Path(image_path)

        if not path.is_absolute():
            path = self.data_root / path

        return path

    def _prepare_balanced_lists(self) -> None:
        for _, row in self.data.iterrows():
            image_path = self._resolve_path(
                row[self.image_column]
            )

            label = int(
                row[self.label_column]
            )

            if label == 1:
                self.pos_list.append(image_path)
            else:
                self.neg_list.append(image_path)

        if not self.pos_list:
            raise ValueError(
                "No positive samples found."
            )

        if not self.neg_list:
            raise ValueError(
                "No negative samples found."
            )

    def __len__(self) -> int:
        if self.balance_classes:
            return max(
                len(self.pos_list),
                len(self.neg_list),
            ) * 2

        return len(self.data)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[
        torch.Tensor,
        torch.Tensor,
        str,
    ]:
        if self.balance_classes:
            image_path, label = (
                self._get_balanced_sample(index)
            )

        else:
            row = self.data.iloc[index]

            image_path = self._resolve_path(
                row[self.image_column]
            )

            label = float(
                row[self.label_column]
            )

        image = Image.open(image_path)

        if self.channels == 3:
            image = image.convert("RGB")

        elif self.channels == 1:
            image = ImageOps.grayscale(image)

        else:
            raise ValueError(
                "channels must be either 1 or 3."
            )

        if self.transform is not None:
            image = self.transform(image)

        target = torch.tensor(
            label * self.label_scale,
            dtype=torch.float32,
        )

        if self.target_transform is not None:
            target = self.target_transform(target)

        return (
            image,
            target,
            str(image_path),
        )

    def _get_balanced_sample(
        self,
        index: int,
    ) -> tuple[Path, float]:
        if index % 2 == 0:
            image_path = random.choice(
                self.pos_list
            )

            label = 1.0

        else:
            image_path = random.choice(
                self.neg_list
            )

            label = 0.0

        return image_path, label

    def get_image_path(
        self,
        index: int,
    ) -> tuple[Path, float]:
        row = self.data.iloc[index]

        image_path = self._resolve_path(
            row[self.image_column]
        )

        label = float(
            row[self.label_column]
        )

        return image_path, label


