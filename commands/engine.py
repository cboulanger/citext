import os, sys
from io import BytesIO
from zipfile import ZipFile
import requests
from configs import *


def check_version(version):
    if version != get_version() and not os.path.exists(config_exparser_dir(version)):
        raise ValueError(f"EXparser version {version} hasn't been downloaded - run engine install {version} first.")


def engine_install(version):
    file_url = f"{config_url_git_repo()}/archive/refs/tags/v{version}.zip"
    print(f"Downloading engine from {file_url}")
    try:
        url = requests.get(file_url)
        zipfile = ZipFile(BytesIO(url.content))
        file_list = [zipfile.open(file_name) for file_name in zipfile.namelist() if
                     "/EXparser/" in file_name and file_name.endswith("py")]
        for file in file_list:
            file_path = os.path.join(config_tmp_dir(), file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as t:
                t.write(file.read())
                file.close()
    except Exception as err:
        raise err


def engine_list():
    engines = []
    prefix = os.path.basename(config_url_git_repo())
    for file_name in os.listdir(config_tmp_dir()):
        if os.path.isdir(os.path.join(config_tmp_dir(), file_name)) and file_name.startswith(prefix):
            engines.append(file_name[len(prefix) + 1:])
    engines.append(get_version())
    engines.sort()
    return engines


def exec_list():
    print("\n".join(engine_list()))


def engine_use(version):
    check_version(version)
    with open(config_exparser_version_file(), "w") as f:
        f.write(version)


def exec_use(version):
    engine_use(version)
    print(f"Now using version {version}")
