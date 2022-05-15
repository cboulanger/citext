import sys, os, shutil
from configs import *
from commands.split import split_model
from commands.model_list import list_models
from commands.model_delete import delete_model_folders
from commands.training import *
from commands.extraction import call_extraction
from evaluation import eval_extraction, eval_segmentation
from commands.segmentation import call_segmentation
from commands.report import compute_accuracy_info

def run_full_eval_workflow(model_name,
                           skip_splitting=False,
                           skip_extraction=False,
                           skip_segmentation=False,
                           prefix="test_",
                           add_logfile=False):
    """
    Run splitting, training, and evaluation for a model
    :param model_name:str
    :param skip_splitting:bool
    :param skip_extraction:bool
    :param skip_segmentation:bool
    :param prefix:str the prefix for the split model
    :param add_logfile:bool
    :return:tuple extr_accuracy, seg_accuracy
    """

    split_model_name = f"{prefix}{model_name}"
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
            add_logfile=add_logfile)

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
            add_logfile=add_logfile)

    # output accuracy
    extr_accuracy = round(compute_accuracy_info(split_model_name, "extraction")['mean'], 3) if not skip_extraction else 0
    seg_accuracy = round(compute_accuracy_info(split_model_name, "segmentation")['mean'], 3) if not skip_segmentation else 0
    return extr_accuracy, seg_accuracy
