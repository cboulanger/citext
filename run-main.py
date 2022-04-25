import os.path
import shutil
import subprocess
import sys
import traceback
from lib.pogressbar import *
from lib.logger import *
from dotenv import load_dotenv

from evaluation import compare_output_to_gold

load_dotenv()

dataset_dir = "EXparser/Dataset"
model_dir = "EXparser/Models"


class Commands(Enum):
    LAYOUT = "layout"
    EXPARSER = "exparser"
    SEGMENTATION = "segmentation"
    EXMATCHER = "exmatcher"
    TRAIN_EXTRACTION = "train_extraction"
    TRAIN_SEGMENTATION = "train_segmentation"
    CREATE_MODEL = "create_model"
    DELETE_MODEL = "delete_model"
    LIST_MODELS = "list_models"
    START_SERVER = "start_server"
    UPLOAD_MODEL = "upload_model"
    DOWNLOAD_MODEL = "download_model"
    LIST_PACKAGES = "list_packages"
    DELETE_PACKAGE = "delete_package"
    EVALUATE = "eval"


def run_command(command):
    log(command)
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                            shell=True)
    while True:
        return_code = proc.poll()
        if return_code is not None:
            break
        line = str(proc.stdout.readline()).strip()
        if line != "":
            progress_print(line)
    progress_disable()
    # subprocess returned with error
    if return_code != 0:
        lines = [line.strip('\n') for line in proc.stderr.readlines() if line.strip('\n')]
        err_msg = '\n'.join(lines)
        raise RuntimeError(err_msg)


def call_run_layout_extractor():
    os.chdir(config_url_venu())
    command = 'java -jar cermine.layout.extractor-0.0.1-jar-with-dependencies.jar '
    command += config_url_pdfs() + ' '
    command += config_url_Layouts() + ' '
    command += '90000000'
    run_command(command)


def call_run_exmatcher():
    run_command('python3.6 run-crossref.py')


def call_run_exparser(model_name=None):
    from commands.run_exparser import call_Exparser
    call_Exparser(os.path.join(model_dir, get_version(), model_name))


def call_segmentation(model_name=None, input_dir=None):
    from commands.run_segmentation import call_Exparser_segmentation
    call_Exparser_segmentation(os.path.join(model_dir, get_version(), model_name), input_dir)


def call_extraction_training(model_name: str):
    from EXparser.Feature_Extraction import extract_features
    from EXparser.Txt2Vec import text_to_vec
    from EXparser.Training_Ext import train_extraction
    progress_enable()
    extract_features(os.path.join(dataset_dir, model_name))
    text_to_vec(os.path.join(dataset_dir, model_name))
    train_extraction(os.path.join(dataset_dir, model_name),
                     os.path.join(model_dir, get_version(), model_name))
    progress_disable()


def call_segmentation_training(model_name: str):
    from EXparser.Training_Seg import train_segmentation
    from EXparser.Feature_Extraction import extract_features
    from EXparser.Txt2Vec import text_to_vec
    progress_enable()
    extract_features(os.path.join(dataset_dir, model_name))
    text_to_vec(os.path.join(dataset_dir, model_name))
    train_segmentation(os.path.join(dataset_dir, model_name),
                       os.path.join(model_dir, get_version(), model_name))
    progress_disable()


def copy_kde_files(model_name):
    # todo: get rid of the copying if all models are trainable
    path = os.path.join(model_dir, get_version(), model_name)
    default_path = os.path.join(model_dir, get_version(), "default")
    src_files = os.listdir(default_path)
    for file_name in src_files:
        full_file_name = os.path.join(default_path, file_name)
        if os.path.isfile(full_file_name) and "kde_" in file_name:
            shutil.copy(full_file_name, path)


def create_model_folders(model_name: str):
    model_dir_path = os.path.join(model_dir, get_version(), model_name)
    if not os.path.isdir(model_dir_path):
        os.mkdir(model_dir_path)
    copy_kde_files(model_name)
    dataset_dir_path = os.path.join(dataset_dir, model_name)
    if not os.path.isdir(dataset_dir_path):
        os.mkdir(dataset_dir_path)
    for subdir in DatasetDirs:
        subdir_path = os.path.join(dataset_dir, model_name, subdir.value)
        if not os.path.isdir(subdir_path):
            os.mkdir(subdir_path)


def list_models():
    models = []
    curr_model_dir = os.path.join(model_dir, get_version())
    for file in os.listdir(curr_model_dir):
        if os.path.isdir(os.path.join(curr_model_dir, file)):
            models.append(file)
    return models


def delete_model_folders(model_name):
    model_dir_path = os.path.join(model_dir, get_version(), model_name)
    if not os.path.isdir(model_dir_path):
        raise RuntimeError(f'Model "{model_name}" does not exist.')
    shutil.rmtree(model_dir_path, ignore_errors=True)
    dataset_dir_path = os.path.join(dataset_dir, model_name)
    shutil.rmtree(dataset_dir_path, ignore_errors=True)


def call_start_server(port):
    # todo: make server multi-threaded: https://stackoverflow.com/a/46224191
    from http.server import HTTPServer, CGIHTTPRequestHandler, test
    test(CGIHTTPRequestHandler, HTTPServer, port=port)


def call_upload_model():
    num_args = len(sys.argv)
    if num_args < 3:
        raise RuntimeError("Please provide a name for the model")
    model_name = sys.argv[2]
    package_name = sys.argv[3] if num_args > 3 else model_name
    kwargs = {}
    if num_args > 4:
        for i in range(4, num_args):
            kwargs[sys.argv[i]] = True
    from commands.model_storage import upload_model
    upload_model(model_name, package_name, **kwargs)


def call_download_model():
    if len(sys.argv) < 3:
        raise RuntimeError("Please provide a name for the model")
    model_name = sys.argv[2]
    package_name = sys.argv[3] if len(sys.argv) == 4 else model_name
    from commands.model_storage import download_model
    create_model_folders(model_name)
    download_model(model_name, package_name)


if __name__ == "__main__":
    func_name = ''
    if len(sys.argv) > 1:
        func_name = sys.argv[1]
    try:
        if func_name == Commands.LAYOUT.value:
            call_run_layout_extractor()

        elif func_name == Commands.EXPARSER.value:
            if len(sys.argv) == 3:
                call_run_exparser(sys.argv[2])
            else:
                call_run_exparser()

        elif func_name == Commands.SEGMENTATION.value:
            if len(sys.argv) == 3:
                call_segmentation(sys.argv[2])
            elif len(sys.argv) == 4:
                call_segmentation(sys.argv[2], sys.argv[3])
            else:
                call_segmentation()

        elif func_name == Commands.EXMATCHER.value:
            call_run_exmatcher()

        elif func_name == Commands.TRAIN_EXTRACTION.value:
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            call_extraction_training(sys.argv[2])

        elif func_name == Commands.TRAIN_SEGMENTATION.value:
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            call_segmentation_training(sys.argv[2])

        elif func_name == Commands.CREATE_MODEL.value:
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            create_model_folders(sys.argv[2])
            sys.stdout.write("Please put the training data to: " + os.path.join(dataset_dir, model_name)
                             + " and then run the training commands.\n")

        elif func_name == Commands.DELETE_MODEL.value:
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            model_name = sys.argv[2]
            if model_name == "default":
                raise RuntimeError("Default model cannot be deleted")
            delete_model_folders(model_name)

        elif func_name == Commands.LIST_MODELS.value:
            print("\n".join(list_models()))

        elif func_name == Commands.START_SERVER.value:
            port = 8000
            if len(sys.argv) == 3:
                port = sys.argv[2]
            call_start_server(port)

        elif func_name == Commands.UPLOAD_MODEL.value:
            call_upload_model()

        elif func_name == Commands.DOWNLOAD_MODEL.value:
            call_download_model()

        elif func_name == Commands.LIST_PACKAGES.value:
            from commands.model_storage import list_packages
            print("\n".join(list_packages()))

        elif func_name == Commands.DELETE_PACKAGE.value:
            if len(sys.argv) < 3:
                raise RuntimeError("No package name given")
            package_name = sys.argv[2]
            from commands.model_storage import delete_package
            delete_package(package_name)

        elif func_name == Commands.EVALUATE.value:
            if len(sys.argv) < 2:
                raise RuntimeError("Three arguments are expected: gold folder, model output folder and mode: seg or extr")
            gold_folder = sys.argv[2]
            model_out_folder = sys.argv[3]
            mode = sys.argv[4]
            compare_output_to_gold(gold_folder, model_out_folder, mode)
        else:
            raise RuntimeError("Wrong input command: '" + func_name + "'; valid commands are: " +
                               ", ".join([c.value for c in Commands]) + "\n")
    except KeyboardInterrupt:
        sys.stderr.write("\nAborted\n")
        log("\nAborted")
        sys.exit(1)
    except:
        sys.stderr.write(traceback.format_exc())
        log(traceback.format_exc())
        sys.exit(1)
    finally:
        log('\n' + ('*' * 50) + '\n')
