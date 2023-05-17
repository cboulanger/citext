#!/usr/bin/env python3

import importlib
import os.path
import shutil
import subprocess
import sys
import traceback
from lib.logger import *
import argparse
from configs import *

# This is the CitExt CLI which however has been stripped of almost all the preexisting CLI
# commands which had been written for the EXcite engine.
# If needed, commands can be easily reimplemented.

if __name__ == "__main__":

    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='Run exparser tools.', prog="")
    subcommands = parser.add_subparsers()

    ### dataset ###
    server_parser = subcommands.add_parser("dataset", help="Manage datasets of training data")
    server_subcommands = server_parser.add_subparsers()

    # list
    p = server_subcommands.add_parser("list", help="List existing datasets")
    p.set_defaults(class_name="Dataset", func_name="list")

    # create
    p = server_subcommands.add_parser("create", help="Create a new dataset")
    p.add_argument("dataset_name", help="The name of the dataset")
    p.add_argument("--include", "-i", action="append", help="Name of a dataset that the dataset includes when the model is trained")
    p.set_defaults(class_name="Dataset", func_name="create")

    # delete
    p = server_subcommands.add_parser("delete", help="Delete the dataset")
    p.add_argument("dataset_name", help="The name of the dataset")
    p.set_defaults(class_name="Dataset", func_name="delete")

    ### server ###
    server_parser = subcommands.add_parser("server", help="Manage the server that provides the Web UI.")
    server_subcommands = server_parser.add_subparsers()

    # start
    p = server_subcommands.add_parser("start", help="Start the webserver")
    p.add_argument("--port", "-p", help="The port on which to listen", default=8000)
    p.set_defaults(command="server", func_name="server_start")

    # parse arguments
    try:
        args = parser.parse_args()
    except Exception as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)

    # import command module and run command
    kwargs = vars(args)
    if hasattr(args, "class_name"):
        module = importlib.import_module(f"lib.{args.class_name.lower()}")
        command = getattr(module, args.class_name)
        del kwargs['class_name']
    elif hasattr(args, "command"):
        command = importlib.import_module(f"commands.{args.command}")
        del kwargs['command']
    else:
        print("Missing command or invalid CLI configuration. Try --help.")
        sys.exit(1)

    if hasattr(args, "func_name"):
        func_name = args.func_name
        del kwargs['func_name']
    else:
        func_name = "execute"

    try:
        result = getattr(command, func_name)(**kwargs)
        if result is not None:
            print(result)
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
