import lightning as L
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint

from config.settings_data import DataSetsSettings
from utils.data_repository_utils import load_dataset_catalog
from utils.models.model_catalog import ModelCatalog
from utils.models.training.binary_classification_module import (
    BinaryClassificationModule,
)
from utils.models.training.data_module import ImageClassificationDataModule


PROFILE = "default"


def main() -> None:
    settings = DataSetsSettings.build(PROFILE)

    L.seed_everything(
        1,
        workers=True,
    )

    # Dataset ---------------------------------------------------------
    dataset_catalog = load_dataset_catalog(
        settings.ap_detection_config
    )

    dataset = dataset_catalog.get(
        dataset_name="d110_s120_PA_acquisition_parameters_detection",
        task="ap-detection",
        version="v1.0.0",
    )

    data_module = ImageClassificationDataModule(
        training_csv=dataset.training.csv_path,
        validation_csv=dataset.validation.csv_path,
        test_csv=dataset.test.csv_path,
        data_root=dataset.data_root,
        batch_size=64,
        test_batch_size=64,
        num_workers=8,
        channels=3,
        balance_training=True,
    )

    # Model -----------------------------------------------------------
    model_catalog = ModelCatalog()

    network = model_catalog.create(
        "pean_resnet18",
        in_channels=3,
        aggregation="gap",
        evidence_threshold=0.5,
    )

    # Lightning module -----------------------------------------------
    module = BinaryClassificationModule(
        model=network,
        learning_rate=1e-3,
        optimizer_name="Adam",
        gamma=0.7,
        decision_threshold=0.5,
    )

    # Training callbacks ---------------------------------------------
    checkpoint = ModelCheckpoint(
        dirpath="checkpoints",
        filename="best-{epoch:03d}-{val_loss:.4f}",
        monitor="val_loss",
        mode="min",
        save_top_k=1,
        save_last=True,
    )

    early_stopping = EarlyStopping(
        monitor="val_loss",
        mode="min",
        patience=5,
    )

    trainer = L.Trainer(
        max_epochs=14,
        accelerator="auto",
        devices="auto",
        callbacks=[checkpoint, early_stopping],
        log_every_n_steps=10,
    )

    trainer.fit(
        module,
        datamodule=data_module,
    )

    trainer.test(
        module,
        datamodule=data_module,
        ckpt_path="best",
    )


if __name__ == "__main__":
    main()
