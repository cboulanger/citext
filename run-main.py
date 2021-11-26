# -*- coding: utf-8 -*-
import time, datetime, json, os, subprocess, traceback
import sys
from configs import *
from EXparser.run_training import _call_extraction_training

logf = open(config_url_venu() + 'logfile.log', "a")


def call_run_layout_extractor():
    command = ''
    try:
        print(command)
        os.chdir(config_url_venu())        
        command = 'java -jar cermine.layout.extractor-0.0.1-jar-with-dependencies.jar '
        command += config_url_pdfs() + ' '
        command += config_url_Layouts() + ' '
        command += '90000000'

        print(command)
        proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)
    except:
        print(traceback.format_exc())
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
    return command


def call_run_exmatcher():
    command = ''
    try:
        command = 'python run-crossref.py'
        print(command)
        proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)
    except:
        print(traceback.format_exc())
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
    return command


def call_run_exparser():
    command = ''
    try:
        command = 'python run-exparser.py'
        print(command)
        proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)  
    except:
        print(traceback.format_exc())
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
    return command


def call_extraction_training():
    _call_extraction_training()


if __name__ == "__main__":
    func_name = ''
    if len(sys.argv) > 1:
        func_name = sys.argv[1]
    if func_name == 'layout':
        call_run_layout_extractor()
    elif func_name == 'exparser':
        call_run_exparser()
    elif func_name == 'exmatcher':
        call_run_exmatcher()
    elif func_name == "train_extraction":
        call_extraction_training()
    else:
        print("Wrong input command!")