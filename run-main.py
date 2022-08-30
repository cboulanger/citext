import importlib
import os.path
import shutil
import subprocess
import sys
import traceback
from lib.logger import *
#from dotenv import load_dotenv
import argparse
from configs import *

#load_dotenv()

if __name__ == "__main__":

    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='Run exparser tools.', prog="")
    subcommands = parser.add_subparsers()

    # model
    model_parser = subcommands.add_parser("model", help="Tools to work with models")
    model_subcommands = model_parser.add_subparsers()

    # model create
    p = model_subcommands.add_parser("create", help="Create a new model")
    p.add_argument("model_name", type=str, help="The name of the model to be created.")
    p.set_defaults(command="model_create")

    # model delete
    p = model_subcommands.add_parser("delete", help="Delete one or more models")
    p.add_argument("model_names",
                   metavar="model", type=str, nargs="+",
                   help="The name of the model to be deleted. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected for deletion")
    p.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    p.set_defaults(command="model_delete")

    # model list
    p = model_subcommands.add_parser("list", help="List all available models")
    p.set_defaults(command="model_list")

    # model merge
    p = model_subcommands.add_parser("merge", help="Merge one or more models into a new model")
    p.add_argument("target", type=str,
                   help="The name of the model into which the other models will be merged. Will be created if it does not exist.")
    p.add_argument("models",
                   metavar="model", type=str, nargs="+",
                   help="The name of the model which will be merged into the target model. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected")
    p.add_argument("--omit-test-data", "-O",
                   help="When copying training data, omit the documents used for testing in the given models",
                   action="store_true")
    p.add_argument("--non-interactive", "-I", action="store_true", help="Do not ask for confirmation")
    p.set_defaults(command="model_merge")

    # match
    match_parser = subcommands.add_parser("match", help="Commands to match the extracted references against databases")
    match_subcommands = match_parser.add_subparsers()

    # match crossref
    p = match_subcommands.add_parser("crossref", help="Match references using the CrossRef API")
    p.add_argument("--input-base-dir", "-d", type=str, help="The parent directory of the workflow folders",
                   default=None)
    p.set_defaults(command="match_crossref")

    # package
    pkg_parser = subcommands.add_parser("package",
                                        help="Commands to store model and training data as a package in a repository and download it from there.")
    pkg_subcommands = pkg_parser.add_subparsers()

    # package list
    p = pkg_subcommands.add_parser("list", help="List all available data packages")
    p.set_defaults(command="package", func_name="exec_list")

    # package publish
    p = pkg_subcommands.add_parser("publish", help="Publish model data as a package in the repository")
    p.add_argument("package_name", type=str,
                   help="Name of the package in which to publish the model data. If it ends with '*', all models matching the wildcard will be published as a package.")
    p.add_argument("--model-name", "-n", type=str,
                   help="Name of the model from which to publish data. If not given, the name of the package is used")
    p.add_argument("--trained-model", "-m", action="store_true", help="Include the trained model itself")
    p.add_argument("--training-data", "-t", choices=["extraction", "segmentation", "all"],
                   help="The type of training data to include in the package")
    p.add_argument("--overwrite", "-o", action="store_true", help="Overwrite an existing package")
    p.set_defaults(command="package", func_name="exec_publish")

    # package import
    p = pkg_subcommands.add_parser("import", help="Import model data from a package in the repository")
    p.add_argument("package_name", type=str, help="Name of the package from which to import model data")
    p.add_argument("--model-name", "-n", type=str,
                   help="Name of the model into which to import data. If not given, the name of the package is used. Will be created if it does not exist")
    p.set_defaults(command="package", func_name="exec_import")

    # package delete
    p = pkg_subcommands.add_parser("delete", help="Delete a package")
    p.add_argument("package_names", metavar="package_name", type=str, nargs="+",
                   help="Name(s) of the package to delete. You can use a * as wildcard")
    p.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    p.set_defaults(command="package", func_name="exec_delete")

    # server start
    server_parser = subcommands.add_parser("server", help="Commands dealing with the server that provides the Web UI.")
    server_subcommands = server_parser.add_subparsers()

    p = server_subcommands.add_parser("start", help="Start the webserver")
    p.add_argument("--port", "-p", help="The port on which to listen", default=8000)
    p.set_defaults(command="server", func_name="server_start")


    # dataset
    dataset_parser = subcommands.add_parser("dataset", help="Commands to work with different datasets")
    dataset_subcommands = dataset_parser.add_subparsers()

    # dataset convert
    p = dataset_subcommands.add_parser("convert", help="Convert the (excite) dataset into a different format")
    p.add_argument("model_name", type=str, help="The name of the model which has been trained with the given dataset")
    p.add_argument("--format", "-f", dest="target_format", type=str, default="anystyle", help="The format into which to convert the dataset")
    p.add_argument("--out-dir", "-o", dest="target_dir", type=str, help="The output directory, must exist. If not given, a subdirectory is created in the dataset folder")
    p.set_defaults(command="dataset", func_name="dataset_convert")

    # dataset fix
    p = dataset_subcommands.add_parser("fix", help="Fixes problems in EXcite datasets")
    p.add_argument("model_name", type=str, help="The name of the model which has been trained with the given dataset")
    p.set_defaults(command="dataset", func_name="dataset_fix")

    # parse arguments
    try:
        args = parser.parse_args()
    except Exception as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)

    # import command module and run command
    command = importlib.import_module("commands." + args.command)
    func_name = "execute"
    if hasattr(args, "func_name"):
        func_name = args.func_name
    kwargs = vars(args)
    del kwargs['command']
    if 'func_name' in kwargs:
        del kwargs['func_name']
    try:
        getattr(command, func_name)(**kwargs)
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
