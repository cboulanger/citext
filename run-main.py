# -*- coding: utf-8 -*-
import shutil
import subprocess
import sys
import traceback
from configs import *
from progress.bar import Bar

from EXparser.Training_Seg import train_segmentation
from EXparser.Feature_Extraction import extract_features
from EXparser.Txt2Vec import text_to_vec
from EXparser.Training_Ext import train_extraction
from run_segmentation import call_Exparser_segmentation
from run_exparser import call_Exparser

logf = open(config_url_venu() + 'logfile.log', "a")


def run_command(command):
    logf.write(command)
    progressbar = None
    currtask = ""
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    while True:
        return_code = proc.poll()
        if return_code is not None:
            break
        line = str(proc.stdout.readline()).strip()
        if line != "":
            # keep output that starts with ">" as a progress indicator message ">task:index/total"
            if line.startswith(">"):
                [task, progress, *_] = line[1:].split(":")
                [index, total] = progress.split("/")
                if not progressbar or task != currtask:
                    if progressbar:
                        progressbar.finish()
                    currtask = task
                    progressbar = Bar(task, bar_prefix=' [', bar_suffix='] ', empty_fill = '.',
                                      suffix='%(index)d/%(max)d: %(eta_td)s remaining...',
                                      max=int(total))
                progressbar.goto(int(index))
                if int(index) == int(total):
                    progressbar.finish()
            else:
                if progressbar:
                    progressbar.finish()
                    progressbar = None
                    print()
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
    call_Exparser("EXparser/Models/" + get_version() + "/" + model_name)


def call_segmentation(model_name=None):
    call_Exparser_segmentation("EXparser/Models/" + get_version() + "/" + model_name)


def call_extraction_training(model_name: str):
    extract_features("EXparser/Dataset/" + model_name)
    text_to_vec("EXparser/Dataset/" + model_name)
    train_extraction("EXparser/Dataset/" + model_name,
                     "EXparser/Models/" + get_version() + "/" + model_name)


def call_segmentation_training(model_name: str):
    extract_features("/app/EXparser/Dataset/" + model_name)
    text_to_vec("/app/EXparser/Dataset/" + model_name)
    train_segmentation("/app/EXparser/Dataset/" + model_name,
                       "/app/EXparser/Models/" + get_version() + "/" + model_name)


def create_model_folder(model_name: str):
    path = "/app/EXparser/Models/" + get_version() + "/" + model_name
    os.mkdir(path)

    # todo: get rid of the copying if all models are trainabe
    default_path = "/app/EXparser/Models/" + get_version() + "/default/"
    src_files = os.listdir(default_path)
    for file_name in src_files:
        full_file_name = os.path.join(default_path, file_name)
        if os.path.isfile(full_file_name) and "kde_" in file_name:
            shutil.copy(full_file_name, path)

    os.mkdir("/app/EXparser/Dataset/" + model_name)

    sys.stdout.write("Please put the training data to: " + "/app/EXparser/Dataset/" + model_name
                     + ". And perform the training.")


if __name__ == "__main__":
    func_name = ''
    if len(sys.argv) > 1:
        func_name = sys.argv[1]
    try:
        if func_name == 'layout':
            call_run_layout_extractor()
        elif func_name == 'exparser':
            if len(sys.argv) == 3:
                call_run_exparser(sys.argv[2])
            else:
                call_run_exparser()
        elif func_name == 'segmentation':
            if len(sys.argv) == 3:
                call_segmentation(sys.argv[2])
            else:
                call_segmentation()
        elif func_name == 'exmatcher':
            call_run_exmatcher()
        elif func_name == "train_extraction":
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            call_extraction_training(sys.argv[2])
        elif func_name == "train_segmentation":
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            call_segmentation_training(sys.argv[2])
        elif func_name == "create_model":
            if len(sys.argv) < 3:
                raise RuntimeError("Please provide a name for the model")
            create_model_folder(sys.argv[2])
        else:
            raise RuntimeError("Wrong input command: " + func_name)
    except KeyboardInterrupt:
        sys.stderr.write("\nAborted")
        logf.write("\nAborted")
        sys.exit(1)
    except:
        sys.stderr.write(traceback.format_exc())
        logf.write(traceback.format_exc())
        sys.exit(1)
    finally:
        logf.write('\n' + ('*' * 50) + '\n')
