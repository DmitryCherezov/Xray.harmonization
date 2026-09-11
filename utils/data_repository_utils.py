from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from utils.templates_split import SplitNames


PathLike = str | Path
PathsLike = PathLike | Iterable[PathLike]
DatasetKey = tuple[str, str, str]


class DatasetRepositoryError(Exception):
    """
    Base exception for dataset repository operations.
    """


class DatasetCertificateError(DatasetRepositoryError):
    """
    Raised when certificate.yaml is missing required information
    or contains invalid values.
    """


class DatasetPathError(DatasetRepositoryError):
    """
    Raised when a path declared in certificate.yaml is invalid
    or does not exist.
    """


class DuplicateDatasetError(DatasetRepositoryError):
    """
    Raised when the catalog already contains the same dataset,
    task, and version.
    """


class DatasetNotFoundError(DatasetRepositoryError):
    """
    Raised when a requested dataset is not present in the catalog.
    """


@dataclass(frozen=True)
class DatasetSplit:
    """
    Description of one dataset split.

    Parameters
    ----------
    name
        Split name: training, validation, or test.
    csv_path
        Absolute path to the CSV manifest.
    data_directory
        Absolute path to the split data directory.
    patients
        Patient counts reported in certificate.yaml.
    images
        Successfully saved image counts reported in certificate.yaml.
    failed_images
        Failed image counts reported in certificate.yaml.
    """

    name: SplitNames
    csv_path: Path
    data_directory: Path
    patients: Mapping[str, int]
    images: Mapping[str, int]
    failed_images: Mapping[str, int]


@dataclass(frozen=True)
class DatasetVersion:
    """
    Loaded description of one dataset task version.

    This object contains resolved absolute paths. Code using this object
    does not need to know whether config and data directories are stored
    together or separately.
    """

    dataset_name: str
    task: str
    version: str
    schema_version: str

    dataset_root: Path
    task_root: Path
    version_root: Path

    certificate_path: Path
    config_root: Path
    csv_root: Path
    data_root: Path

    splits: Mapping[SplitNames, DatasetSplit]
    certificate: Mapping[str, Any]

    @property
    def key(self) -> DatasetKey:
        """
        Return the unique catalog key.
        """
        return (
            self.dataset_name,
            self.task,
            self.version,
        )

    @property
    def training(self) -> DatasetSplit:
        """
        Return the training split.
        """
        return self.get_split(SplitNames.TRAINING)

    @property
    def validation(self) -> DatasetSplit:
        """
        Return the validation split.
        """
        return self.get_split(SplitNames.VALIDATION)

    @property
    def test(self) -> DatasetSplit:
        """
        Return the test split.
        """
        return self.get_split(SplitNames.TEST)

    def get_split(
        self,
        split_name: SplitNames | str,
    ) -> DatasetSplit:
        """
        Return one split by enum member or string value.
        """
        try:
            split_name = SplitNames(split_name)
        except ValueError as exc:
            allowed = ", ".join(
                split.value
                for split in SplitNames
            )

            raise ValueError(
                f"Unknown split name: {split_name!r}. "
                f"Allowed values are: {allowed}."
            ) from exc

        try:
            return self.splits[split_name]
        except KeyError as exc:
            raise DatasetCertificateError(
                f"Split {split_name.value!r} is not available "
                f"for dataset {self.key}."
            ) from exc

    def resolve_image_path(
        self,
        filename: str | Path,
        *,
        require_exists: bool = False,
    ) -> Path:
        """
        Resolve a filename from a CSV manifest against data_root.

        CSV filenames are expected to be relative to data_root.

        Parameters
        ----------
        filename
            Relative filename stored in a CSV manifest.
        require_exists
            If True, raise FileNotFoundError when the image does not exist.
        """
        filename = Path(filename)

        if filename.is_absolute() or filename.drive:
            raise DatasetPathError(
                "CSV image filename must be relative to data_root. "
                f"Received: {filename}"
            )

        data_root = self.data_root.resolve()
        image_path = (data_root / filename).resolve()

        try:
            image_path.relative_to(data_root)
        except ValueError as exc:
            raise DatasetPathError(
                f"Image path escapes data_root: {filename}"
            ) from exc

        if require_exists and not image_path.is_file():
            raise FileNotFoundError(
                f"Dataset image was not found: {image_path}"
            )

        return image_path


@dataclass(frozen=True)
class DatasetLoadFailure:
    """
    Information about a certificate that could not be loaded.
    """

    certificate_path: Path
    exception_type: str
    message: str


class DatasetScanner:
    """
    Find dataset certificate files under one or more paths.

    Accepted input paths may point to:

    - a dataset root;
    - a task root;
    - a version root;
    - a config directory;
    - certificate.yaml itself.
    """

    certificate_filename = "certificate.yaml"
    config_directory_name = "config"

    def scan(
        self,
        paths: PathsLike,
    ) -> tuple[Path, ...]:
        """
        Find all certificate.yaml files under the supplied paths.

        Returns
        -------
        tuple[Path, ...]
            Unique absolute certificate paths sorted alphabetically.
        """
        search_paths = self._normalize_paths(paths)
        certificates: set[Path] = set()

        for search_path in search_paths:
            search_path = search_path.expanduser()

            if not search_path.exists():
                raise FileNotFoundError(
                    f"Dataset search path was not found: {search_path}"
                )

            if search_path.is_file():
                if search_path.name != self.certificate_filename:
                    raise ValueError(
                        "A file supplied to DatasetScanner must be named "
                        f"{self.certificate_filename!r}: {search_path}"
                    )

                certificates.add(
                    search_path.resolve()
                )

                continue

            # The provided path may already be the config directory.
            direct_certificate = (
                search_path
                / self.certificate_filename
            )

            if direct_certificate.is_file():
                certificates.add(
                    direct_certificate.resolve()
                )

            # The provided path may be the version directory.
            version_certificate = (
                search_path
                / self.config_directory_name
                / self.certificate_filename
            )

            if version_certificate.is_file():
                certificates.add(
                    version_certificate.resolve()
                )

            # The provided path may be a task or dataset root.
            for certificate_path in search_path.rglob(
                self.certificate_filename
            ):
                if not certificate_path.is_file():
                    continue

                # Enforce the agreed structure:
                #
                # task/version/config/certificate.yaml
                if (
                    certificate_path.parent.name
                    != self.config_directory_name
                ):
                    continue

                certificates.add(
                    certificate_path.resolve()
                )

        return tuple(
            sorted(
                certificates,
                key=lambda path: str(path).lower(),
            )
        )

    @staticmethod
    def _normalize_paths(
        paths: PathsLike,
    ) -> tuple[Path, ...]:
        """
        Convert one path or an iterable of paths into a tuple.
        """
        if isinstance(paths, (str, Path)):
            return (Path(paths),)

        normalized = tuple(
            Path(path)
            for path in paths
        )

        if not normalized:
            raise ValueError(
                "At least one dataset search path must be provided."
            )

        return normalized


class DatasetLoader:
    """
    Load and validate one dataset version from certificate.yaml.
    """

    def __init__(
        self,
        *,
        validate_paths: bool = True,
        validate_csv_headers: bool = True,
        require_all_splits: bool = True,
    ) -> None:
        self.validate_paths = validate_paths
        self.validate_csv_headers = validate_csv_headers
        self.require_all_splits = require_all_splits

    def load(
        self,
        certificate_path: PathLike,
    ) -> DatasetVersion:
        """
        Load one certificate.yaml and construct DatasetVersion.
        """
        certificate_path = (
            Path(certificate_path)
            .expanduser()
            .resolve()
        )

        if not certificate_path.is_file():
            raise FileNotFoundError(
                f"Dataset certificate was not found: "
                f"{certificate_path}"
            )

        if certificate_path.name != "certificate.yaml":
            raise DatasetCertificateError(
                "Dataset certificate file must be named "
                f"'certificate.yaml': {certificate_path}"
            )

        config_root = certificate_path.parent

        if config_root.name != "config":
            raise DatasetCertificateError(
                "Expected certificate location: "
                "[task]/[version]/config/certificate.yaml. "
                f"Received: {certificate_path}"
            )

        version_root = config_root.parent
        task_root = version_root.parent
        dataset_root = task_root.parent

        inferred_version = version_root.name
        inferred_task = task_root.name

        certificate = self._read_yaml(
            certificate_path
        )

        schema_version = self._require_nonempty_string(
            certificate.get("schema_version"),
            "schema_version",
        )

        dataset_section = self._require_mapping(
            certificate.get("dataset"),
            "dataset",
        )

        dataset_name = self._require_nonempty_string(
            dataset_section.get("name"),
            "dataset.name",
        )

        certificate_version = self._require_nonempty_string(
            dataset_section.get("version"),
            "dataset.version",
        )

        if certificate_version != inferred_version:
            raise DatasetCertificateError(
                "Dataset version in certificate.yaml does not match "
                "the version directory name. "
                f"Certificate: {certificate_version!r}; "
                f"directory: {inferred_version!r}."
            )

        certificate_task = dataset_section.get("task")

        if certificate_task is None:
            task = inferred_task
        else:
            task = self._require_nonempty_string(
                certificate_task,
                "dataset.task",
            )

            if task != inferred_task:
                raise DatasetCertificateError(
                    "Dataset task in certificate.yaml does not match "
                    "the task directory name. "
                    f"Certificate: {task!r}; "
                    f"directory: {inferred_task!r}."
                )

        storage_section = self._require_mapping(
            certificate.get("storage"),
            "storage",
        )

        csv_root = self._resolve_path_reference(
            storage_section.get("csv_root"),
            base_directory=config_root,
            field_name="storage.csv_root",
        )

        data_root = self._resolve_path_reference(
            storage_section.get("data_root"),
            base_directory=config_root,
            field_name="storage.data_root",
        )

        if self.validate_paths:
            if not csv_root.is_dir():
                raise DatasetPathError(
                    f"CSV root directory was not found: {csv_root}"
                )

            if not data_root.is_dir():
                raise DatasetPathError(
                    f"Data root directory was not found: {data_root}"
                )

        split_section = self._require_mapping(
            certificate.get("splits"),
            "splits",
        )

        splits: dict[
            SplitNames,
            DatasetSplit,
        ] = {}

        for split_name in SplitNames:
            split_data = split_section.get(
                split_name.value
            )

            if split_data is None:
                if self.require_all_splits:
                    raise DatasetCertificateError(
                        f"Missing split description: "
                        f"splits.{split_name.value}"
                    )

                continue

            split_data = self._require_mapping(
                split_data,
                f"splits.{split_name.value}",
            )

            csv_specification = split_data.get("csv")

            if csv_specification is None:
                raise DatasetCertificateError(
                    f"Missing field: "
                    f"splits.{split_name.value}.csv"
                )

            csv_path = self._resolve_path_reference(
                csv_specification,
                base_directory=config_root,
                field_name=(
                    f"splits.{split_name.value}.csv"
                ),
            )

            data_directory_specification = split_data.get(
                "data_directory",
                split_name.value,
            )

            data_directory = self._resolve_path_reference(
                data_directory_specification,
                base_directory=data_root,
                field_name=(
                    f"splits."
                    f"{split_name.value}."
                    f"data_directory"
                ),
            )

            if self.validate_paths:
                if not csv_path.is_file():
                    raise DatasetPathError(
                        f"CSV manifest was not found: {csv_path}"
                    )

                if not data_directory.is_dir():
                    raise DatasetPathError(
                        f"Split data directory was not found: "
                        f"{data_directory}"
                    )

            if (
                self.validate_paths
                and self.validate_csv_headers
            ):
                self._validate_csv_manifest(
                    csv_path
                )

            patients = self._read_count_mapping(
                split_data.get("patients", {}),
                (
                    f"splits."
                    f"{split_name.value}."
                    f"patients"
                ),
            )

            images = self._read_count_mapping(
                split_data.get("images", {}),
                (
                    f"splits."
                    f"{split_name.value}."
                    f"images"
                ),
            )

            failed_images = self._read_count_mapping(
                split_data.get(
                    "failed_images",
                    {},
                ),
                (
                    f"splits."
                    f"{split_name.value}."
                    f"failed_images"
                ),
            )

            splits[split_name] = DatasetSplit(
                name=split_name,
                csv_path=csv_path,
                data_directory=data_directory,
                patients=patients,
                images=images,
                failed_images=failed_images,
            )

        return DatasetVersion(
            dataset_name=dataset_name,
            task=task,
            version=certificate_version,
            schema_version=schema_version,
            dataset_root=dataset_root,
            task_root=task_root,
            version_root=version_root,
            certificate_path=certificate_path,
            config_root=config_root,
            csv_root=csv_root,
            data_root=data_root,
            splits=splits,
            certificate=certificate,
        )

    @staticmethod
    def _read_yaml(
        certificate_path: Path,
    ) -> dict[str, Any]:
        """
        Read YAML and ensure that its root is a mapping.
        """
        try:
            with certificate_path.open(
                "r",
                encoding="utf-8",
            ) as yaml_file:
                content = yaml.safe_load(
                    yaml_file
                )
        except yaml.YAMLError as exc:
            raise DatasetCertificateError(
                f"Invalid YAML file: {certificate_path}. "
                f"Error: {exc}"
            ) from exc

        if not isinstance(content, dict):
            raise DatasetCertificateError(
                "The root of certificate.yaml must be a mapping."
            )

        return content

    @staticmethod
    def _require_mapping(
        value: Any,
        field_name: str,
    ) -> Mapping[str, Any]:
        """
        Validate that a certificate field is a mapping.
        """
        if not isinstance(value, Mapping):
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} "
                "must be a mapping."
            )

        return value

    @staticmethod
    def _require_nonempty_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Validate that a certificate field is a non-empty string.
        """
        if not isinstance(value, str):
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} "
                "must be a string."
            )

        value = value.strip()

        if not value:
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} "
                "must not be empty."
            )

        return value

    @classmethod
    def _resolve_path_reference(
        cls,
        path_reference: Any,
        *,
        base_directory: Path,
        field_name: str,
    ) -> Path:
        """
        Resolve a string path or a path-reference mapping.

        Supported mapping format:

            path: "../data"
            path_type: "relative"
            relative_to: "certificate_directory"

        Absolute paths are also supported:

            path: "D:/datasets/task/v1/data"
            path_type: "absolute"
        """
        if isinstance(path_reference, (str, Path)):
            path_value = Path(path_reference)

            if path_value.is_absolute() or path_value.drive:
                return path_value.expanduser().resolve()

            return (
                base_directory
                / path_value
            ).expanduser().resolve()

        if not isinstance(path_reference, Mapping):
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} must be "
                "a string path or a path-reference mapping."
            )

        raw_path = path_reference.get("path")

        if not isinstance(raw_path, str) or not raw_path.strip():
            raise DatasetCertificateError(
                f"Certificate field {field_name!r}.path "
                "must be a non-empty string."
            )

        path_value = Path(raw_path)
        path_type = path_reference.get(
            "path_type",
            "relative",
        )

        if path_type == "absolute":
            if not (
                path_value.is_absolute()
                or path_value.drive
            ):
                raise DatasetCertificateError(
                    f"Certificate field {field_name!r} is marked "
                    "as absolute, but contains a relative path: "
                    f"{raw_path}"
                )

            return path_value.expanduser().resolve()

        if path_type != "relative":
            raise DatasetCertificateError(
                f"Unknown path_type in {field_name!r}: "
                f"{path_type!r}."
            )

        relative_to = path_reference.get(
            "relative_to",
            "certificate_directory",
        )

        if relative_to != "certificate_directory":
            raise DatasetCertificateError(
                f"Unsupported relative_to value in "
                f"{field_name!r}: {relative_to!r}."
            )

        if path_value.is_absolute() or path_value.drive:
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} is marked "
                "as relative, but contains an absolute path: "
                f"{raw_path}"
            )

        return (
            base_directory
            / path_value
        ).expanduser().resolve()

    @staticmethod
    def _read_count_mapping(
        value: Any,
        field_name: str,
    ) -> dict[str, int]:
        """
        Validate a mapping containing non-negative integer counts.
        """
        if not isinstance(value, Mapping):
            raise DatasetCertificateError(
                f"Certificate field {field_name!r} "
                "must be a mapping."
            )

        result: dict[str, int] = {}

        for key, count in value.items():
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
            ):
                raise DatasetCertificateError(
                    f"Certificate count "
                    f"{field_name}.{key} must be a "
                    "non-negative integer."
                )

            result[str(key)] = count

        return result

    @staticmethod
    def _validate_csv_manifest(
        csv_path: Path,
    ) -> None:
        """
        Check that a CSV manifest contains filename and label columns.

        This validates only the header and does not iterate through the
        complete dataset.
        """
        with csv_path.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            reader = csv.DictReader(
                csv_file
            )

            fieldnames = set(
                reader.fieldnames or []
            )

        required_fields = {
            "filename",
            "label",
        }

        missing_fields = (
            required_fields - fieldnames
        )

        if missing_fields:
            missing = ", ".join(
                sorted(missing_fields)
            )

            raise DatasetCertificateError(
                f"CSV manifest {csv_path} is missing "
                f"required columns: {missing}."
            )


class DatasetCatalog:
    """
    In-memory collection of loaded dataset versions.

    Dataset versions are uniquely identified by:

        dataset_name + task + version
    """

    def __init__(self) -> None:
        self._datasets: dict[
            DatasetKey,
            DatasetVersion,
        ] = {}

        self._load_failures: list[
            DatasetLoadFailure
        ] = []

    @classmethod
    def from_paths(
        cls,
        paths: PathsLike,
        *,
        strict: bool = True,
        scanner: DatasetScanner | None = None,
        loader: DatasetLoader | None = None,
    ) -> DatasetCatalog:
        """
        Scan paths, load all discovered certificates, and build a catalog.

        Parameters
        ----------
        paths
            One path or an iterable of paths.
        strict
            If True, stop on the first invalid certificate or duplicate.
            If False, store failures in load_failures and continue.
        scanner
            Optional custom scanner.
        loader
            Optional custom loader.
        """
        scanner = scanner or DatasetScanner()
        loader = loader or DatasetLoader()

        catalog = cls()

        certificate_paths = scanner.scan(
            paths
        )

        for certificate_path in certificate_paths:
            try:
                dataset = loader.load(
                    certificate_path
                )

                catalog.add(dataset)

            except Exception as exc:
                if strict:
                    raise

                catalog._load_failures.append(
                    DatasetLoadFailure(
                        certificate_path=certificate_path,
                        exception_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        return catalog

    @property
    def load_failures(
        self,
    ) -> tuple[DatasetLoadFailure, ...]:
        """
        Return certificates skipped during non-strict loading.
        """
        return tuple(
            self._load_failures
        )

    @property
    def datasets(
        self,
    ) -> tuple[DatasetVersion, ...]:
        """
        Return all loaded datasets.
        """
        return tuple(
            self._datasets.values()
        )

    def add(
        self,
        dataset: DatasetVersion,
    ) -> None:
        """
        Add one loaded dataset version to the catalog.
        """
        key = dataset.key

        if key in self._datasets:
            existing = self._datasets[key]

            raise DuplicateDatasetError(
                "The catalog already contains dataset "
                f"{key}. Existing certificate: "
                f"{existing.certificate_path}; "
                f"new certificate: {dataset.certificate_path}."
            )

        self._datasets[key] = dataset

    def get(
        self,
        dataset_name: str,
        task: str,
        version: str,
    ) -> DatasetVersion:
        """
        Get one exact dataset version.
        """
        key = (
            dataset_name,
            task,
            version,
        )

        try:
            return self._datasets[key]
        except KeyError as exc:
            raise DatasetNotFoundError(
                f"Dataset was not found: {key}."
            ) from exc

    def find(
        self,
        *,
        dataset_name: str | None = None,
        task: str | None = None,
        version: str | None = None,
    ) -> tuple[DatasetVersion, ...]:
        """
        Find datasets matching the supplied fields.

        Any field set to None is not used as a filter.
        """
        matches = [
            dataset
            for dataset in self._datasets.values()
            if (
                dataset_name is None
                or dataset.dataset_name == dataset_name
            )
            and (
                task is None
                or dataset.task == task
            )
            and (
                version is None
                or dataset.version == version
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda dataset: (
                    dataset.dataset_name,
                    dataset.task,
                    _version_sort_key(
                        dataset.version
                    ),
                ),
            )
        )

    def get_versions(
        self,
        dataset_name: str,
        task: str,
    ) -> tuple[DatasetVersion, ...]:
        """
        Return all versions of one dataset task.
        """
        versions = self.find(
            dataset_name=dataset_name,
            task=task,
        )

        if not versions:
            raise DatasetNotFoundError(
                "No versions were found for dataset "
                f"{dataset_name!r}, task {task!r}."
            )

        return versions

    def get_latest(
        self,
        dataset_name: str,
        task: str,
    ) -> DatasetVersion:
        """
        Return the latest version using natural version ordering.

        Examples
        --------
        v2 is ordered before v10.
        1.9 is ordered before 1.10.
        """
        versions = self.get_versions(
            dataset_name=dataset_name,
            task=task,
        )

        return max(
            versions,
            key=lambda dataset: _version_sort_key(
                dataset.version
            ),
        )

    def __len__(self) -> int:
        return len(
            self._datasets
        )

    def __iter__(
        self,
    ) -> Iterator[DatasetVersion]:
        return iter(
            self._datasets.values()
        )

    def __contains__(
        self,
        key: object,
    ) -> bool:
        return key in self._datasets


def _version_sort_key(
    version: str,
) -> tuple[tuple[int, int | str], ...]:
    """
    Create a natural sorting key for version-like strings.
    """
    parts = re.split(
        r"(\d+)",
        version.lower(),
    )

    return tuple(
        (
            (0, int(part))
            if part.isdigit()
            else (1, part)
        )
        for part in parts
        if part
    )


def load_dataset_catalog(
    paths: PathsLike,
    *,
    strict: bool = True,
    validate_paths: bool = True,
    validate_csv_headers: bool = True,
) -> DatasetCatalog:
    """
    Convenience function for scanning and loading dataset versions.
    """
    loader = DatasetLoader(
        validate_paths=validate_paths,
        validate_csv_headers=validate_csv_headers,
    )

    return DatasetCatalog.from_paths(
        paths=paths,
        strict=strict,
        loader=loader,
    )