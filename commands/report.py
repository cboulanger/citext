import os, csv
import pandas
from configs import *
import pandas as pd
from .model_list import list_models, expand_wildcards
from statistics import mean, stdev

col_names = ["model", "ext_mean", "ext_min", "ext_max", "ext_stdev", "seg_mean", "seg_min", "seg_max", "seg_stdev"]

def get_csv_path(model_name: str, model_type: str, prefix: str = "") -> str:
    return os.path.join(config_dataset_dir(), model_name, prefix + model_type + ".csv")


def get_model_accuracy(model_name: str, model_type: str, prefix: str = "") -> pandas.DataFrame:
    csv_path = get_csv_path(model_name, model_type, prefix)
    if not os.path.exists(csv_path):
        raise ValueError(
            f"No {model_type} accuracy information for model '{model_name}' exists at {csv_path}. Please run evaluation first.")
    return pd.read_csv(csv_path, names=["file", "accuracy"])


def compute_accuracy_info(model_name: str, model_type: str, prefix: str = "") -> dict:
    df = get_model_accuracy(model_name, model_type, prefix)
    a = df["accuracy"]
    return {
        "mean": mean(a),
        "min": min(a),
        "max": max(a),
        "stdev": stdev(a)
    }


def compare_accuracy(model_names: list, prefix: str = "") -> pd.DataFrame:
    global col_names
    col_dict = {key: [] for key in col_names}
    for name in model_names:
        if name not in list_models():
            raise ValueError(f"Model {name} does not exist")
        col_dict["model"].append(name)
        for model_type in ["extraction", "segmentation"]:
            for (key, value) in compute_accuracy_info(name, model_type, prefix).items():
                col_dict[f"{model_type[0:3]}_{key}"].append(value)
    df = pd.DataFrame(col_dict)
    df.reindex(col_names)
    return df


def execute(model_names: list, prefix: str = "", output_file: str = None):
    global col_names
    if len(model_names) == 0:
        raise ValueError("No model name given")
    model_names = expand_wildcards(model_names)
    df = compare_accuracy(model_names, prefix)
    pd.set_option('expand_frame_repr', False)
    print(df[col_names])
    if output_file is not None:
        with open(output_file, "w") as file:
            df[col_names].to_csv(file)
        print(f"Accuracy data written to {output_file}")
