# -*- coding: utf-8 -*-
import os.path
import shutil
import subprocess
import sys
import traceback
import builtins
from progress.bar import Bar
from configs import *
from EXparser.Training_Seg import train_segmentation
from EXparser.Feature_Extraction import extract_features
from EXparser.Txt2Vec import text_to_vec
from EXparser.Training_Ext import train_extraction
from run_segmentation import call_Exparser_segmentation
from run_exparser import call_Exparser

logf = open(config_url_venu() + 'logfile.log', "a")

dataset_dir = "Exparser/Dataset"
model_dir = "Exparser/Models"

class Commands(Enum):
    LAYOUT = "layout"
    EXPARSER = "exparser"
    SEGMENTATION = "segmentation"
    EXMATCHER = "exmatcher"
    TRAIN_EXTRACTION = "train_extraction"
    TRAIN_SEGMENTATION = "train_segmentation"
    CREATE_MODEL = "create_model"

# monkey-patch print to support progress bar output
progressbar = None
currtask = ""
oldprint = builtins.print
total = len(os.listdir(config_url_pdfs()))
index = 0

def progress_bar_print(string="", end="\n", file=None):
    global progressbar, currtask, oldprint, total, index
    # keep output that starts with ">" as a progress indicator message that has the form ">task:index/total:additional_text_for_logfile"
    builtins.print = oldprint  # progress bar needs the default "print"
    if string.startswith(">") or string.startswith("processing"):
        if string.startswith(">"):
            task, progress, *_ = string[1:].split(":")
            index, total = progress.split("/")
        else:
            task = "Extracting layout features"
            index = index + 1
        if not progressbar or task != currtask:
            if progressbar:
                progressbar.finish()
            currtask = task
            progressbar = Bar(task, bar_prefix=' [', bar_suffix='] ', empty_fill='.',
                              suffix='%(index)d/%(max)d: %(eta_td)s remaining...',
                              max=int(total))
        progressbar.goto(int(index))
        if int(index) == int(total):
            total = None
            index = 0
            progressbar.finish()
    elif string.startswith("Used memory is megabytes"):
        # ignore cermine output
        pass
    else:
        if progressbar:
            progressbar.finish()
            progressbar = None
            total = None
            index = 0
        print(string, end = end)
    logf.write(string + end)
    builtins.print = progress_bar_print

builtins.print = progress_bar_print

def run_command(command):
    logf.write(command)
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
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
    call_Exparser(os.path.join(model_dir, get_version(), model_name))


def call_segmentation(model_name=None):
    call_Exparser_segmentation(os.path.join(model_dir, get_version(), model_name))


def call_extraction_training(model_name: str):
    extract_features(os.path.join(dataset_dir,  model_name))
    text_to_vec(os.path.join(dataset_dir, model_name))
    train_extraction(os.path.join(dataset_dir, model_name),
                     os.path.join(model_dir, get_version(), model_name))


def call_segmentation_training(model_name: str):
    extract_features(os.path.join(dataset_dir, model_name))
    text_to_vec(os.path.join(dataset_dir, model_name))
    train_segmentation(os.path.join(dataset_dir, model_name),
                       os.path.join(model_dir, get_version(), model_name))


def create_model_folder(model_name: str):
    path = os.path.join(model_dir, get_version(), model_name)
    os.mkdir(path)

    # todo: get rid of the copying if all models are trainable
    default_path = os.path.join(model_dir, get_version(), "default")
    src_files = os.listdir(default_path)
    for file_name in src_files:
        full_file_name = os.path.join(default_path, file_name)
        if os.path.isfile(full_file_name) and "kde_" in file_name:
            shutil.copy(full_file_name, path)

    os.mkdir(os.path.join(dataset_dir, model_name))
    for subdir in DatasetDirs:
        os.mkdir(os.path.join(dataset_dir, model_name, subdir.value))

    sys.stdout.write("Please put the training data to: " + os.path.join(dataset_dir,  model_name)
                     + " and then run the training commands.\n")


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
            create_model_folder(sys.argv[2])
        else:
            raise RuntimeError("Wrong input command: '" + func_name + "'; valid commands are: " +
                               ", ".join([c.value for c in Commands]) + "\n")
    except KeyboardInterrupt:
        sys.stderr.write("\nAborted\n")
        logf.write("\nAborted")
        sys.exit(1)
    except:
        sys.stderr.write(traceback.format_exc())
        logf.write(traceback.format_exc())
        sys.exit(1)
    finally:
        logf.write('\n' + ('*' * 50) + '\n')
