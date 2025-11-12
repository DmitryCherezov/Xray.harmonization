from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import yaml
import os


def _project_root() -> Path:
    """Resolve project root by walking up to the folder that has .git or config/."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "config").is_dir():
            return parent if parent.is_dir() else parent.parent
    return Path.cwd()  # fallback


ROOT = _project_root()
CONFIG_DIR = os.path.join(ROOT, "config")

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class Settings:
    DB_path: Path
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





def load_settings(yaml_profile="default") -> Settings:
    yaml_path = Path( os.path.join(ROOT, 'config', yaml_profile +".yaml")  )
    yaml_settings = _load_yaml( yaml_path )
    
    result = Settings(
        # Database paths
        DB_path = Path(os.path.join( ROOT, 'databases', yaml_settings['DB_name'])),
        # HOSP
        admission_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'admissions'+'.csv') ),
        d_hcpcs_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'd_hcpcs'+'.csv') ),
        d_icd_diagnoses_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'd_icd_diagnoses'+'.csv') ),
        d_icd_procedures_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'd_icd_procedures'+'.csv') ),
        d_labitems_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'd_labitems'+'.csv') ),
        diagnoses_icd_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'diagnoses_icd'+'.csv') ),
        drgcodes_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'drgcodes'+'.csv') ),
        emar_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'emar'+'.csv') ),
        emar_detail_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'emar_detail'+'.csv') ),
        hcpcsevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'hcpcsevents'+'.csv') ),
        labevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'labevents'+'.csv') ),
        microbiologyevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'microbiologyevents'+'.csv') ),
        omr_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'omr'+'.csv') ),
        patients_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'patients'+'.csv') ),
        pharmacy_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'pharmacy'+'.csv') ),
        poe_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'poe'+'.csv') ),
        poe_detail_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'poe_detail'+'.csv') ),
        prescriptions_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'prescriptions'+'.csv') ),
        procedures_icd_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'procedures_icd'+'.csv') ),
        provider_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'provider'+'.csv') ),
        services_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'services'+'.csv') ),
        transfers_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'hosp', 'transfers'+'.csv') ),
        # ICU
        caregiver_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'caregiver'+'.csv') ),
        chartevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'chartevents'+'.csv') ),
        d_items_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'd_items'+'.csv') ),
        datetimeevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'datetimeevents'+'.csv') ),
        icustays_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'icustays'+'.csv') ),
        ingredientevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'ingredientevents'+'.csv') ),
        inputevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'inputevents'+'.csv') ),
        outputevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'outputevents'+'.csv') ),
        procedureevents_csv = Path( os.path.join( yaml_settings['MIMIC_root'], 'physionet.org', 'files', 'mimiciv', '3.1', 'icu', 'procedureevents'+'.csv') )
    )

    return result



if __name__ == "__main__":
    pass
