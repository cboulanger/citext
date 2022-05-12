import sys, os, tempfile, shutil
from webdav3.client import Client
from zipfile import ZipFile
from configs import *
from progress.bar import Bar
from .model_create import create_model_folders
from .model_list import list_models
from lib.pogressbar import get_progress_bar

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


def get_package_dir():
    return os.path.join(os.environ.get("EXCITE_WEBDAV_MODEL_PATH"), get_version())


def get_package_path(package_name):
    return os.path.join(get_package_dir(), package_name + ".zip")


def create_version_dir():
    version_dir = get_package_dir()
    client = get_client()
    if not client.check(version_dir):
        client.mkdir(version_dir)


def package_exists(package_name):
    client = get_client()
    package_path = get_package_path(package_name)
    return client.check(package_path)


def get_zip_path(model_name):
    return os.path.join(tempfile.gettempdir(), model_name + ".zip")


def list_packages():
    client = get_client()
    package_list = [name.strip(".zip") for name in client.list(get_package_dir()) if ".zip" in name]
    package_list.sort()
    return package_list


def upload_package(package_name, model_name, trained_model=False, training_data=None, overwrite=False):
    """
    :param package_name: The name of the (remote) package, which can contain various parts of the model and training data
    :param model_name: The name of the (local) model as used by the commands
    :param trained_model: If True, include trained model data
    :param training_data: If given, the type of training data to include: "extractión", "segmentation" or "all"
    :param overwrite: If true, existing remote package data will be overwritten
    :return:
    """
    if model_name is None:
        raise RuntimeError("No model name given.")
    if package_name is None:
        raise RuntimeError("No package name given.")
    if package_exists(package_name) and overwrite == False:
        raise RuntimeError(f'Package {package_name} exists. Use kwarg "overwrite" to update it.')
    directories = []
    if not (trained_model or training_data):
        raise RuntimeError(
            'One of --trained-model or --training-data is required')
    if training_data:
        directories.append(os.path.join(config_dataset_dir(), model_name))
    if trained_model:
        directories.append(os.path.join(config_model_dir(), get_version(), model_name))
    file_paths = []
    for directory in directories:
        if not os.path.isdir(directory):
            raise RuntimeError(f'Cannot upload model data: {directory} does not exist.')
        for root, directories, files in os.walk(directory):
            for file_name in files:
                file_name = str(file_name)
                root = str(root)
                if file_name.startswith("."):
                    continue
                file_path = os.path.join(root, file_name)
                if (trained_model and not "kde_" in file_path) or \
                        (training_data in ["extraction", "all"] and ("/LYT/" in file_path or "/LRT/" in file_path)) or \
                        (training_data in ["segmentation", "all"] and "/SEG/" in file_path):
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


def download_package(package_name, model_name):
    if model_name not in list_models():
        raise ValueError(f"Model '{model_name}' does not exist")
    client = get_client()
    if not package_exists(package_name):
        raise RuntimeError(f'Package "{package_name}" does not exist')
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
            os.makedirs(os.path.dirname(targetpath), exist_ok=True)
            with zip_file.open(name) as source, open(targetpath, "wb") as target:
                shutil.copyfileobj(source, target)
    os.remove(zip_path)


def delete_package(package_name):
    client = get_client()
    if not package_exists(package_name):
        raise RuntimeError(f'Package "{package_name}" does not exist')
    client.clean(get_package_path(package_name))

def delete_packages(package_names, non_interactive=False):
    packages_to_delete = []
    remote_packages = list_packages()
    for pn in package_names:
        if pn.endswith("*"):
            pn = pn[:-1]
            for rp in remote_packages:
                if rp[:len(pn)] == pn:
                    packages_to_delete.append(rp)
        else:
            packages_to_delete.append(pn)

    if non_interactive == False:
        pkg_list = "', '".join(packages_to_delete[:-1]) + f"' and '{packages_to_delete[-1]}" if len(packages_to_delete) > 1 else packages_to_delete[0]
        print(f"This will delete model(s) '{pkg_list}'.")
        answer = input("Proceed? [y/n] ").lower()
        if answer != "y":
            sys.exit(0)

    for package_name in packages_to_delete:
        delete_package(package_name)

    return packages_to_delete


def exec_list():
    print("\n".join(list_packages()))


def exec_publish(package_name, **kwargs):
    # this is a shortcut to publish several models at once
    if package_name.endswith("*"):
        if kwargs['model_name']:
            raise ValueError("If package name contains a wildcard, the model name must not be specified.")
        for model_name in list_models():
            if package_name[:-1] == model_name[:len(package_name[:-1])]:
                exec_publish(model_name, **kwargs)
        return
    if not kwargs['model_name']:
        kwargs['model_name'] = package_name

    upload_package(package_name, **kwargs)
    print(f"Package '{package_name}' successfully published")


def exec_import(package_name, model_name=None):
    if not model_name:
        model_name = package_name
    if model_name not in list_models():
        create_model_folders(model_name)
    download_package(package_name, model_name)
    print(f"Package '{package_name}' successfully imported into model '{model_name}'")


def exec_delete(package_names, non_interactive=False):
    pkgs = delete_packages(package_names, non_interactive)
    print(f"{len(pkgs)} package(s) deleted")
