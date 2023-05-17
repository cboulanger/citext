import os, sys, re
import shutil
from configs import *

class Dataset:
    @staticmethod
    def create(dataset_name: str, include : list = None):
        if type(include) is list:
            for ds in include:
                if ds not in Dataset.list():
                    raise RuntimeError(f"Included dataset {ds} does not exist")
        model_dir_path = os.path.join(config_model_dir(), dataset_name)
        if os.path.isdir(model_dir_path):
            raise ValueError(f"Model '{dataset_name}' already exists.")
        os.makedirs(model_dir_path, exist_ok=True)
        dataset_dir_path = os.path.join(config_dataset_dir(), dataset_name)
        if not os.path.isdir(dataset_dir_path):
            os.makedirs(dataset_dir_path, exist_ok=True)
        for subdir in ['finder','parser']:
            subdir_path = os.path.join(config_dataset_dir(), dataset_name, 'anystyle', subdir)
            os.makedirs(subdir_path, exist_ok=True)
            with open(os.path.join(subdir_path, '_merge-datasets'), mode="w") as f:
                if type(include) is list:
                    f.write("\n".join(include))

    @staticmethod
    def delete(dataset_name: str):
        """
        Deletes the model data and the training data of the given model
        :param dataset_name:
        :return:
        """
        model_dir_path = os.path.join(config_model_dir(), dataset_name)
        if not os.path.isdir(model_dir_path):
            raise ValueError(f'Model "{dataset_name}" does not exist.')
        shutil.rmtree(model_dir_path, ignore_errors=True)
        dataset_dir_path = os.path.join(config_dataset_dir(), dataset_name)
        shutil.rmtree(dataset_dir_path, ignore_errors=True)

    @staticmethod
    def find_by_prefix(prefix:str):
        """
        Given a prefix, return all model names that match the prefix
        :param prefix:str
        :return:list
        """
        return [ m for m in Dataset.list() if m[:len(prefix)] == prefix]

    @staticmethod
    def expand_wildcards(dataset_names):
        datasets = []
        for ds in dataset_names:
            if ds.endswith("*"):
                datasets.extend(Dataset.find_by_prefix(ds[:-1]))
            else:
                datasets.append(ds)
        return datasets

    @staticmethod
    def list():
        datasets = []
        curr_model_dir = os.path.join(config_model_dir())
        for file in os.listdir(curr_model_dir):
            if os.path.isdir(os.path.join(curr_model_dir, file)):
                datasets.append(file)
        datasets.sort()
        return datasets

    @staticmethod
    def split(dataset_name, test_dataset_name):
        raise "Not functional, must be reimplemented"
        if dataset_name not in Dataset.list():
            raise ValueError(f"Model {dataset_name} does not exist")
        if test_dataset_name in Dataset.list():
            raise ValueError(f"Test model {dataset_name} exists, delete first.")
    
        def dataset_subdir(subdir):
            return os.path.join(config_dataset_dir(), dataset_name, subdir)
        def test_dataset_subdir(subdir):
            return os.path.join(config_dataset_dir(), test_dataset_name, subdir)
    
        # make sure we have enough data for training and evaluation
        num_lrt_docs = len(os.listdir(dataset_subdir("LRT")))
        num_seg_docs = len(os.listdir(dataset_subdir("SEG")))
        if num_lrt_docs < 20 or num_seg_docs < 20:
            raise ValueError(f"Model {dataset_name} must at least have 20 training documents in LRT and SEG")
    
        # create model dirs for training and test data
        create_model_folders(test_dataset_name)
    
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
