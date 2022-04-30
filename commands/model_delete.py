import os, sys, shutil
from configs import *
from commands.model_list import get_models_with_prefix


def delete_model_folders(model_name: str):
    """
    Deletes the model data and the training data of the given model
    :param model_name:
    :return:
    """
    model_dir_path = os.path.join(model_dir(), get_version(), model_name)
    if not os.path.isdir(model_dir_path):
        raise ValueError(f'Model "{model_name}" does not exist.')
    shutil.rmtree(model_dir_path, ignore_errors=True)
    dataset_dir_path = os.path.join(dataset_dir(), model_name)
    shutil.rmtree(dataset_dir_path, ignore_errors=True)


def execute(model_names, non_interactive=False):
    models = []
    for model_name_or_prefix in model_names:
        model_names_expanded = get_models_with_prefix(model_name_or_prefix[:-1]) if model_name_or_prefix.endswith(
            "*") else [model_name_or_prefix]
        for model_name in model_names_expanded:
            if model_name == "default":
                print("The default model cannot be deleted")
                sys.exit(1)
            models.append(model_name)

    if non_interactive == False:
        model_list = "', '".join(models[:-1]) + f"' and '{models[-1]}" if len(models) > 1 else models[0]
        print(f"This will delete model(s) '{model_list}'.")
        answer = input("Proceed? [y/n] ").lower()
        if answer != "y":
            sys.exit(0)

    for model_name in models:
        delete_model_folders(model_name)
