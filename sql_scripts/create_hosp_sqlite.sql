PRAGMA foreign_keys = ON;

CREATE TABLE patients (
  subject_id INTEGER PRIMARY KEY NOT NULL,
  gender TEXT NOT NULL,
  anchor_age INTEGER NOT NULL,
  anchor_year INTEGER NOT NULL,
  anchor_year_group TEXT NOT NULL,
  dod TEXT
);

CREATE TABLE provider (
  provider_id TEXT PRIMARY KEY NOT NULL
);

CREATE TABLE omr (
  subject_id INTEGER NOT NULL,
  chartdate TEXT NOT NULL,
  seq_num INTEGER NOT NULL,
  result_name TEXT NOT NULL,
  result_value TEXT NOT NULL,
  PRIMARY KEY (subject_id, chartdate, seq_num),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id)
);

CREATE TABLE admissions (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER PRIMARY KEY NOT NULL,
  admittime TEXT NOT NULL,
  dischtime TEXT,
  deathtime TEXT,
  admission_type TEXT NOT NULL,
  admit_provider_id TEXT,
  admission_location TEXT,
  discharge_location TEXT,
  insurance TEXT,
  language TEXT,
  marital_status TEXT,
  race TEXT,
  edregtime TEXT,
  edouttime TEXT,
  hospital_expire_flag INTEGER,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (admit_provider_id) REFERENCES provider(provider_id)
);

CREATE TABLE d_hcpcs (
  code TEXT PRIMARY KEY NOT NULL,
  category INTEGER,
  long_description TEXT,
  short_description TEXT
);

CREATE TABLE hcpcsevents (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER NOT NULL,
  chartdate TEXT,
  hcpcs_cd TEXT NOT NULL,
  seq_num INTEGER NOT NULL,
  short_description TEXT,
  PRIMARY KEY (hadm_id, seq_num),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (hcpcs_cd) REFERENCES d_hcpcs(code)
);

CREATE TABLE d_icd_diagnoses (
  icd_code TEXT NOT NULL,
  icd_version INTEGER NOT NULL,
  long_title TEXT,
  PRIMARY KEY (icd_code, icd_version)
);

CREATE TABLE diagnoses_icd (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER NOT NULL,
  seq_num INTEGER NOT NULL,
  icd_code TEXT,
  icd_version INTEGER,
  PRIMARY KEY (hadm_id, seq_num),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (icd_code, icd_version) REFERENCES d_icd_diagnoses(icd_code, icd_version)
);

CREATE TABLE d_icd_procedures (
  icd_code TEXT NOT NULL,
  icd_version INTEGER NOT NULL,
  long_title TEXT,
  PRIMARY KEY (icd_code, icd_version)
);

CREATE TABLE procedures_icd (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER NOT NULL,
  seq_num INTEGER NOT NULL,
  chartdate TEXT NOT NULL,
  icd_code TEXT,
  icd_version INTEGER,
  PRIMARY KEY (hadm_id, seq_num),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (icd_code, icd_version) REFERENCES d_icd_procedures(icd_code, icd_version)
);

CREATE TABLE d_labitems (
  itemid INTEGER PRIMARY KEY,
  label TEXT,
  fluid TEXT,
  category TEXT
);

CREATE TABLE labevents (
  labevent_id INTEGER PRIMARY KEY NOT NULL,
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER,
  specimen_id INTEGER NOT NULL,
  itemid INTEGER NOT NULL,
  order_provider_id TEXT,
  charttime TEXT,
  storetime TEXT,
  value TEXT,
  valuenum REAL,
  valueuom TEXT,
  ref_range_lower REAL,
  ref_range_upper REAL,
  flag TEXT,
  priority TEXT,
  comments TEXT,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (itemid) REFERENCES d_labitems(itemid),
  FOREIGN KEY (order_provider_id) REFERENCES provider(provider_id)
);

CREATE TABLE microbiologyevents (
  microevent_id INTEGER PRIMARY KEY NOT NULL,
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER,
  micro_specimen_id INTEGER NOT NULL,
  order_provider_id TEXT,
  chartdate TEXT NOT NULL,
  charttime TEXT,
  spec_itemid INTEGER NOT NULL,
  spec_type_desc TEXT NOT NULL,
  test_seq INTEGER NOT NULL,
  storedate TEXT,
  storetime TEXT,
  test_itemid INTEGER,
  test_name TEXT,
  org_itemid INTEGER,
  org_name TEXT,
  isolate_num INTEGER,
  quantity TEXT,
  ab_itemid INTEGER,
  ab_name TEXT,
  dilution_text TEXT,
  dilution_comparison TEXT,
  dilution_value REAL,
  interpretation TEXT,
  comments TEXT,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (order_provider_id) REFERENCES provider(provider_id)
);

CREATE TABLE drgcodes (
  subject_id INTEGER,
  hadm_id INTEGER,
  drg_type TEXT,
  drg_code TEXT,
  description TEXT,
  drg_severity INTEGER,
  drg_mortality INTEGER,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE poe (
  poe_id TEXT PRIMARY KEY NOT NULL,
  poe_seq INTEGER NOT NULL,
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER,
  ordertime TEXT NOT NULL,
  order_type TEXT NOT NULL,
  order_subtype TEXT,
  transaction_type TEXT,
  discontinue_of_poe_id TEXT,
  discontinued_by_poe_id TEXT,
  order_provider_id TEXT,
  order_status TEXT,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (order_provider_id) REFERENCES provider(provider_id),
  FOREIGN KEY (discontinue_of_poe_id) REFERENCES poe(poe_id),
  FOREIGN KEY (discontinued_by_poe_id) REFERENCES poe(poe_id)
);

CREATE TABLE poe_detail (
  poe_id TEXT NOT NULL,
  poe_seq INTEGER NOT NULL,
  subject_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  field_value TEXT,
  PRIMARY KEY (poe_id, field_name),
  FOREIGN KEY (poe_id) REFERENCES poe(poe_id)
);

CREATE TABLE pharmacy (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER NOT NULL,
  pharmacy_id INTEGER PRIMARY KEY NOT NULL,
  poe_id TEXT,
  starttime TEXT,
  stoptime TEXT,
  medication TEXT,
  proc_type TEXT NOT NULL,
  status TEXT,
  entertime TEXT NOT NULL,
  verifiedtime TEXT,
  route TEXT,
  frequency TEXT,
  disp_sched TEXT,
  infusion_type TEXT,
  sliding_scale TEXT,
  lockout_interval TEXT,
  basal_rate REAL,
  one_hr_max TEXT,
  doses_per_24_hrs REAL,
  duration REAL,
  duration_interval TEXT,
  expiration_value INTEGER,
  expiration_unit TEXT,
  expirationdate TEXT,
  dispensation TEXT,
  fill_quantity TEXT,
  FOREIGN KEY (poe_id) REFERENCES poe(poe_id),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE prescriptions (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER NOT NULL,
  pharmacy_id INTEGER NOT NULL,
  poe_id TEXT,
  poe_seq INTEGER,
  order_provider_id TEXT,
  starttime TEXT,
  stoptime TEXT,
  drug_type TEXT NOT NULL,
  drug TEXT NOT NULL,
  formulary_drug_cd TEXT,
  gsn TEXT,
  ndc TEXT,
  prod_strength TEXT,
  form_rx TEXT,
  dose_val_rx TEXT,
  dose_unit_rx TEXT,
  form_val_disp TEXT,
  form_unit_disp TEXT,
  doses_per_24_hrs REAL,
  route TEXT,
  PRIMARY KEY (pharmacy_id, drug_type),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (pharmacy_id) REFERENCES pharmacy(pharmacy_id),
  FOREIGN KEY (poe_id) REFERENCES poe(poe_id),
  FOREIGN KEY (order_provider_id) REFERENCES provider(provider_id)
);

CREATE TABLE emar (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER,
  emar_id TEXT PRIMARY KEY NOT NULL,
  emar_seq INTEGER NOT NULL,
  poe_id TEXT NOT NULL,
  pharmacy_id INTEGER,
  enter_provider_id TEXT,
  charttime TEXT NOT NULL,
  medication TEXT,
  event_txt TEXT,
  scheduletime TEXT,
  storetime TEXT NOT NULL,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id),
  FOREIGN KEY (poe_id) REFERENCES poe(poe_id),
  FOREIGN KEY (pharmacy_id) REFERENCES pharmacy(pharmacy_id),
  FOREIGN KEY (enter_provider_id) REFERENCES provider(provider_id)
);

CREATE TABLE emar_detail (
  subject_id INTEGER NOT NULL,
  emar_id TEXT NOT NULL,
  emar_seq INTEGER NOT NULL,
  parent_field_ordinal TEXT,
  administration_type TEXT,
  pharmacy_id INTEGER,
  barcode_type TEXT,
  reason_for_no_barcode TEXT,
  complete_dose_not_given TEXT,
  dose_due TEXT,
  dose_due_unit TEXT,
  dose_given TEXT,
  dose_given_unit TEXT,
  will_remainder_of_dose_be_given TEXT,
  product_amount_given TEXT,
  product_unit TEXT,
  product_code TEXT,
  product_description TEXT,
  product_description_other TEXT,
  prior_infusion_rate TEXT,
  infusion_rate TEXT,
  infusion_rate_adjustment TEXT,
  infusion_rate_adjustment_amount TEXT,
  infusion_rate_unit TEXT,
  route TEXT,
  infusion_complete TEXT,
  completion_interval TEXT,
  new_iv_bag_hung TEXT,
  continued_infusion_in_other_location TEXT,
  restart_interval TEXT,
  side TEXT,
  site TEXT,
  non_formulary_visual_verification TEXT,
  PRIMARY KEY (emar_id, emar_seq, parent_field_ordinal),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (emar_id) REFERENCES emar(emar_id),
  FOREIGN KEY (pharmacy_id) REFERENCES pharmacy(pharmacy_id)
);

CREATE TABLE services (
  subject_id INTEGER,
  hadm_id INTEGER,
  transfertime TEXT,
  prev_service TEXT,
  curr_service TEXT,
  PRIMARY KEY (hadm_id, transfertime, curr_service),
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE transfers (
  subject_id INTEGER NOT NULL,
  hadm_id INTEGER,
  transfer_id INTEGER PRIMARY KEY NOT NULL,
  eventtype TEXT,
  careunit TEXT,
  intime TEXT,
  outtime TEXT,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE studies (
  study_id INTEGER PRIMARY KEY NOT NULL,
  subject_id INTEGER NOT NULL,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id)
);

CREATE TABLE images (
  image_id INTEGER PRIMARY KEY NOT NULL,
  study_id INTEGER NOT NULL,
  file_path TEXT,
  FOREIGN KEY (study_id) REFERENCES studies(study_id)
);

CREATE TABLE image_acquisition (
  image_id INTEGER PRIMARY KEY NOT NULL,
  view_code TEXT,
  kvp REAL,
  detector_type_code TEXT,
  rows INTEGER,
  cols INTEGER,
  pixel_spacing_row REAL,
  pixel_spacing_col REAL,
  exposure_mas REAL,
  exposure_time_ms REAL,
  body_part TEXT,
  manufacturer TEXT,
  model_name TEXT,
  FOREIGN KEY (image_id) REFERENCES images(image_id)
);

CREATE TABLE chexpert_diagnosisi (
  study_id INTEGER PRIMARY KEY NOT NULL,
  atelectasis INTEGER,
  cardiomegaly INTEGER,
  consolidation INTEGER,
  edema INTEGER,
  enlarged_cardiomediastinum INTEGER,
  fracture INTEGER,
  lung_lesion INTEGER,
  lung_opacity INTEGER,
  no_finding INTEGER,
  pleural_effusion INTEGER,
  pleural_other INTEGER,
  pneumonia INTEGER,
  pneumothorax INTEGER,
  support_devices INTEGER,
  FOREIGN KEY (study_id) REFERENCES studies(study_id)
);
