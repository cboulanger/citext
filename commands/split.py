import sys,os, shutil, re, random
from .model_list import list_models
from .model_create import create_model_folders
from configs import config_dataset_dir

def split_model(model_name, test_model_name):
    if model_name not in list_models():
        raise ValueError(f"Model {model_name} does not exist")
    if test_model_name in list_models():
        raise ValueError(f"Test model {model_name} exists, delete first.")

    def dataset_subdir(subdir):
        return os.path.join(config_dataset_dir(), model_name, subdir)
    def test_dataset_subdir(subdir):
        return os.path.join(config_dataset_dir(), test_model_name, subdir)

    # make sure we have enough data for training and evaluation
    num_lrt_docs = len(os.listdir(dataset_subdir("LRT")))
    num_seg_docs = len(os.listdir(dataset_subdir("SEG")))
    if num_lrt_docs < 20 or num_seg_docs < 20:
        raise ValueError(f"Model {model_name} must at least have 20 training documents in LRT and SEG")

    # create model dirs for training and test data
    create_model_folders(test_model_name)

    # split LRT files into testing and training docs
    lrt_files = os.listdir(dataset_subdir("LRT"))
    num_testing = max(int(num_lrt_docs / 20), 5)
    shuffled_files = random.sample(lrt_files, num_lrt_docs)
    test_files = shuffled_files[:num_testing]

    # copy files to testing or training
    for lrt_file_name in lrt_files:
        # file names
        lrt_file_name = str(lrt_file_name)
        seg_file_name = lrt_file_name.replace(".csv", ".xml")
        # path to gold data in original model
        lrt_orig_path = os.path.join(dataset_subdir("LRT"), lrt_file_name)
        lyt_orig_path = os.path.join(dataset_subdir("LYT"), lrt_file_name)
        seg_orig_path = os.path.join(dataset_subdir("SEG"), seg_file_name)
        # evaluation model, path to training files
        seg_train_path = os.path.join(test_dataset_subdir("SEG"), seg_file_name)
        lyt_train_path = os.path.join(test_dataset_subdir("LYT"), lrt_file_name)
        lrt_train_path = os.path.join(test_dataset_subdir("LRT"), lrt_file_name)
        # evaluation model, path to testing files
        seg_test_path = os.path.join(test_dataset_subdir("TEST_SEG"), seg_file_name)
        refs_test_path = os.path.join(test_dataset_subdir("TEST_REFS"), lrt_file_name)
        lyt_test_path = os.path.join(test_dataset_subdir("TEST_LYT"), lrt_file_name)

        # copy LYT training data or generate it
        if os.path.exists(lyt_orig_path):
            try:
                shutil.copy(lyt_orig_path, lyt_train_path)
            except PermissionError as err:
                # work around WSL problem
                sys.stderr.write(f"Warning: {str(err)}\n")
        else:
            with open(lrt_orig_path) as s, open(lyt_train_path, "w") as t:
                t.write(re.sub("<\/?(ref|oth)>", "", s.read()))

        # test data
        if lrt_file_name in test_files:
            # move LYT data from training to testing
            shutil.move(lyt_train_path, lyt_test_path)
            if os.path.exists(seg_orig_path):
                # copy SEG gold to test data
                try:
                    shutil.copy(seg_orig_path, seg_test_path)
                except PermissionError as err:
                    # work around WSL problem
                    sys.stderr.write(f"Warning: {str(err)}\n")
                # generate REFS test data from SEG gold to evaluate extraction output and to serve as segmentation input
                with open(seg_orig_path) as s, open(refs_test_path, "w") as t:
                    content = s.read()
                    # remove tags and empty lines
                    content = re.sub("<[^>]*>", "", content)
                    content = "\n".join(filter(str.strip, content.splitlines()))
                    t.write(content)
            else:
                sys.stderr.write(f"Segmentation gold file '{seg_orig_path}' is missing for evaluation")

        # training data
        else:
            # copy LRT and SEG
            try:
                shutil.copy(lrt_orig_path, lrt_train_path)
            except PermissionError as err:
                # work around WSL problem
                sys.stderr.write(f"Warning: {str(err)}\n")
            if os.path.exists(seg_orig_path):
                try:
                    shutil.copy(seg_orig_path, seg_train_path)
                except PermissionError as err:
                    # work around WSL problem
                    sys.stderr.write(f"Warning: {str(err)}\n")
            else:
                sys.stderr.write(f"Segmentation gold file {seg_orig_path} is missing for training")
