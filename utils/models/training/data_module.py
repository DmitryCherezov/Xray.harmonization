from pathlib import Path

import lightning as L
from torch.utils.data import DataLoader

from .csv_dataset import CsvImageDataset


class ImageClassificationDataModule(L.LightningDataModule):
    def __init__(
        self,
        training_csv: str | Path,
        validation_csv: str | Path,
        test_csv: str | Path,
        data_root: str | Path,
        batch_size: int = 64,
        test_batch_size: int = 64,
        num_workers: int = 8,
        channels: int = 3,
        balance_training: bool = True,
        train_transform=None,
        evaluation_transform=None,
    ) -> None:
        super().__init__()

        self.training_csv = training_csv
        self.validation_csv = validation_csv
        self.test_csv = test_csv
        self.data_root = data_root

        self.batch_size = batch_size
        self.test_batch_size = test_batch_size
        self.num_workers = num_workers
        self.channels = channels
        self.balance_training = balance_training
        self.train_transform = train_transform
        self.evaluation_transform = evaluation_transform

    def setup(self, stage: str | None = None) -> None:
        self.training_dataset = CsvImageDataset(
            csv_path=self.training_csv,
            data_root=self.data_root,
            channels=self.channels,
            balance_classes=self.balance_training,
            transform=self.train_transform,
        )

        self.validation_dataset = CsvImageDataset(
            csv_path=self.validation_csv,
            data_root=self.data_root,
            channels=self.channels,
            balance_classes=False,
            transform=self.evaluation_transform,
        )

        self.test_dataset = CsvImageDataset(
            csv_path=self.test_csv,
            data_root=self.data_root,
            channels=self.channels,
            balance_classes=False,
            transform=self.evaluation_transform,
        )

    def train_dataloader(self) -> DataLoader:
        return DataLoader(
            self.training_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=True,
        )

    def val_dataloader(self) -> DataLoader:
        return DataLoader(
            self.validation_dataset,
            batch_size=self.test_batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=True,
        )

    def test_dataloader(self) -> DataLoader:
        return DataLoader(
            self.test_dataset,
            batch_size=self.test_batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=True,
        )
