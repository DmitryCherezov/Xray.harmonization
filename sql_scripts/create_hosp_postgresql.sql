CREATE TABLE "patients" (
  "subject_id" integer PRIMARY KEY NOT NULL,
  "gender" varchar(1) NOT NULL,
  "anchor_age" integer NOT NULL,
  "anchor_year" integer NOT NULL,
  "anchor_year_group" varchar(255) NOT NULL,
  "dod" timestamp
);

CREATE TABLE "omr" (
  "subject_id" integer NOT NULL,
  "chartdate" date NOT NULL,
  "seq_num" integer NOT NULL,
  "result_name" varchar(100) NOT NULL,
  "result_value" text NOT NULL,
  PRIMARY KEY ("subject_id", "chartdate", "seq_num")
);

CREATE TABLE "provider" (
  "provider_id" varchar(10) PRIMARY KEY NOT NULL
);

CREATE TABLE "admissions" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer PRIMARY KEY NOT NULL,
  "admittime" timestamp NOT NULL,
  "dischtime" timestamp,
  "deathtime" timestamp,
  "admission_type" varchar(40) NOT NULL,
  "admit_provider_id" varchar(10),
  "admission_location" varchar(60),
  "discharge_location" varchar(60),
  "insurance" varchar(255),
  "language" varchar(10),
  "marital_status" varchar(30),
  "race" varchar(80),
  "edregtime" timestamp,
  "edouttime" timestamp,
  "hospital_expire_flag" smallint
);

CREATE TABLE "d_hcpcs" (
  "code" char(5) PRIMARY KEY NOT NULL,
  "category" smallint,
  "long_description" text,
  "short_description" varchar(180)
);

CREATE TABLE "hcpcsevents" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer NOT NULL,
  "chartdate" date,
  "hcpcs_cd" char(5) NOT NULL,
  "seq_num" integer NOT NULL,
  "short_description" varchar(180),
  PRIMARY KEY ("hadm_id", "seq_num")
);

CREATE TABLE "d_icd_diagnoses" (
  "icd_code" char(7) NOT NULL,
  "icd_version" integer NOT NULL,
  "long_title" varchar(255),
  PRIMARY KEY ("icd_code", "icd_version")
);

CREATE TABLE "diagnoses_icd" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer NOT NULL,
  "seq_num" integer NOT NULL,
  "icd_code" varchar(7),
  "icd_version" integer,
  PRIMARY KEY ("hadm_id", "seq_num")
);

CREATE TABLE "d_icd_procedures" (
  "icd_code" char(7) NOT NULL,
  "icd_version" integer NOT NULL,
  "long_title" varchar(255),
  PRIMARY KEY ("icd_code", "icd_version")
);

CREATE TABLE "procedures_icd" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer NOT NULL,
  "seq_num" integer NOT NULL,
  "chartdate" date NOT NULL,
  "icd_code" varchar(7),
  "icd_version" integer,
  PRIMARY KEY ("hadm_id", "seq_num")
);

CREATE TABLE "d_labitems" (
  "itemid" integer PRIMARY KEY,
  "label" varchar(50),
  "fluid" varchar(50),
  "category" varchar(50)
);

CREATE TABLE "labevents" (
  "labevent_id" integer PRIMARY KEY NOT NULL,
  "subject_id" integer NOT NULL,
  "hadm_id" integer,
  "specimen_id" integer NOT NULL,
  "itemid" integer NOT NULL,
  "order_provider_id" varchar(10),
  "charttime" timestamp,
  "storetime" timestamp,
  "value" varchar(200),
  "valuenum" double,
  "valueuom" varchar(20),
  "ref_range_lower" double,
  "ref_range_upper" double,
  "flag" varchar(10),
  "priority" varchar(7),
  "comments" text
);

CREATE TABLE "microbiologyevents" (
  "microevent_id" integer PRIMARY KEY NOT NULL,
  "subject_id" integer NOT NULL,
  "hadm_id" integer,
  "micro_specimen_id" integer NOT NULL,
  "order_provider_id" varchar(10),
  "chartdate" timestamp NOT NULL,
  "charttime" timestamp,
  "spec_itemid" integer NOT NULL,
  "spec_type_desc" varchar(100) NOT NULL,
  "test_seq" integer NOT NULL,
  "storedate" timestamp,
  "storetime" timestamp,
  "test_itemid" integer,
  "test_name" varchar(100),
  "org_itemid" integer,
  "org_name" varchar(100),
  "isolate_num" smallint,
  "quantity" varchar(50),
  "ab_itemid" integer,
  "ab_name" varchar(30),
  "dilution_text" varchar(10),
  "dilution_comparison" varchar(20),
  "dilution_value" double,
  "interpretation" varchar(5),
  "comments" text
);

CREATE TABLE "drgcodes" (
  "subject_id" integer,
  "hadm_id" integer,
  "drg_type" varchar(4),
  "drg_code" varchar(10),
  "description" varchar(195),
  "drg_severity" smallint,
  "drg_mortality" smallint
);

CREATE TABLE "poe" (
  "poe_id" varchar(25) PRIMARY KEY NOT NULL,
  "poe_seq" integer NOT NULL,
  "subject_id" integer NOT NULL,
  "hadm_id" integer,
  "ordertime" timestamp NOT NULL,
  "order_type" varchar(25) NOT NULL,
  "order_subtype" varchar(50),
  "transaction_type" varchar(15),
  "discontinue_of_poe_id" varchar(25),
  "discontinued_by_poe_id" varchar(25),
  "order_provider_id" varchar(10),
  "order_status" varchar(15)
);

CREATE TABLE "poe_detail" (
  "poe_id" varchar(25) NOT NULL,
  "poe_seq" integer NOT NULL,
  "subject_id" integer NOT NULL,
  "field_name" varchar(255) NOT NULL,
  "field_value" text,
  PRIMARY KEY ("poe_id", "field_name")
);

CREATE TABLE "pharmacy" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer NOT NULL,
  "pharmacy_id" integer PRIMARY KEY NOT NULL,
  "poe_id" varchar(25),
  "starttime" timestamp,
  "stoptime" timestamp,
  "medication" text,
  "proc_type" varchar(50) NOT NULL,
  "status" varchar(50),
  "entertime" timestamp NOT NULL,
  "verifiedtime" timestamp,
  "route" varchar(50),
  "frequency" varchar(50),
  "disp_sched" varchar(255),
  "infusion_type" varchar(15),
  "sliding_scale" varchar(1),
  "lockout_interval" varchar(50),
  "basal_rate" real,
  "one_hr_max" varchar(10),
  "doses_per_24_hrs" real,
  "duration" real,
  "duration_interval" varchar(50),
  "expiration_value" integer,
  "expiration_unit" varchar(50),
  "expirationdate" timestamp,
  "dispensation" varchar(50),
  "fill_quantity" varchar(50)
);

CREATE TABLE "prescriptions" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer NOT NULL,
  "pharmacy_id" integer NOT NULL,
  "poe_id" varchar(25),
  "poe_seq" integer,
  "order_provider_id" varchar(10),
  "starttime" timestamp,
  "stoptime" timestamp,
  "drug_type" varchar(20) NOT NULL,
  "drug" varchar(255) NOT NULL,
  "formulary_drug_cd" varchar(50),
  "gsn" varchar(255),
  "ndc" varchar(25),
  "prod_strength" varchar(255),
  "form_rx" varchar(25),
  "dose_val_rx" varchar(100),
  "dose_unit_rx" varchar(50),
  "form_val_disp" varchar(50),
  "form_unit_disp" varchar(50),
  "doses_per_24_hrs" real,
  "route" varchar(50),
  PRIMARY KEY ("pharmacy_id", "drug_type")
);

CREATE TABLE "emar" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer,
  "emar_id" varchar(25) PRIMARY KEY NOT NULL,
  "emar_seq" integer NOT NULL,
  "poe_id" varchar(25) NOT NULL,
  "pharmacy_id" integer,
  "enter_provider_id" varchar(10),
  "charttime" timestamp NOT NULL,
  "medication" text,
  "event_txt" varchar(100),
  "scheduletime" timestamp,
  "storetime" timestamp NOT NULL
);

CREATE TABLE "emar_detail" (
  "subject_id" integer NOT NULL,
  "emar_id" varchar(25) NOT NULL,
  "emar_seq" integer NOT NULL,
  "parent_field_ordinal" varchar(10),
  "administration_type" varchar(50),
  "pharmacy_id" integer,
  "barcode_type" varchar(4),
  "reason_for_no_barcode" text,
  "complete_dose_not_given" varchar(5),
  "dose_due" varchar(100),
  "dose_due_unit" varchar(50),
  "dose_given" varchar(255),
  "dose_given_unit" varchar(50),
  "will_remainder_of_dose_be_given" varchar(5),
  "product_amount_given" varchar(30),
  "product_unit" varchar(30),
  "product_code" varchar(30),
  "product_description" varchar(255),
  "product_description_other" varchar(255),
  "prior_infusion_rate" varchar(40),
  "infusion_rate" varchar(40),
  "infusion_rate_adjustment" varchar(50),
  "infusion_rate_adjustment_amount" varchar(30),
  "infusion_rate_unit" varchar(30),
  "route" varchar(10),
  "infusion_complete" varchar(1),
  "completion_interval" varchar(50),
  "new_iv_bag_hung" varchar(1),
  "continued_infusion_in_other_location" varchar(1),
  "restart_interval" text,
  "side" varchar(10),
  "site" varchar(255),
  "non_formulary_visual_verification" varchar(1),
  PRIMARY KEY ("emar_id", "emar_seq", "parent_field_ordinal")
);

CREATE TABLE "services" (
  "subject_id" integer,
  "hadm_id" integer,
  "transfertime" timestamp,
  "prev_service" varchar(20),
  "curr_service" varchar(20),
  PRIMARY KEY ("hadm_id", "transfertime", "curr_service")
);

CREATE TABLE "transfers" (
  "subject_id" integer NOT NULL,
  "hadm_id" integer,
  "transfer_id" integer PRIMARY KEY NOT NULL,
  "eventtype" varchar(10),
  "careunit" varchar(255),
  "intime" timestamp,
  "outtime" timestamp
);

CREATE TABLE "studies" (
  "study_id" integer PRIMARY KEY NOT NULL,
  "subject_id" integer NOT NULL
);

CREATE TABLE "images" (
  "image_id" integer PRIMARY KEY NOT NULL,
  "study_id" integer NOT NULL,
  "file_path" text
);

CREATE TABLE "image_acquisition" (
  "image_id" integer PRIMARY KEY NOT NULL,
  "view_code" varchar(16),
  "kvp" real,
  "detector_type_code" varchar(32),
  "rows" integer,
  "cols" integer,
  "pixel_spacing_row" real,
  "pixel_spacing_col" real,
  "exposure_mas" real,
  "exposure_time_ms" real,
  "body_part" text,
  "manufacturer" text,
  "model_name" text
);

CREATE TABLE "chexpert_diagnosisi" (
  "study_id" integer PRIMARY KEY NOT NULL,
  "atelectasis" integer,
  "cardiomegaly" integer,
  "consolidation" integer,
  "edema" integer,
  "enlarged_cardiomediastinum" integer,
  "fracture" integer,
  "lung_lesion" integer,
  "lung_opacity" integer,
  "no_finding" integer,
  "pleural_effusion" integer,
  "pleural_other" integer,
  "pneumonia" integer,
  "pneumothorax" integer,
  "support_devices" integer
);

COMMENT ON COLUMN "provider"."provider_id" IS 'Pattern like P003AB, P00102. Random deidentified identifier.';

COMMENT ON COLUMN "image_acquisition"."view_code" IS 'e.g., PA/AP/LAT';

COMMENT ON COLUMN "image_acquisition"."detector_type_code" IS 'e.g., DIRECT/SCINTILLATOR/CR';

COMMENT ON COLUMN "image_acquisition"."pixel_spacing_row" IS 'mm/pixel';

COMMENT ON COLUMN "image_acquisition"."pixel_spacing_col" IS 'mm/pixel';

ALTER TABLE "omr" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "admissions" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "admissions" ADD FOREIGN KEY ("admit_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "hcpcsevents" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "hcpcsevents" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "hcpcsevents" ADD FOREIGN KEY ("hcpcs_cd") REFERENCES "d_hcpcs" ("code") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "diagnoses_icd" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "diagnoses_icd" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "diagnoses_icd" ADD FOREIGN KEY ("icd_code", "icd_version") REFERENCES "d_icd_diagnoses" ("icd_code", "icd_version") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "procedures_icd" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "procedures_icd" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "procedures_icd" ADD FOREIGN KEY ("icd_code", "icd_version") REFERENCES "d_icd_procedures" ("icd_code", "icd_version") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "labevents" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "labevents" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "labevents" ADD FOREIGN KEY ("itemid") REFERENCES "d_labitems" ("itemid") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "labevents" ADD FOREIGN KEY ("order_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "microbiologyevents" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "microbiologyevents" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "microbiologyevents" ADD FOREIGN KEY ("order_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "drgcodes" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "drgcodes" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe" ADD FOREIGN KEY ("order_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe" ADD FOREIGN KEY ("discontinue_of_poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe" ADD FOREIGN KEY ("discontinued_by_poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "poe_detail" ADD FOREIGN KEY ("poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pharmacy" ADD FOREIGN KEY ("poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pharmacy" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pharmacy" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "prescriptions" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "prescriptions" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "prescriptions" ADD FOREIGN KEY ("pharmacy_id") REFERENCES "pharmacy" ("pharmacy_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "prescriptions" ADD FOREIGN KEY ("poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "prescriptions" ADD FOREIGN KEY ("order_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar" ADD FOREIGN KEY ("poe_id") REFERENCES "poe" ("poe_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar" ADD FOREIGN KEY ("pharmacy_id") REFERENCES "pharmacy" ("pharmacy_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar" ADD FOREIGN KEY ("enter_provider_id") REFERENCES "provider" ("provider_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar_detail" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar_detail" ADD FOREIGN KEY ("emar_id") REFERENCES "emar" ("emar_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "emar_detail" ADD FOREIGN KEY ("pharmacy_id") REFERENCES "pharmacy" ("pharmacy_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "services" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "services" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transfers" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transfers" ADD FOREIGN KEY ("hadm_id") REFERENCES "admissions" ("hadm_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "studies" ADD FOREIGN KEY ("subject_id") REFERENCES "patients" ("subject_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "images" ADD FOREIGN KEY ("study_id") REFERENCES "studies" ("study_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "image_acquisition" ADD FOREIGN KEY ("image_id") REFERENCES "images" ("image_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "chexpert_diagnosisi" ADD FOREIGN KEY ("study_id") REFERENCES "studies" ("study_id") DEFERRABLE INITIALLY IMMEDIATE;
