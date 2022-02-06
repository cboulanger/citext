# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import traceback
from configs import *

logf = open(config_url_venu() + 'logfile.log', "a")

output_on_same_line = False

def parse_and_format_output(output):
    global output_on_same_line
    # keep output that starts with ">" on one line
    if output.startswith(">"):
        if output_on_same_line:
            sys.stdout.write("\033[F")  # back to previous line
            sys.stdout.write("\033[K")  # clear line
        else:
            output_on_same_line = True;
        # we can add a progress meter later
        print(">>> " + output[1:])
    else:
        if output_on_same_line:
            print()
            output_on_same_line = False
        print(output)


def run_command(command):
    logf.write(command)
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    while True:
        return_code = proc.poll()
        if return_code is not None:
            break
        line = str(proc.stdout.readline()).strip()
        if line != "":
            parse_and_format_output(line)

    # subprocess returned with error
    if return_code != 0:
        raise RuntimeError("\n".join(proc.stderr.readlines()))


def call_run_layout_extractor():
    os.chdir(config_url_venu())
    command = 'java -jar cermine.layout.extractor-0.0.1-jar-with-dependencies.jar '
    command += config_url_pdfs() + ' '
    command += config_url_Layouts() + ' '
    command += '90000000'
    run_command(command)


def call_run_exmatcher():
    run_command('python run-crossref.py')


def call_run_exparser():
    run_command('python run-exparser.py')


def call_segmentation():
    run_command('python run-segmentation.py')


def call_extraction_training():
    for cmd in ["Feature_Extraction", "Txt2Vec", "Training_Ext"]:
        run_command('python /app/EXparser/' + cmd + '.py')


def call_segmentation_training():
    for cmd in ["Feature_Extraction", "Txt2Vec", "Training_Seg"]:
        run_command('python /app/EXparser/' + cmd + '.py')


if __name__ == "__main__":
    func_name = ''
    if len(sys.argv) > 1:
        func_name = sys.argv[1]
    try:
        if func_name == 'layout':
            call_run_layout_extractor()
        elif func_name == 'exparser':
            call_run_exparser()
        elif func_name == 'segmentation':
            call_segmentation()
        elif func_name == 'exmatcher':
            call_run_exmatcher()
        elif func_name == "train_extraction":
            call_extraction_training()
        elif func_name == "train_segmentation":
            call_segmentation_training()
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
        logf.write('\n*' * 50 + '\n')