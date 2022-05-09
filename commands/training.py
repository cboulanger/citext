import os
from configs import *
from commands.model_create import generate_lyt_from_lrt_if_missing
from EXparser.Txt2Vec import text_to_vec
from EXparser.Feature_Extraction import extract_features
from EXparser.Training_Ext import train_extraction
from EXparser.Training_Seg import train_segmentation

def call_extraction_training(model_name: str):
    generate_lyt_from_lrt_if_missing(model_name)
    extract_features(os.path.join(config_dataset_dir(), model_name))
    text_to_vec(os.path.join(config_dataset_dir(), model_name))
    train_extraction(os.path.join(config_dataset_dir(), model_name),
                     os.path.join(config_model_dir(), get_version(), model_name))

def call_segmentation_training(model_name: str):
    extract_features(os.path.join(config_dataset_dir(), model_name))
    text_to_vec(os.path.join(config_dataset_dir(), model_name))
    train_segmentation(os.path.join(config_dataset_dir(), model_name),
                       os.path.join(config_model_dir(), get_version(), model_name))
