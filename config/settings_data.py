from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import yaml
import os
from config.settings_project import ProjectPaths


###############################################################################
#   CONSTANTS
###############################################################################

_config_instance = None


    #DB_path: Path
    #sql_hosp_creation_script: Path
    
###############################################################################
#   DATA CLASSES
###############################################################################
@dataclass(frozen=True, slots=True)
class DataSetsSettings:
    MIMIC_IV_root: Path
    MIMIC_CXR_root: Path
    MIMIC_CXR_JPG_root: Path
    
    @classmethod
    def build(cls, profile:str='default') -> "DataSetsSettings":
        conf = _get_config(profile)
        return cls(
            MIMIC_IV_root = Path(
                conf.get('MIMIC_IV_root')
            ),
            MIMIC_CXR_root = Path(
                conf.get('MIMIC_CXR_root')
            ),
            MIMIC_CXR_JPG_root = Path(
                conf.get('MIMIC_CXR_JPG_root')
            )
        )



@dataclass(frozen=True, slots=True)
class CSVSettings:
    admission_csv: Path
    d_hcpcs_csv: Path
    d_icd_diagnoses_csv: Path
    d_icd_procedures_csv: Path
    d_labitems_csv: Path
    diagnoses_icd_csv: Path
    drgcodes_csv: Path
    emar_csv: Path
    emar_detail_csv: Path
    hcpcsevents_csv: Path
    labevents_csv: Path
    microbiologyevents_csv: Path
    omr_csv: Path
    patients_csv: Path
    pharmacy_csv: Path
    poe_csv: Path
    poe_detail_csv: Path
    prescriptions_csv: Path
    procedures_icd_csv: Path
    provider_csv: Path
    services_csv: Path
    transfers_csv: Path
    caregiver_csv: Path
    chartevents_csv: Path
    d_items_csv: Path
    datetimeevents_csv: Path
    icustays_csv: Path
    ingredientevents_csv: Path
    inputevents_csv: Path
    outputevents_csv: Path
    procedureevents_csv: Path


class YamlConfigManager:
    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path
        self._data: dict[str, Any] = {}
        self.reload()

    @classmethod
    def from_profile(cls, yaml_profile: str = "default") -> "YamlConfigManager":
        paths = ProjectPaths.build()
        yaml_path = paths.config / f"{yaml_profile}.yaml"
        return cls(yaml_path)

    def reload(self) -> None:
        if not self.yaml_path.exists():
            self._data = {}
            return

        with self.yaml_path.open("r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    def save(self) -> None:
        with self.yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self._data, f, sort_keys=False, allow_unicode=True)

    def get(self, param_name: str, default: Any = None) -> Any:
        return self._data.get(param_name, default)

    def set(self, param_name: str, value: Any, autosave: bool = True) -> None:
        self._data[param_name] = value
        if autosave:
            self.save()

###############################################################################
#   UTIL FUNCTIONS
###############################################################################
'''
def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
'''

def _get_config(profile: str = "default"):
    global _config_instance

    if _config_instance is None:
        paths = ProjectPaths.build()
        yaml_path = paths.config / f"{profile}.yaml"
        _config_instance = YamlConfigManager(yaml_path)

    return _config_instance


###############################################################################
#   MAIN INTERFACE FUNCTIONS
###############################################################################


def load_csv_settings(yaml_profile: str = "default") -> CSVSettings:
    paths = DataSetsSettings.build()

    hosp_root = Path( os.path.join(
        paths.MIMIC_IV_root,
        'physionet.org',
        'files',
        'mimiciv',
        '3.1',
        'hosp'
        ))
    
    ICU_root = Path( os.path.join(
        paths.MIMIC_IV_root,
        'physionet.org',
        'files',
        'mimiciv',
        '3.1',
        'icu'
        ))

    result = CSVSettings(
        # Database paths
        #DB_path = Path(os.path.join( ROOT, 'databases', yaml_settings['DB_name'])),
        # HOSP
        admission_csv = hosp_root / 'admissions.csv',
        d_hcpcs_csv = hosp_root / 'd_hcpcs.csv',
        d_icd_diagnoses_csv = hosp_root / 'd_icd_diagnoses.csv',
        d_icd_procedures_csv = hosp_root / 'd_icd_procedures.csv',
        d_labitems_csv = hosp_root / 'd_labitems.csv',
        diagnoses_icd_csv = hosp_root / 'diagnoses_icd.csv',
        drgcodes_csv = hosp_root / 'drgcodes.csv',
        emar_csv = hosp_root / 'emar.csv',
        emar_detail_csv = hosp_root / 'emar_detail.csv',
        hcpcsevents_csv = hosp_root / 'hcpcsevents.csv',
        labevents_csv = hosp_root / 'labevents.csv',
        microbiologyevents_csv = hosp_root / 'microbiologyevents.csv',
        omr_csv = hosp_root / 'omr.csv',
        patients_csv = hosp_root / 'patients.csv',
        pharmacy_csv = hosp_root / 'pharmacy.csv',
        poe_csv = hosp_root / 'poe.csv',
        poe_detail_csv = hosp_root / 'poe_detail.csv',
        prescriptions_csv = hosp_root / 'prescriptions.csv',
        procedures_icd_csv = hosp_root / 'procedures_icd.csv',
        provider_csv = hosp_root / 'provider.csv',
        services_csv = hosp_root / 'services.csv',
        transfers_csv = hosp_root / 'transfers.csv',
        # ICU
        caregiver_csv = ICU_root / 'caregiver.csv',
        chartevents_csv = ICU_root / 'chartevents.csv',
        d_items_csv = ICU_root / 'd_items.csv',
        datetimeevents_csv = ICU_root / 'datetimeevents.csv',
        icustays_csv = ICU_root / 'icustays.csv',
        ingredientevents_csv = ICU_root / 'ingredientevents.csv',
        inputevents_csv = ICU_root / 'inputevents.csv',
        outputevents_csv = ICU_root / 'outputevents.csv',
        procedureevents_csv = ICU_root / 'procedureevents.csv'
    )

    return result

