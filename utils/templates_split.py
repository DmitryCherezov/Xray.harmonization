from enum import StrEnum


class View(StrEnum):
    PA = "PA"
    AP = "AP"
    LA = "LA"


class DetectorType(StrEnum):
    DIRECT = "DIRECT"
    SCINTILLATOR = "SCINTILLATOR"


class SplitType(StrEnum):
    BALANCED = "balanced"
    STANDARD = "60-20-20"


class SplitNames(StrEnum):
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"


class ClinicalCondition(StrEnum):
    ATELECTASIS = "atelectasis"
    CARDIOMEGALY = "cardiomegaly"
    CONSOLIDATION = "consolidation"
    EDEMA = "edema"
    ENLARGED_CARDIOMEDIASTINUM = "enlarged_cardiomediastinum"
    FRACTURE = "fracture"
    LUNG_LESION = "lung_lesion"
    LUNG_OPACITY = "lung_opacity"
    NO_FINDING = "no_finding"
    PLEURAL_EFFUSION = "pleural_effusion"
    PLEURAL_OTHER = "pleural_other"
    PNEUMONIA = "pneumonia"
    PNEUMOTHORAX = "pneumothorax"
    HEALTHY = "healthy"

class BinaryClassDatasetSplitStatistic(StrEnum):
    TRAIN_POSITIVE_PATIENT_NUM = "train_positive_patient_num"
    TRAIN_NEGATIVE_PATIENT_NUM = "train_negative_patient_num"
    VALIDATION_POSITIVE_PATIENT_NUM = "validation_positive_patient_num"
    VALIDATION_NEGATIVE_PATIENT_NUM = "validation_negative_patient_num"
    TEST_POSITIVE_PATIENT_NUM = "test_positive_patient_num"
    TEST_NEGATIVE_PATIENT_NUM = "test_negative_patient_num"

    TRAIN_POSITIVE_IMAGE_NUM = "train_positive_image_num"
    TRAIN_NEGATIVE_IMAGE_NUM = "train_negative_image_num"
    VALIDATION_POSITIVE_IMAGE_NUM = "validation_positive_image_num"
    VALIDATION_NEGATIVE_IMAGE_NUM = "validation_negative_image_num"
    TEST_POSITIVE_IMAGE_NUM = "test_positive_image_num"
    TEST_NEGATIVE_IMAGE_NUM = "test_negative_image_num"


class BinaryClassDatasetReadError(StrEnum):
    TRAIN_POSITIVE = "train_positive_read_error"
    VALIDATION_POSITIVE = "validation_positive_read_error"
    TEST_POSITIVE = "test_positive_read_error"
    TRAIN_NEGATIVE = "train_negative_read_error"
    VALIDATION_NEGATIVE = "validation_negative_read_error"
    TEST_NEGATIVE = "test_negative_read_error"


CLINICAL_CONDITIONS: frozenset[str] = frozenset(
    condition.value for condition in ClinicalCondition
)

# Labels that represent actual findings.
# NO_FINDING and HEALTHY are intentionally excluded.
DISEASE_COLUMNS: tuple[str, ...] = (
    ClinicalCondition.ATELECTASIS.value,
    ClinicalCondition.CARDIOMEGALY.value,
    ClinicalCondition.CONSOLIDATION.value,
    ClinicalCondition.EDEMA.value,
    ClinicalCondition.ENLARGED_CARDIOMEDIASTINUM.value,
    ClinicalCondition.FRACTURE.value,
    ClinicalCondition.LUNG_LESION.value,
    ClinicalCondition.LUNG_OPACITY.value,
    ClinicalCondition.PLEURAL_EFFUSION.value,
    ClinicalCondition.PLEURAL_OTHER.value,
    ClinicalCondition.PNEUMONIA.value,
    ClinicalCondition.PNEUMOTHORAX.value,
)