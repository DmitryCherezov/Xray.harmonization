import lightning as L
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score


class BinaryRegressionModule(L.LightningModule):
    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        optimizer_name: str = "Adam",
        momentum: float = 0.2,
        weight_decay: float = 0.0,
        gamma: float = 0.7,
        decision_threshold: float = 0.5,
    ) -> None:
        super().__init__()

        self.model = model

        self.learning_rate = learning_rate
        self.optimizer_name = optimizer_name
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.gamma = gamma
        self.decision_threshold = decision_threshold

        self.criterion = nn.MSELoss()

        self.validation_scores = []
        self.validation_labels = []

        self.test_scores = []
        self.test_labels = []

        self.save_hyperparameters(ignore=["model"])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    @staticmethod
    def _prepare_output(
        output: torch.Tensor,
    ) -> torch.Tensor:

        if output.ndim == 2 and output.shape[1] == 1:
            return output[:, 0]

        if output.ndim == 1:
            return output

        raise ValueError(
            "Binary model must return shape [batch] "
            "or [batch, 1]. "
            f"Received: {tuple(output.shape)}"
        )

    def training_step(
        self,
        batch,
        batch_idx: int,
    ):
        images, targets, _ = batch

        output = self(images)
        output = self._prepare_output(output)

        targets = targets.float()

        loss = self.criterion(
            output,
            targets,
        )

        self.log(
            "train_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(images),
        )

        return loss

    def on_validation_epoch_start(self) -> None:
        self.validation_scores = []
        self.validation_labels = []

    def validation_step(
        self,
        batch,
        batch_idx: int,
    ):
        images, targets, _ = batch

        output = self(images)
        output = self._prepare_output(output)

        targets = targets.float()

        loss = self.criterion(
            output,
            targets,
        )

        predictions = (
            output > self.decision_threshold
        ).long()

        target_classes = (
            targets > self.decision_threshold
        ).long()

        accuracy = (
            predictions == target_classes
        ).float().mean()

        self.validation_scores.append(
            output.detach().cpu()
        )

        self.validation_labels.append(
            targets.detach().cpu()
        )

        self.log(
            "val_loss",
            loss,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(images),
        )

        self.log(
            "val_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=len(images),
        )

    def on_validation_epoch_end(self) -> None:
        scores = torch.cat(
            self.validation_scores
        ).numpy()

        labels = torch.cat(
            self.validation_labels
        ).numpy().astype(int)

        auc = roc_auc_score(
            labels,
            scores,
        )

        self.log(
            "val_auc",
            auc,
            prog_bar=True,
        )

    def on_test_epoch_start(self) -> None:
        self.test_scores = []
        self.test_labels = []

    def test_step(
        self,
        batch,
        batch_idx: int,
    ):
        images, targets, _ = batch

        output = self(images)
        output = self._prepare_output(output)

        targets = targets.float()

        loss = self.criterion(
            output,
            targets,
        )

        predictions = (
            output > self.decision_threshold
        ).long()

        target_classes = (
            targets > self.decision_threshold
        ).long()

        accuracy = (
            predictions == target_classes
        ).float().mean()

        self.test_scores.append(
            output.detach().cpu()
        )

        self.test_labels.append(
            targets.detach().cpu()
        )

        self.log(
            "test_loss",
            loss,
            on_step=False,
            on_epoch=True,
            batch_size=len(images),
        )

        self.log(
            "test_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            batch_size=len(images),
        )

    def on_test_epoch_end(self) -> None:
        scores = torch.cat(
            self.test_scores
        ).numpy()

        labels = torch.cat(
            self.test_labels
        ).numpy().astype(int)

        auc = roc_auc_score(
            labels,
            scores,
        )

        predicted = (
            scores > self.decision_threshold
        ).astype(int)

        target = (
            labels > self.decision_threshold
        ).astype(int)

        confusion_matrix = np.zeros(
            (2, 2),
            dtype=int,
        )

        for target_value, prediction_value in zip(
            target,
            predicted,
        ):
            confusion_matrix[
                target_value,
                prediction_value,
            ] += 1

        self.log(
            "test_auc",
            auc,
        )

        print(
            "\nTest confusion matrix:"
        )

        print(confusion_matrix)

        print(
            f"Test AUC: {auc:.4f}"
        )

    def configure_optimizers(self):
        if self.optimizer_name == "Adam":
            optimizer = torch.optim.Adam(
                self.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay,
            )

        elif self.optimizer_name == "SGD":
            optimizer = torch.optim.SGD(
                self.parameters(),
                lr=self.learning_rate,
                momentum=self.momentum,
                weight_decay=self.weight_decay,
            )

        else:
            raise ValueError(
                f"Unknown optimizer: "
                f"{self.optimizer_name}"
            )

        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=1,
            gamma=self.gamma,
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": scheduler,
        }