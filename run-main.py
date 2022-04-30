import importlib
import os.path
import shutil
import subprocess
import sys
import traceback
from lib.pogressbar import *
from lib.logger import *
from dotenv import load_dotenv
import argparse
from configs import *

from evaluation import compare_output_to_gold

load_dotenv()

dataset_dir = "EXparser/Dataset"
model_dir = "EXparser/Models"

# legacy commands, see below for new argparse implementations
class Commands(Enum):
    LAYOUT = "layout"
    EXPARSER = "exparser"
    SEGMENTATION = "segmentation"
    EXMATCHER = "exmatcher"
    TRAIN_EXTRACTION = "train_extraction"
    TRAIN_SEGMENTATION = "train_segmentation"
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

    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='Run exparser tools.')
    subcommands = parser.add_subparsers()

    model_parser = subcommands.add_parser("model", help="Tools to work with models")
    model_subcommands = model_parser.add_subparsers()

    # model create
    model_create_parser = model_subcommands.add_parser("create", help="Create a new model")
    model_create_parser.add_argument("model_name", type=str, help="The name of the model to be created.")
    model_create_parser.set_defaults(command="model_create")

    # model delete
    model_delete_parser = model_subcommands.add_parser("delete", help="Delete one or more models")
    model_delete_parser.add_argument("model_names",
                                    metavar="model", type=str, nargs="+",
                                    help="The name of the model to be deleted. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected for deletion")
    model_delete_parser.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    model_delete_parser.set_defaults(command="model_delete")

    # model list
    model_list_parser = model_subcommands.add_parser("list", help="List all available models")
    model_list_parser.set_defaults(command="model_list")

    # model merge
    model_merge_parser = model_subcommands.add_parser("merge", help="Merge one or more models into a new model")
    model_merge_parser.add_argument("target", type=str, help="The name of the model into which the other models will be merged. Will be created if it does not exist.")
    model_merge_parser.add_argument("models",
                                    metavar="model", type=str, nargs="+",
                                    help="The name of the model which will be merged into the target model. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected")
    model_merge_parser.add_argument("-O", "--omit-test-data", help="When copying training data, omit the documents used for testing in the given models", action="store_true")
    model_merge_parser.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    model_merge_parser.set_defaults(command="model_merge")

    # add legacy commands
    parsers = []
    for data in Commands:
        cmd = subcommands.add_parser(data.value, help=f"Run the {data.value} command")
        cmd.add_argument("args", nargs="+")
        cmd.set_defaults(command=data.value)
        parsers.append(cmd)

    # check if argparse implementation of command exists, import and run it
    try:
        args = parser.parse_args()
        if args.command is not None:
            command = importlib.import_module("commands." + args.command)
            kwargs = vars(args)
            del kwargs['command']
            command.execute(**kwargs)
            sys.exit(0)
    except ModuleNotFoundError as err:
        # it's a legacy command
        pass

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
            if len(sys.argv) < 4:
                raise RuntimeError("Three arguments are expected: gold folder, model output folder and mode: seg or extr")
            gold_folder = sys.argv[2]
            model_out_folder = sys.argv[3]
            mode = sys.argv[4]
            log_folder = sys.argv[5]
            compare_output_to_gold(gold_folder, model_out_folder, mode, log_folder)

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
