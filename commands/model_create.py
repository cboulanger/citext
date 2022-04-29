import os, sys
import shutil
from configs import *

def copy_kde_files(model_name):
    # todo: get rid of the copying if all models are trainable
    path = os.path.join(model_dir(), get_version(), model_name)
    default_path = os.path.join(model_dir(), get_version(), "default")
    src_files = os.listdir(default_path)
    for file_name in src_files:
        full_file_name = os.path.join(default_path, file_name)
        if os.path.isfile(full_file_name) and "kde_" in file_name:
            shutil.copy(full_file_name, path)

def create_model_folders(model_name: str):
    model_dir_path = os.path.join(model_dir(), get_version(), model_name)
    if os.path.isdir(model_dir_path):
        raise ValueError(f"Model '{model_name}' already exists.")
    os.mkdir(model_dir_path)
    copy_kde_files(model_name)
    dataset_dir_path = os.path.join(dataset_dir(), model_name)
    if not os.path.isdir(dataset_dir_path):
        os.mkdir(dataset_dir_path)
    for subdir in DatasetDirs:
        subdir_path = os.path.join(dataset_dir(), model_name, subdir.value)
        if not os.path.isdir(subdir_path):
            os.mkdir(subdir_path)

def execute(model_name: str):
    try:
        create_model_folders(model_name)
        sys.stdout.write("Please put the training data to: " + os.path.join(dataset_dir(), model_name)
                     + " and then run the training commands.\n")
    except ValueError as err:
        print(str(err))
