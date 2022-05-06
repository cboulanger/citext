import os
from configs import *

def call_extraction_training(model_name: str):
    from EXparser.Feature_Extraction import extract_features
    from EXparser.Txt2Vec import text_to_vec
    from EXparser.Training_Ext import train_extraction
    extract_features(os.path.join(dataset_dir(), model_name))
    text_to_vec(os.path.join(dataset_dir(), model_name))
    train_extraction(os.path.join(dataset_dir(), model_name),
                     os.path.join(model_dir(), get_version(), model_name))



def call_segmentation_training(model_name: str):
    from EXparser.Training_Seg import train_segmentation
    from EXparser.Feature_Extraction import extract_features
    from EXparser.Txt2Vec import text_to_vec
    extract_features(os.path.join(dataset_dir(), model_name))
    text_to_vec(os.path.join(dataset_dir(), model_name))
    train_segmentation(os.path.join(dataset_dir(), model_name),
                       os.path.join(model_dir(), get_version(), model_name))
