import sys, os, shutil
from configs import *

def model_merge(target: str, models:list=[]):
    target_dir = os.path.join("EXparser", "Dataset", target)
    training_data_dirs = ["LYT", "LRT", "SEG"]

    for curr_dir in os.listdir(source_dir):
        if curr_dir[0:len(dir_prefix)] == dir_prefix:
            for subdir in training_data_dirs:
                subdir_path = os.path.join(source_dir, curr_dir, subdir)
                for curr_file in os.listdir(subdir_path):
                    if curr_file.startswith("."): continue
                    file_path = os.path.join(subdir_path, curr_file)
                    target_path = os.path.join(target_dir, subdir)
                    print(f'Copying {os.path.join(curr_dir, subdir, curr_file)}')
                    shutil.copy(file_path, target_path)

def execute(target: str, models:list=[]):
    """
    Merge one or more models training data into another one. Model will be created if it does not exist
    :param target:str
    :param models:list List of model names. If a model name ends with "*", it is used as
    a prefix and all models starting with this prefix are selected
    :return:
    """

    model_list = "', '".join(models[:-1]) + f"' and '{models[-1]}" if len(models) > 1 else models[0]
    print(f"This will add training data in models '{model_list}' to the '{target}' model training data.")
    answer = input("Proceed? [y/n] ").lower()
    if answer != "y":
        sys.exit(0)

    sys.exit(0)
