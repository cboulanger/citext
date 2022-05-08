import os, sys, re
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

def import_annotations(model_name, parent_dir):
    for subdir_name in ["LRT", "SEG"]:
        source_path = os.path.join(parent_dir, subdir_name)
        target_path = os.path.join(dataset_dir(), model_name, subdir_name)
        if os.path.exists(source_path):
            for file_name in os.listdir(source_path):
                shutil.copy(os.path.join(source_path, file_name), target_path)

def generate_lyt_from_lrt_if_missing(model_name: str):
    lrt_dir = os.path.join(dataset_dir(), model_name, "LRT")
    lyt_dir = os.path.join(dataset_dir(), model_name, "LYT")
    for lrt_file_name in os.listdir(lrt_dir):
        lrt_file_path = os.path.join(lrt_dir, lrt_file_name)
        lyt_file_path = os.path.join(lyt_dir, lrt_file_name)
        if not os.path.exists(lyt_file_path):
            with open(lrt_file_path) as s, open(lyt_file_path, "w") as t:
                t.write(re.sub("<\/?(ref|oth)>", "", s.read()))

def execute(model_name: str):
    try:
        create_model_folders(model_name)
        sys.stdout.write("Please put the training data to: " + os.path.join(dataset_dir(), model_name)
                     + " and then run the training commands.\n")
    except ValueError as err:
        print(str(err))
