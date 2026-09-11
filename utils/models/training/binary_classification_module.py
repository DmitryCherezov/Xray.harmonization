import lightning as L
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score


class BinaryClassificationModule(L.LightningModule):
    """Lightning module for one-logit binary classification."""

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        optimizer_name: str = "Adam",
        momentum: float = 0.2,
        weight_decay: float = 0.0,
        gamma: float = 0.7,
        decision_threshold: float = 0.5,
        pos_weight: float | None = None,
    ) -> None:
        super().__init__()

        if not 0.0 < decision_threshold < 1.0:
            raise ValueError("'decision_threshold' must be between 0 and 1.")

        self.model = model
        self.learning_rate = learning_rate
        self.optimizer_name = optimizer_name
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.gamma = gamma
        self.decision_threshold = decision_threshold

        if pos_weight is None:
            self.criterion = nn.BCEWithLogitsLoss()
        else:
            self.criterion = nn.BCEWithLogitsLoss(
                pos_weight=torch.tensor([pos_weight], dtype=torch.float32)
            )

        self.validation_probabilities: list[torch.Tensor] = []
        self.validation_labels: list[torch.Tensor] = []
        self.test_probabilities: list[torch.Tensor] = []
        self.test_labels: list[torch.Tensor] = []

        self.save_hyperparameters(ignore=["model"])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    @staticmethod
    def _flatten_binary_output(output: torch.Tensor) -> torch.Tensor:
        if output.ndim == 2 and output.shape[1] == 1:
            return output[:, 0]
        if output.ndim == 1:
            return output
        raise ValueError(
            "Binary model must return [batch] or [batch, 1]. "
            f"Received {tuple(output.shape)}."
        )

    def _shared_step(
        self,
        batch,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        images, targets, _ = batch
        logits = self._flatten_binary_output(self(images))
        targets = targets.float().reshape(-1)

        loss = self.criterion(logits, targets)
        probabilities = torch.sigmoid(logits)
        predictions = (probabilities >= self.decision_threshold).long()
        accuracy = (predictions == targets.long()).float().mean()

        return loss, probabilities, targets, accuracy

    def training_step(self, batch, batch_idx: int) -> torch.Tensor:
        loss, _, _, accuracy = self._shared_step(batch)

        self.log(
            "train_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(batch[0]),
        )
        self.log(
            "train_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
            batch_size=len(batch[0]),
        )
        return loss

    def on_validation_epoch_start(self) -> None:
        self.validation_probabilities.clear()
        self.validation_labels.clear()

    def validation_step(self, batch, batch_idx: int) -> None:
        loss, probabilities, targets, accuracy = self._shared_step(batch)

        self.validation_probabilities.append(probabilities.detach().cpu())
        self.validation_labels.append(targets.detach().cpu())

        self.log(
            "val_loss",
            loss,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(batch[0]),
        )
        self.log(
            "val_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(batch[0]),
        )

    def on_validation_epoch_end(self) -> None:
        auc = self._epoch_auc(
            self.validation_labels,
            self.validation_probabilities,
        )
        if auc is not None:
            self.log("val_auc", auc, prog_bar=True)

    def on_test_epoch_start(self) -> None:
        self.test_probabilities.clear()
        self.test_labels.clear()

    def test_step(self, batch, batch_idx: int) -> None:
        loss, probabilities, targets, accuracy = self._shared_step(batch)

        self.test_probabilities.append(probabilities.detach().cpu())
        self.test_labels.append(targets.detach().cpu())

        self.log(
            "test_loss",
            loss,
            on_step=False,
            on_epoch=True,
            batch_size=len(batch[0]),
        )
        self.log(
            "test_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            batch_size=len(batch[0]),
        )

    def on_test_epoch_end(self) -> None:
        if not self.test_probabilities or not self.test_labels:
            return

        probabilities = torch.cat(
            self.test_probabilities
        ).numpy()

        labels = torch.cat(
            self.test_labels
        ).numpy().astype(int)

        predictions = (
            probabilities >= self.decision_threshold
        ).astype(int)

        confusion_matrix = np.zeros(
            (2, 2),
            dtype=int,
        )

        for target_value, prediction_value in zip(
            labels,
            predictions,
        ):
            confusion_matrix[
                target_value,
                prediction_value,
            ] += 1

        tn, fp, fn, tp = confusion_matrix.ravel()

        # Keep it available after trainer.test(...)
        self.test_confusion_matrix = confusion_matrix

        auc = self._safe_auc(
            labels,
            probabilities,
        )

        if auc is not None:
            self.log(
                "test_auc",
                auc,
            )

        self.log(
            "test_tn",
            float(tn),
        )

        self.log(
            "test_fp",
            float(fp),
        )

        self.log(
            "test_fn",
            float(fn),
        )

        self.log(
            "test_tp",
            float(tp),
        )

    @classmethod
    def _epoch_auc(
        cls,
        labels: list[torch.Tensor],
        probabilities: list[torch.Tensor],
    ) -> float | None:
        if not labels or not probabilities:
            return None
        y = torch.cat(labels).numpy().astype(int)
        p = torch.cat(probabilities).numpy()
        return cls._safe_auc(y, p)

    @staticmethod
    def _safe_auc(labels: np.ndarray, probabilities: np.ndarray) -> float | None:
        if np.unique(labels).size < 2:
            return None
        return float(roc_auc_score(labels, probabilities))

    def configure_optimizers(self):
        optimizer_name = self.optimizer_name.lower()

        if optimizer_name == "adam":
            optimizer = torch.optim.Adam(
                self.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay,
            )
        elif optimizer_name == "sgd":
            optimizer = torch.optim.SGD(
                self.parameters(),
                lr=self.learning_rate,
                momentum=self.momentum,
                weight_decay=self.weight_decay,
            )
        else:
            raise ValueError(f"Unknown optimizer: {self.optimizer_name}")

        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=1,
            gamma=self.gamma,
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": scheduler,
        }
