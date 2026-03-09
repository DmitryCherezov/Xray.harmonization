#==============================================================================
#                   COMMAND TEMPLATES
#==============================================================================

CONFIG_FOLDER_NAME = 'config'


#==============================================================================
#                   URLS
#==============================================================================


MIMIC_IV_URL = "https://physionet.org/files/mimiciv/3.1/"
MIMIC_CXR_URL = "https://physionet.org/files/mimic-cxr/2.1.0/"
MIMIC_CXR_JPG_URL = "https://physionet.org/files/mimic-cxr-jpg/2.1.0/mimic-cxr-2.0.0-chexpert.csv.gz"

#==============================================================================
#                   PATHS
#==============================================================================

MIMIC_CXR_JPG_DIAGNOSING_CSV_GZ_PARTS = (
    "physionet.org", "files", "mimic-cxr-jpg", "2.1.0", "mimic-cxr-2.0.0-chexpert.csv.gz"
)


#==============================================================================
#                   MESSAGES
#==============================================================================

MESSAGE_ROOT_FOUND = '[X] Root fount'

MESSAGE_REQUIRED_CSV_NOT_FOUND = 'Required CSV file not found:\n{csv_file_path}'
MESSAGE_ALL_FILES_FOUND = '[X] All required CSV files found'
MESSAGE_SQLITE_CONNECTION_READY = '[X] Connection is ready'


MESSAGE_SUCCESS_DOWNLOAD = "\n✅ Download complete."
MESSAGE_ERROR_WITH_CODE = "\n❌ wget exited with code {error_code}."

ZIP_NOT_FOUND_MESSAGE = "ZIP not found: {zip_path}"
ZIP_FILE_EXISTS_MESSAGE = "Extracted to: {target_dir}"

#==============================================================================
#                   COMMAND TEMPLATES
#==============================================================================

WGET_CMD = (
    "wget "
    "-r -N -c -np "
    "--show-progress --progress=bar:force:noscroll "
    "--user {username} "
    "--password {password} "
    "{url}"

)




