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
    DB_name: Path
    admission_csv: Path
    patient_csv: Path
    transfer_csv: Path

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
    pharmacy_csv: Path
    poe_csv: Path
    poe_detail_csv: Path
    prescriptions_csv: Path
    procedures_icd_csv: Path
    services_csv: Path


def load_settings(yaml_profile="default") -> Settings:
    yaml_path = Path( os.path.join(ROOT, 'config', yaml_profile +".yaml")  )
    settings = _load_yaml( yaml_path )
    
    result = Settings(

        DB_path = Path(os.path.join( ROOT, 'databases', settings['DB_name'])),
        admission_csv = Path( os.path.join( settings['MIMIC_root'], 'core', 'admissions'+'.csv') ),
        patient_csv = Path( os.path.join( settings['MIMIC_root'], 'core', 'patients'+'.csv') ),
        transfer_csv = Path( os.path.join( settings['MIMIC_root'], 'core', 'transfers'+'.csv') ),

        d_hcpcs_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'd_hcpcs'+'.csv') ),
        d_icd_diagnoses_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'd_icd_diagnoses'+'.csv') ),
        d_icd_procedures_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'd_icd_procedures'+'.csv') ),
        d_labitems_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'd_labitems'+'.csv') ),
        diagnoses_icd_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'diagnoses_icd'+'.csv') ),
        drgcodes_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'drgcodes'+'.csv') ),
        emar_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'emar'+'.csv') ),
        emar_detail_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'emar_detail'+'.csv') ),
        hcpcsevents_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'hcpcsevents'+'.csv') ),
        labevents_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'labevents'+'.csv') ),
        microbiologyevents_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'microbiologyevents'+'.csv') ),
        pharmacy_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'pharmacy'+'.csv') ),
        poe_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'poe'+'.csv') ),
        poe_detail_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'poe_detail'+'.csv') ),
        prescriptions_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'prescriptions'+'.csv') ),
        procedures_icd_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'procedures_icd'+'.csv') ),
        services_csv = Path( os.path.join( settings['MIMIC_root'], 'hosp', 'services'+'.csv') )

    )

    return result



if __name__ == "__main__":
    pass
