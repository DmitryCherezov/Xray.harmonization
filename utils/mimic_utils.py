import os
import gzip
import zipfile
import tarfile
import shutil
import hashlib
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Dict, List

def download_mimic_iv(
        username: str,
        password: str,
        target_dir: Path, 
        templates: ModuleType,
        download_url: str = ''
        ):
    
    os.makedirs(target_dir, exist_ok=True)
    os.chdir(target_dir)

    if download_url == '':
        cmd = templates.WGET_CMD.format(
            username=username,
            password=password,
            url=templates.MIMIC_IV_URL
        )
    else:
        cmd = templates.WGET_CMD.format(
            username=username,
            password=password,
            url=download_url
        )


    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdout is None:
        raise RuntimeError("Failed to capture subprocess output")

    for line in proc.stdout:
        print(line, end="", flush=True)

    proc.wait()

    if proc.returncode == 0:
        print(templates.MESSAGE_SUCCESS_DOWNLOAD)
    else:
        print(templates.MESSAGE_ERROR_WITH_CODE)





def checksum_validation_mimic_iv(
        mimic_iv_path: Path, 
        templates: ModuleType
        ) -> Dict[str, List[str]]:
    
    sha_files = list(mimic_iv_path.rglob("SHA256SUMS.txt"))
    if not sha_files:
        raise FileNotFoundError(templates.ERROR_CHECK_SUM_FILE_MISSING)
    sha_file = sha_files[0]
    sha_root = sha_file.parent

    def compute_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    correct_checksum: List[str] = []
    wrong_checksum: List[str] = []
    missing_files: List[str] = []


    with sha_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid format in SHA256SUMS.txt at line {line_number}: {line!r}"
                )

            expected_hash, relative_path_str = parts
            relative_path = Path(relative_path_str)
            file_path = sha_root / relative_path

            if not file_path.exists():
                missing_files.append(str(relative_path))
                continue

            actual_hash = compute_sha256(file_path)
            if actual_hash.lower() != expected_hash.lower():
                wrong_checksum.append(str(relative_path))
            else:
                correct_checksum.append(str(file_path))

    return {
        "correct checksum": correct_checksum,
        "wrong checksum": wrong_checksum,
        "missing files": missing_files,
    }


def unpack_mimic_iv(
        correct_files: List[str]
        ):
    
    CHUNK_SIZE = 1024 * 1024

    for file_path in correct_files:
        if file_path.endswith('.gz'):
            src_path = Path(file_path)
            dest_apth = Path(file_path[:-3])
            with gzip.open(src_path, "rb") as f_in, open(dest_apth, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out, length=CHUNK_SIZE)



def download_mimic_cxr(
    username:str,
    password:str,
    target_dir:Path,
    templates:ModuleType
    ) -> None:
    
    download_mimic_iv(
        username = username,
        password = password,
        target_dir = target_dir, 
        templates = templates,
        download_url = templates.MIMIC_CXR_URL
        )

def download_mimic_cxr_checksum(
    username:str,
    password:str,
    target_dir:Path,
    templates:ModuleType
    ) -> Path:
    
    download_mimic_iv(
        username = username,
        password = password,
        target_dir = target_dir, 
        templates = templates,
        download_url = templates.MIMIC_CXR_CHECKSUM_URL
        )
    
    sha_files = list(target_dir.rglob("SHA256SUMS.txt"))
    if len(sha_files) == 0:
        raise FileNotFoundError(templates.ERROR_SHA_FILE_NOT_FOUND)
    sha_file = sha_files[0]
    checksum_path = Path(sha_file)
    return checksum_path


def generate_wget_filelist(
    checksum_path: Path,
    patient_num: int,
    target_dir: Path,
    templates: ModuleType 
    ) -> Path:
    
    file_urls = []
    urls_pids = []
    file_list_path = target_dir / 'MIMIC_CXR_filelist.txt'

    with open(checksum_path, 'r') as fid:
        for line in fid:
            relative_path = line.strip().split(' ')[1]
            if 'files' in relative_path:
                path_structure = relative_path.split('/')
                pid = path_structure[2]
                if (pid not in urls_pids) and (len(urls_pids) < patient_num ):
                    urls_pids.append(pid)
                if (pid in urls_pids):
                    url = templates.MIMIC_CXR_URL + '/' + relative_path
                    file_urls.append(url)

            else:
                url = templates.MIMIC_CXR_URL + relative_path + '\n'
                file_urls.append(url)
    
    with open(file_list_path , 'w') as fid:
        fid.writelines(file_urls)

    return file_list_path


def download_wget_filelist(
    username: str,
    password: str,
    filelist: Path,
    target_dir: Path,
    templates: ModuleType
    ):
    os.makedirs(target_dir, exist_ok=True)
    os.chdir(target_dir)

    cmd = templates.WGET_FLIST_CMD.format(
            username=username,
            password=password,
            filelist=filelist
        )
        


    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdout is None:
        raise RuntimeError("Failed to capture subprocess output")

    for line in proc.stdout:
        print(line, end="", flush=True)

    proc.wait()

    if proc.returncode == 0:
        print(templates.MESSAGE_SUCCESS_DOWNLOAD)
    else:
        print(templates.MESSAGE_ERROR_WITH_CODE)


def filelist_checksum_validation(
        filelist: Path,
        target_dir: Path,
        templates: ModuleType
    ): 
    
    sha_files = list(target_dir.rglob("SHA256SUMS.txt"))
    if not sha_files:
        raise FileNotFoundError(templates.ERROR_CHECK_SUM_FILE_MISSING)
    sha_file = sha_files[0]
    sha_root = sha_file.parent

    def compute_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    correct_checksum: List[str] = []
    wrong_checksum: List[str] = []
    missing_files: List[str] = []

    checksum_dict = {}
    with sha_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid format in SHA256SUMS.txt at line {line_number}: {line!r}"
                )

            expected_hash, relative_path_str = parts
            checksum_dict[relative_path_str] = expected_hash
    
    with filelist.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            relative_path = line.split(templates.MIMIC_CXR_URL)[1]
            expected_sha255_value = checksum_dict.get( relative_path, '' )
            if expected_sha255_value!='':
                validation_file_path = target_dir / relative_path
                if not validation_file_path.exists():
                    missing_files.append(str(relative_path))
                    continue
                sha255_value = compute_sha256(validation_file_path)
                if sha255_value == expected_sha255_value:
                    correct_checksum.append(relative_path)
                else:
                    wrong_checksum.append(relative_path)
            else:
                missing_files.append(relative_path)

    return {
        "correct checksum": correct_checksum,
        "wrong checksum": wrong_checksum,
        "missing files": missing_files,
    }




def find_files(
        root_dir: Path,
        extension: str
    ) -> List[Path]:

    if not extension.startswith("."):
        extension = f".{extension}"

    return [p.resolve() for p in root_dir.rglob(f"*{extension}") if p.is_file()]

def _extract_zip(file_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(file_path, "r") as zf:
        zf.extractall(target_dir)


def _extract_tar(file_path: Path, target_dir: Path) -> None:
    with tarfile.open(file_path, "r:*") as tf:
        tf.extractall(target_dir)


def _extract_gz(file_path: Path) -> Path:
    output_path = file_path.parent / file_path.stem
    with gzip.open(file_path, "rb") as f_in, open(output_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return output_path


def _get_base_name(file_path: Path) -> str:
    name = file_path.name
    for ext in [".tar.gz", ".tar.bz2", ".tar.xz"]:
        if name.endswith(ext):
            return name[:-len(ext)]
    return file_path.stem


def unzip_files(root_dir: Path, file_extension: str) -> None:
    file_list = find_files(root_dir=root_dir, extension=file_extension)

    for file_path in file_list:
        suffixes = file_path.suffixes
        base_name = _get_base_name(file_path)

        extract_dir = file_path.parent / base_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        if file_path.suffix == ".zip":
            _extract_zip(file_path, extract_dir)

        elif suffixes[-2:] in [[".tar", ".gz"], [".tar", ".bz2"], [".tar", ".xz"]]:
            _extract_tar(file_path, extract_dir)

        elif file_path.suffix == ".tar":
            _extract_tar(file_path, extract_dir)

        elif file_path.suffix == ".gz":
            _extract_gz(file_path)  # no directory, single file

        else:
            raise ValueError(f"Unsupported archive format: {file_path}")







