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


# legacy commands not yet migrated to argparse implementation
class Commands(Enum):
    LAYOUT = "layout"
    EXPARSER = "exparser"
    SEGMENTATION = "segmentation"
    EXMATCHER = "exmatcher"
    TRAIN_EXTRACTION = "train_extraction"
    TRAIN_SEGMENTATION = "train_segmentation"


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
            print(line)
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
    from commands.run_exparser import call_exparser_extraction
    call_exparser_extraction(os.path.join(config_model_dir(), get_version(), model_name))


def call_segmentation(model_name=None, input_dir=None):
    from commands.run_segmentation import call_exparser_segmentation
    call_exparser_segmentation(os.path.join(config_model_dir(), get_version(), model_name), input_dir)


if __name__ == "__main__":



    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='Run exparser tools.', prog="")
    subcommands = parser.add_subparsers()

    # model
    model_parser = subcommands.add_parser("model", help="Tools to work with models")
    model_subcommands = model_parser.add_subparsers()

    # model create
    mcp = model_subcommands.add_parser("create", help="Create a new model")
    mcp.add_argument("model_name", type=str, help="The name of the model to be created.")
    mcp.set_defaults(command="model_create")

    # model delete
    mdp = model_subcommands.add_parser("delete", help="Delete one or more models")
    mdp.add_argument("model_names",
                     metavar="model", type=str, nargs="+",
                     help="The name of the model to be deleted. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected for deletion")
    mdp.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    mdp.set_defaults(command="model_delete")

    # model list
    mlp = model_subcommands.add_parser("list", help="List all available models")
    mlp.set_defaults(command="model_list")

    # model merge
    mmp = model_subcommands.add_parser("merge", help="Merge one or more models into a new model")
    mmp.add_argument("target", type=str,
                     help="The name of the model into which the other models will be merged. Will be created if it does not exist.")
    mmp.add_argument("models",
                     metavar="model", type=str, nargs="+",
                     help="The name of the model which will be merged into the target model. If a model name ends with \"*\", it is used as a prefix and all models starting with this prefix are selected")
    mmp.add_argument("-O", "--omit-test-data",
                     help="When copying training data, omit the documents used for testing in the given models",
                     action="store_true")
    mmp.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    mmp.set_defaults(command="model_merge")

    # eval
    ep = subcommands.add_parser("eval", help="Evaluate a model")
    ep.add_argument("model_name", type=str, help="The name of the model to evaluate")
    ep.add_argument("--extraction", "-x", action="store_true", default=False, help="Evaluate extraction")
    ep.add_argument("--segmentation", "-s", action="store_true", default=False, help="Evaluate segmentation")
    ep.add_argument("--exparser-result-dir", "-e", metavar="path", type=str,
                    help="Path to the folder containing the output to evaluate", required=True)
    ep.add_argument("--gold-dir", "-g", metavar="path", type=str,
                    help="Path to the folder containing the 'gold standard' files against which to evaluate the result.",
                    required=True)
    ep.add_argument("--add-logfile", "-l", action="store_true", default=False,
                    help="Generate verbose debug logfile (.log)")
    ep.add_argument("--output-dir", "-d", metavar="path", type=str,
                    help="Path to the directory in which the evaluation output files should be stored. Defaults to the model's dataset directory.")
    ep.add_argument("--output-filename-prefix", "-f", metavar="prefix", type=str,
                    help="Prefix for the output files, to which the mode ('segmentation' or 'extraction') will be appended. Defaults to a timestamp.")
    ep.set_defaults(command="eval")

    # report
    ap = subcommands.add_parser("report", help="Generate a report of accuracy information for one or more models.")
    ap.add_argument("model_names", metavar="name", nargs="+",
                    help="One or more names of models to include in the accuracy report. If a name ends with *, all matching model names will be included.")
    ap.add_argument("--output-file", "-o",
                    help="Optional path to a file in which the results are stored as CSV data. If not given, they are printed to the console.")
    ap.add_argument("--prefix", "-p", default="",
                    help="An optional prefix to the accuracy files produced by evaluation")
    ap.set_defaults(command="report")

    # package
    pkg_parser = subcommands.add_parser("package",
                                        help="Commands to store model and training data as a package in a repository and download it from there.")
    pkg_subcommands = pkg_parser.add_subparsers()

    # package list
    rlp = pkg_subcommands.add_parser("list", help="List all available data packages")
    rlp.set_defaults(command="package", func_name="exec_list")

    # package publish
    rpp = pkg_subcommands.add_parser("publish", help="Publish model data as a package in the repository")
    rpp.add_argument("package_name", type=str,
                     help="Name of the package in which to publish the model data. If it ends with '*', all models matching the wildcard will be published as a package.")
    rpp.add_argument("--model-name", "-n", type=str,
                     help="Name of the model from which to publish data. If not given, the name of the package is used")
    rpp.add_argument("--trained-model", "-m", action="store_true", help="Include the trained model itself")
    rpp.add_argument("--training-data", "-t", choices=["extraction", "segmentation", "all"],
                     help="The type of training data to include in the package")
    rpp.add_argument("--overwrite", "-o", action="store_true", help="Overwrite an existing package")
    rpp.set_defaults(command="package", func_name="exec_publish")

    # package import
    rip = pkg_subcommands.add_parser("import", help="Import model data from a package in the repository")
    rip.add_argument("package_name", type=str, help="Name of the package from which to import model data")
    rip.add_argument("--model-name", "-n", type=str,
                     help="Name of the model into which to import data. If not given, the name of the package is used. Will be created if it does not exist")
    rip.set_defaults(command="package", func_name="exec_import")

    # package delete
    rdp = pkg_subcommands.add_parser("delete", help="Delete a package")
    rdp.add_argument("package_names", metavar="package_name", type=str, nargs="+",
                     help="Name(s) of the package to delete. You can use a * as wildcard")
    rdp.add_argument("-I", "--non-interactive", action="store_true", help="Do not ask for confirmation")
    rdp.set_defaults(command="package", func_name="exec_delete")

    # server start

    server_parser = subcommands.add_parser("server", help="Commands dealing with the server that provides the Web UI.")
    server_subcommands = server_parser.add_subparsers()

    p = server_subcommands.add_parser("start", help="Start the webserver")
    p.add_argument("--port", "-p", help="The port on which to listen", default=8000)
    p.set_defaults(command="server", func_name="server_start")

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
            func_name = "execute"
            if hasattr(args, "func_name"):
                func_name = args.func_name
            kwargs = vars(args)
            del kwargs['command']
            if 'func_name' in kwargs:
                del kwargs['func_name']
            # call command function
            getattr(command, func_name)(**kwargs)
            sys.exit(0)
    except ModuleNotFoundError as err:
        # it's a legacy command or something went wrong
        print(str(err))

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
            from commands.training import call_extraction_training
            call_extraction_training(sys.argv[2])

        elif func_name == Commands.TRAIN_SEGMENTATION.value:
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            from commands.training import call_segmentation_training
            call_segmentation_training(sys.argv[2])

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
