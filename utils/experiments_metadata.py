from dataclasses import dataclass


@dataclass
class DatasetReportMetadata: 
    title: str 
    task_description: str 
    labeling: str 
    positive_class_description: str 
    negative_class_description: str 
    inclusion_criteria: str 
    exclusion_criteria: str



def get_AP_detection_dataset_metadata() -> DatasetReportMetadata:
    return DatasetReportMetadata(
        title="Acquisition Parameter Detection Dataset",
        task_description=(
            "This dataset was created for a binary classification task "
            "that differentiates PA chest X-ray images acquired using two "
            "different acquisition configurations. The negative class "
            "contains images acquired with a direct detector at 110 kVp, "
            "whereas the positive class contains images acquired with a "
            "scintillator detector at 120 kVp. The dataset is intended for "
            "the development and evaluation of a deep learning model that "
            "can distinguish between these acquisition configurations."
        ),
        labeling=(
            "Class labels were assigned using acquisition parameters "
            "extracted from the DICOM metadata headers. Images acquired "
            "with a direct detector at 110 kVp were assigned label 0, "
            "whereas images acquired with a scintillator detector at "
            "120 kVp were assigned label 1."
        ),
        positive_class_description=(
            "PA chest X-ray images acquired with a scintillator detector "
            "at 120 kVp. These images were assigned label 1."
        ),
        negative_class_description=(
            "PA chest X-ray images acquired with a direct detector "
            "at 110 kVp. These images were assigned label 0."
        ),
        inclusion_criteria=(
            "Patients were required to satisfy the healthy clinical "
            "condition criteria. Only PA chest X-ray images with a known "
            "detector type, known tube voltage, and available exposure "
            "information were included. Eligible images were acquired "
            "either with a direct detector at 110 kVp or with a "
            "scintillator detector at 120 kVp. Exposure was required to "
            "be greater than 0 mAs and less than 6.9 mAs."
        ),
        exclusion_criteria=(
            "Images were excluded if the patient did not satisfy the "
            "healthy clinical condition criteria, the image view was not "
            "PA, or the required acquisition parameters were missing or "
            "unknown. Images were also excluded if the detector type or "
            "tube voltage did not match one of the two target acquisition "
            "configurations, or if the exposure value was outside the "
            "specified range. Unreadable or unsuccessfully converted "
            "DICOM images were excluded during dataset generation."
        ),
    )


