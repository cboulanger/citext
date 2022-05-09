from evaluation import eval_extraction, eval_segmentation
import os, sys
from configs import *
from datetime import datetime

def execute(model_name,
            extraction=False,
            segmentation=False,
            exparser_result_dir:str=None,
            gold_dir:str=None,
            add_logfile=False,
            output_dir:str=None,
            output_filename_prefix:str=None):

    if extraction == False and segmentation == False:
        print("No evaluation mode given, add --extraction/-x or --segmentation/-s flag(s)")
        sys.exit(1)

    dataset_path = os.path.join(config_dataset_dir(), model_name)
    if output_filename_prefix is None:
        output_filename_prefix = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + "_"

    if extraction:
        eval_extraction(
            gold_dir=gold_dir,
            exparser_result_dir=exparser_result_dir,
            output_dir= output_dir or dataset_path,
            output_filename_prefix=output_filename_prefix,
            add_logfile=add_logfile)

    if segmentation:
        eval_segmentation(
            gold_dir=gold_dir,
            exparser_result_dir=exparser_result_dir,
            output_dir= output_dir or dataset_path,
            output_filename_prefix=output_filename_prefix,
            add_logfile=add_logfile)
