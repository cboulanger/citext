import importlib
import os.path
import shutil
import subprocess
import sys
import traceback
from lib.logger import *
from dotenv import load_dotenv
import argparse
from configs import *

load_dotenv()

if __name__ == "__main__":

    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='Run exparser tools.', prog="")
    subcommands = parser.add_subparsers()

    # layout
    p = subcommands.add_parser("layout", help="Extract layout information from PDF files")
    p.add_argument("--input-dir", "-i", help="The directory containing the PDFs")
    p.add_argument("--output-dir", "-o", help="The directory into which to save the layout files")
    p.set_defaults(command="layout", func_name="call_run_layout_extractor")

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

    # layout

    # exparser = extraction
    p = subcommands.add_parser("exparser", help="Run extraction & segmentation")
    p.add_argument("model_name", type=str, help="The name of the model to use", default="default")
    p.add_argument("--input-base-dir", "-d", type=str, help="The parent directory of the workflow folders",
                   default=None)
    p.set_defaults(command="extraction")

    # segmentation
    p = subcommands.add_parser("segmentation", help="Run segmentation")
    p.add_argument("model_name", type=str, help="The name of the model to use", default="default")
    p.add_argument("--input-base-dir", "-d", type=str, help="The parent directory of the workflow folders",
                   default=None)
    p.set_defaults(command="segmentation")

    # train
    train_parser = subcommands.add_parser("train", help="Commands to train the models")
    train_subcommands = train_parser.add_subparsers()

    # train extraction
    p = train_subcommands.add_parser("extraction", help="Train the extraction model")
    p.add_argument("model_name", type=str, help="The name of the model to use", default="default")
    p.add_argument("--version", "-v", type=str, help="The exparser engine version to use for training", default=None)
    p.set_defaults(command="training", func_name="call_extraction_training")

    # train segmentation
    p = train_subcommands.add_parser("segmentation", help="Train the segmentation model")
    p.add_argument("model_name", type=str, help="The name of the model to use", default="default")
    p.add_argument("--version", "-v", type=str, help="The exparser engine version to use for training", default=None)
    p.set_defaults(command="training", func_name="call_segmentation_training")

    # train completeness
    p = train_subcommands.add_parser("completeness", help="Train the completeness of the models")
    p.add_argument("model_name", type=str, help="The name of the model to use", default="default")
    p.add_argument("--version", "-v", type=str, help="The exparser engine version to use for training", default=None)
    p.set_defaults(command="training", func_name="call_completeness_training")

    # eval
    p = subcommands.add_parser("eval", help="Evaluate a pretrained model")
    p.add_argument("model_name", type=str, help="The name of the model to evaluate")
    p.add_argument("--extraction", "-x", action="store_true", default=False, help="Evaluate extraction")
    p.add_argument("--segmentation", "-s", action="store_true", default=False, help="Evaluate segmentation")
    p.add_argument("--exparser-result-dir", "-e", metavar="path", type=str,
                   help="Path to the folder containing the output to evaluate", required=True)
    p.add_argument("--gold-dir", "-g", metavar="path", type=str,
                   help="Path to the folder containing the 'gold standard' files against which to evaluate the result.",
                   required=True)
    p.add_argument("--add-logfile", "-l", action="store_true", default=False,
                   help="Generate verbose debug logfile (.log)")
    p.add_argument("--output-dir", "-d", metavar="path", type=str,
                   help="Path to the directory in which the evaluation output files should be stored. Defaults to the model's dataset directory.")
    p.add_argument("--output-filename-prefix", "-f", metavar="prefix", type=str,
                   help="Prefix for the output files, to which the mode ('segmentation' or 'extraction') will be appended. Defaults to a timestamp.")
    p.set_defaults(command="eval")

    # eval_full_workflow
    p = subcommands.add_parser("eval_full_workflow", help="Splits, trains and evaluates model")
    p.add_argument("model_name", type=str, help="The name of the model to evaluate")
    p.add_argument("--prefix", "-p", type=str, help="The prefix to use for the split model which is evaluated",
                   default="test_")
    p.add_argument("--skip_splitting", "-P", help="Skip the splitting step", action="store_true")
    p.add_argument("--skip_extraction", "-X", help="Skip extraction training and evaluation", action="store_true")
    p.add_argument("--skip_segmentation", "-S", help="Skip segmentation training and evaluation", action="store_true")
    p.add_argument("--add-logfile", "-l", help="Output additional log information in the model folder",
                   action="store_true")
    p.set_defaults(command="eval_full_workflow", func_name="run_full_eval_workflow")

    # report
    p = subcommands.add_parser("report", help="Generate a report of accuracy information for one or more models.")
    p.add_argument("model_names", metavar="name", nargs="+",
                   help="One or more names of models to include in the accuracy report. If a name ends with *, all matching model names will be included.")
    p.add_argument("--output-file", "-o",
                   help="Optional path to a file in which the results are stored as CSV data. If not given, they are printed to the console.")
    p.add_argument("--prefix", "-p", default="",
                   help="An optional prefix to the accuracy files produced by evaluation")
    p.set_defaults(command="report")

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

    # engine
    engine_parser = subcommands.add_parser("engine", help="Commands to manage the recognition engine")
    engine_subcommands = engine_parser.add_subparsers()

    # engine install
    p = engine_subcommands.add_parser("install", help="Install a particular version of the engine")
    p.add_argument("version", type=str, help="Install a particular version of the recognition engine")
    p.set_defaults(command="engine", func_name="engine_install")

    # engine list
    p = engine_subcommands.add_parser("list", help="List all installed engines")
    p.set_defaults(command="engine", func_name="exec_list")

    # engine use
    p = engine_subcommands.add_parser("use", help="Use a particular version of the engine")
    p.add_argument("version", type=str,
                   help="Use a particular version of the recognition engine, which must be installed first")
    p.set_defaults(command="engine", func_name="exec_use")

    # set the exparser engine path
    if os.path.exists(config_exparser_version_file()):
        with open(config_exparser_version_file()) as f:
            version = f.read()
        if version != get_version():
            from commands.engine import check_version
            check_version(version)
            sys.path.insert(0, config_exparser_dir(version))

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
