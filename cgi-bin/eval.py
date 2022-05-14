#!/usr/bin/env python3
import sys, os, cgi, traceback, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event, redirectPrintToEvent
from configs import *
from commands.split import split_model
from commands.model_list import list_models
from commands.model_delete import delete_model_folders
from commands.training import *
from commands.extraction import call_extraction
from evaluation import eval_extraction, eval_segmentation
from commands.segmentation import call_segmentation
from commands.report import compute_accuracy_info

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]
skip_splitting = 'skip_splitting' in params
skip_segmentation = 'skip_segmentation' in params
skip_extraction = 'skip_extraction' in params

title = f"Evaluating model '{model_name}'"
oldprint = redirectPrintToEvent(channel_id, title)

try:
    split_model_name = f"test_{model_name}"
    split_model_dir = os.path.join(config_model_dir(), get_version(), split_model_name)
    split_dataset_dir = os.path.join(config_dataset_dir(), split_model_name)

    # splitting
    if not skip_splitting:
        print("Splitting model...")

        # delete existing model data
        if split_model_name in list_models():
            delete_model_folders(split_model_name)

        # create split
        split_model(model_name, split_model_name)

        # create exparser workflow dirs
        for dirname in config_data_dirnames():
            os.makedirs(os.path.join(split_dataset_dir, dirname), exist_ok=True)

    # training

    if not skip_extraction:
        call_extraction_training(split_model_name)

    if not skip_segmentation:
        call_segmentation_training(split_model_name)

    call_completeness_training(split_model_name)

    # evaluation
    if not skip_extraction:
        # copy test layout files for exparser extraction
        test_lyt_dir = os.path.join(split_dataset_dir, DatasetDirs.TEST_LYT.value)
        for file_name in os.listdir(test_lyt_dir):
            try:
                shutil.copy(
                    os.path.join(test_lyt_dir, file_name),
                    os.path.join(split_dataset_dir, config_dirname_layouts(), file_name)
                )
            except PermissionError as err:
                # work around WSL problem
                sys.stderr.write(f"Warning: {str(err)}\n")

        # run extraction
        call_extraction(split_model_dir, split_dataset_dir)

        # evaluate extraction
        eval_extraction(
            gold_dir=os.path.join(split_dataset_dir, "TEST_REFS"),  # $TEST_REFS_DIR
            exparser_result_dir=os.path.join(split_dataset_dir, config_dirname_refs()),  # $EXPARSER_REFS_DIR
            output_dir=split_dataset_dir,
            output_filename_prefix="",
            add_logfile=False)

    if not skip_segmentation:
        # copy refs gold data to excite refs output dir
        excite_refs_path = os.path.join(split_dataset_dir, config_dirname_refs())
        test_refs_path = os.path.join(split_dataset_dir, DatasetDirs.TEST_REFS.value)
        for file_name in os.listdir(excite_refs_path):
            os.remove(os.path.join(excite_refs_path, file_name))
        for file_name in os.listdir(test_refs_path):
            try:
                shutil.copy(os.path.join(test_refs_path, file_name),
                            os.path.join(excite_refs_path, file_name))
            except PermissionError as err:
                # work around WSL problem
                sys.stderr.write(f"Warning: {str(err)}\n")

        # run segmentation
        call_segmentation(split_model_dir, split_dataset_dir)

        # eval segmentation
        eval_segmentation(
            gold_dir=os.path.join(split_dataset_dir, "TEST_SEG"),  # $TEST_SEG_DIR
            exparser_result_dir=os.path.join(split_dataset_dir, config_dirname_refs_seg()),  # $EXPARSER_SEG_DIR
            output_dir=split_dataset_dir,
            output_filename_prefix="",
            add_logfile=False)

    # output accuracy
    extr_accuracy = round(compute_accuracy_info(split_model_name, "extraction")['mean'], 3)
    seg_accuracy = round(compute_accuracy_info(split_model_name, "segmentation")['mean'], 3)
    response = f"{model_name}: Model evaluation results in the following accuracy values:"
    if not skip_extraction:
        response += f" extraction: {extr_accuracy}"
    if not skip_segmentation:
        response += f" segmentation: {seg_accuracy}"
    push_event(channel_id, "success", response)

except Exception as err:
    push_event(channel_id, "error", str(err))
    tb = traceback.format_exc()
    sys.stderr.write(tb)
    response = tb
finally:
    # abortThread.join()
    push_event(channel_id, "info", title+":")
    oldprint("Content-Type: text/plain\n")
    oldprint(response)
