#==============================================================================
#                   URLS
#==============================================================================


MIMIC_IV_URL = "https://physionet.org/files/mimiciv/3.1/"
MIMIC_CXR_URL = "https://physionet.org/files/mimic-cxr/2.1.0/"
MIMIC_CXR_CHECKSUM_URL = "https://physionet.org/files/mimic-cxr/2.1.0/SHA256SUMS.txt"
MIMIC_CXR_JPG_URL = "https://physionet.org/files/mimic-cxr-jpg/2.1.0/mimic-cxr-2.0.0-chexpert.csv.gz"

#==============================================================================
#                   PATHS
#==============================================================================

MIMIC_CXR_JPG_DIAGNOSING_CSV_GZ_PARTS = (
    "physionet.org", "files", "mimic-cxr-jpg", "2.1.0", "mimic-cxr-2.0.0-chexpert.csv.gz"
)
#==============================================================================
#                   FILE EXTENSIONS
#==============================================================================

CSV_GZ_EXTENSION = ".gz"


#==============================================================================
#                   MESSAGES
#==============================================================================

MESSAGE_ROOT_FOUND = '[X] Root fount'

MESSAGE_NUMBER_CSV_FILES_CHECKED = 'Number of CSV files checked: {csv_file_num}'
MESSAGE_REQUIRED_CSV_NOT_FOUND = 'Required CSV file not found:\n{csv_file_path}'
MESSAGE_ALL_FILES_FOUND = '[X] All required CSV files found'
MESSAGE_SQLITE_CONNECTION_READY = '[X] Connection is ready'


MESSAGE_SUCCESS_DOWNLOAD = "\n✅ Download complete."
MESSAGE_ERROR_WITH_CODE = "\n❌ wget exited with code {error_code}."

MESSAGE_ZIP_NOT_FOUND = "ZIP not found: {zip_path}"
MESSAGE_ZIP_FILE_EXISTS = "Extracted to: {target_dir}"

ERROR_CHECK_SUM_FILE_MISSING = "SHA256SUMS.txt not found inside dataset directory"

MESSAGE_MISSING_TYPE = 'Number of {error_type}: {error_num}'
MESSAGE_SUCCESS_UNZIP = "\n✅ Unzipping complete."

ERROR_SHA_FILE_NOT_FOUND = '"SHA256SUMS.txt is not found"'

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

WGET_FLIST_CMD = (
    "wget "
    "-r -N -c -np "
    "--show-progress --progress=bar:force:noscroll "
    "--user {username} "
    "--password {password} "
    "-i {filelist}"
)



