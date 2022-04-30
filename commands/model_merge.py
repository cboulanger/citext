import sys, os, shutil
from configs import *
from commands.model_list import get_models_with_prefix, list_models
from commands.model_create import create_model_folders


def merge_models(target_model: str, source_models: list = [], omit_test_data=False):
    """
    Merge one or more models training data into another one.
    :param target_model:str
    :param source_models:list
    :return:
    """
    target_dir = os.path.join("EXparser", "Dataset", target_model)
    if not os.path.exists(target_dir):
        raise ValueError(f"Model '{target_model}' does not exist")

    training_data_dirs = ["LYT", "LRT", "SEG"]

    for source_model in source_models:
        source_dir = os.path.join("EXparser", "Dataset", source_model)
        if not os.path.exists(source_dir):
            raise ValueError(f"Model '{source_model}' does not exist")
        for traindir_name in training_data_dirs:
            traindir_path = os.path.join(source_dir, traindir_name)
            testdir_path = os.path.join(source_dir, "TEST_LYT")
            for trainfile_name in os.listdir(traindir_path):
                if trainfile_name.startswith("."): continue
                # do not include test data into training data if --omit-test-data flag is set
                testfile_path = os.path.join(testdir_path, trainfile_name.replace(".xml", ".csv"))
                if omit_test_data and os.path.exists(testfile_path): continue
                trainfile_path = os.path.join(traindir_path, trainfile_name)
                target_path = os.path.join(target_dir, traindir_name)
                shutil.copy(trainfile_path, target_path)


def execute(target: str, models: list = [], omit_test_data=False, non_interactive=False):
    """
    :param target:str
    :param mdls:list List of model names. If a model name ends with "*", it is used as
    a prefix and all models starting with this prefix are selected
    :return:
    """

    if not target in list_models():
        create_model_folders(target)

    # expand wildcards if any
    mdls = []
    for model in models:
        if model.endswith("*"):
            mdls.extend(get_models_with_prefix(model[:-1]))
        else:
            mdls.append(model)
    if len(mdls) == 0:
        print("No models with these names exist.")
        sys.exit(1)

    if non_interactive == False:
        model_list = "', '".join(mdls[:-1]) + f"' and '{mdls[-1]}" if len(mdls) > 1 else mdls[0]
        print(f"This will add training data in models '{model_list}' to the '{target}' model training data.")
        answer = input("Proceed? [y/n] ").lower()
        if answer != "y":
            sys.exit(0)

    merge_models(target, mdls, omit_test_data)
