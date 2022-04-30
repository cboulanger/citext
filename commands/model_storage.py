import sys, os, tempfile, shutil
from webdav3.client import Client
from zipfile import ZipFile
from configs import *
from progress.bar import Bar

def get_progress_bar(task, max):
    progressbar = Bar(task, bar_prefix=' [', bar_suffix='] ', empty_fill='.',
                      suffix='%(index)d/%(max)d',
                      max=max)
    return progressbar

client = None
def get_client():
    global client
    if client is None:
        options = {
            'webdav_hostname': os.environ.get("EXCITE_WEBDAV_URL"),
            'webdav_login': os.environ.get("EXCITE_WEBDAV_USER"),
            'webdav_password': os.environ.get("EXCITE_WEBDAV_PASSWORD")
        }
        client = Client(options)
    return client


def call_upload_model():
    num_args = len(sys.argv)
    if num_args < 3:
        raise RuntimeError("Please provide a name for the model")
    model_name = sys.argv[2]
    package_name = sys.argv[3] if num_args > 3 else model_name
    kwargs = {}
    if num_args > 4:
        for i in range(4, num_args):
            kwargs[sys.argv[i]] = True
    from commands.model_storage import upload_model
    upload_model(model_name, package_name, **kwargs)


def call_download_model():
    if len(sys.argv) < 3:
        raise RuntimeError("Please provide a name for the model")
    model_name = sys.argv[2]
    package_name = sys.argv[3] if len(sys.argv) == 4 else model_name
    from commands.model_storage import download_model
    create_model_folders(model_name)
    download_model(model_name, package_name)


def get_package_dir():
    return os.path.join(os.environ.get("EXCITE_WEBDAV_MODEL_PATH"), get_version())


def get_package_path(package_name):
    return os.path.join(get_package_dir(), package_name + ".zip")


def create_version_dir():
    version_dir = os.path.join(get_package_dir(), get_version())
    client = get_client()
    if not client.check(version_dir):
        client.mkdir(version_dir)


def package_exists(package_name):
    client = get_client()
    package_path = get_package_path(package_name)
    return client.check(package_path)


def get_zip_path(model_name):
    return os.path.join(tempfile.gettempdir(), model_name + ".zip")


def upload_model(model_name, package_name, model=False, training=False, extraction=False, segmentation=False,
                 all=False, overwrite=False):
    """
    :param model_name: The name of the (local) model as used by the commands
    :param package_name: The name of the (remote) package, which can contain various parts of the model and training data
    :param model: If True, include model data
    :param training: If True, include training data
    :param extraction: If True, include extraction model or training data
    :param segmentation: If True, include segmentation model or training data
    :param overwrite: If true, existing remote package data will be overwritten
    :return:
    """
    if model_name is None:
        raise RuntimeError("No model name given.")
    if package_name is None:
        package_name = model_name
    if package_exists(package_name) and overwrite == False:
        raise RuntimeError(f'Package {package_name} exists. Use kwarg "overwrite" to update it.')
    directories = []
    if not (model or training) or not (extraction or segmentation or model) and not all:
        raise RuntimeError(
            'Not enough kwargs, need any of "model"/"training" and "extraction"/"segmentation", or "all"')
    if training or all:
        directories.append(os.path.join("EXparser", "Dataset", model_name))
    if model or all:
        directories.append(os.path.join("EXparser", "Models", get_version(), model_name))
    file_paths = []
    for directory in directories:
        if not os.path.isdir(directory):
            raise RuntimeError(f'Cannot upload model data: {directory} does not exist.')
        for root, directories, files in os.walk(directory):
            for file_name in files:
                if file_name.startswith("."):
                    continue
                file_path = os.path.join(root, file_name)
                if all or (model and not "kde_" in file_path) or \
                        (training and extraction and ("/LYT/" in file_path or "/LRT/" in file_path)) or \
                        (training and segmentation and "/SEG/" in file_path):
                    file_paths.append(file_path)
    bar = get_progress_bar("Compressing files", len(file_paths))
    zip_path = get_zip_path(model_name)
    with ZipFile(zip_path, 'w') as zip_file:
        for file_path in file_paths:
            bar.next()
            zip_file.write(file_path, file_path.replace(f'/{model_name}/', f'/{package_name}/'))
    bar.finish()
    # file_size = os.path.getsize(zip_path)
    bar = get_progress_bar(f"Uploading package", 100)
    client = get_client()
    create_version_dir()
    package_path = get_package_path(package_name)
    client.upload_file(remote_path=package_path,
                       local_path=zip_path,
                       progress=lambda current, total: bar.goto(int((current / total) * 100) + 1))
    bar.finish()
    os.remove(zip_path)


def download_model(model_name, package_name):
    if package_name is None:
        package_name = model_name
    client = get_client()
    if not package_exists(package_name):
        raise RuntimeError(f'Package "{package_name}" does not exist')
    # print(client.info(model_path))
    bar = get_progress_bar("Downloading package", 100)
    zip_path = get_zip_path(model_name)
    client.download_file(remote_path=get_package_path(package_name),
                         local_path=zip_path,
                         progress=lambda current, total: bar.goto(int((current / total) * 100)))
    bar.finish()
    print("Uncompressing files...")
    with ZipFile(zip_path, 'r') as zip_file:
        for name in zip_file.namelist():
            targetpath = name.replace(f'/{package_name}/', f'/{model_name}/')
            with zip_file.open(name) as source, open(targetpath, "wb") as target:
                shutil.copyfileobj(source, target)
    os.remove(zip_path)


def list_packages():
    client = get_client()
    return [name.strip(".zip") for name in client.list(get_package_dir()) if ".zip" in name]


def delete_package(package_name):
    client = get_client()
    if not package_exists(package_name):
        raise RuntimeError(f'Package "{package_name}" does not exist')
    client.clean(get_package_path(package_name))
