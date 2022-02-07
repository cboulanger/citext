# -*- coding: utf-8 -*-
import time, os, subprocess
import traceback
from configs import *

logf = open(config_url_venu() + 'logfile.log', "a")


def excite_call_Exmatcher_python(filename):
    command = ''
    try:
        os.chdir(config_url_venu())
        command = 'python3.6 call_exmatcher_crossref.py ' + filename + '.csv'
        print(command)
        proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
    except:
        print(traceback.format_exc())
        logf.write('File Name: %s \n' %(filename))
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
    return command


def excite_call_Exmatcher():
    try:
        folder_path = config_url_Refs_segment_dict()
        dir_list = os.listdir(folder_path)
        list_of_files = []
        list_of_time = []
        i = 1
        count = len(dir_list)
        t1 = time.time()
        for item in dir_list:
            t11 = time.time()
            if item != 'Thumbs.db':
                list_of_files.append(os.path.splitext(item)[0])
                print("%s of %s --- File name is : %s" %(i, count, item))            
                excite_call_Exmatcher_python(os.path.splitext(item)[0])
                print('*' *100)
            i += 1
            t22 = time.time()
            temp = t22 - t11
            list_of_time.append(temp)
        t2 = time.time()
        print('Sum Time: %s' %(t2-t1))
        print('Ave Time: %s' %(sum(list_of_time) / float(len(list_of_time))))
    except:
        print(traceback.format_exc())
        # logf.write('File Name: %s \n' %(filename))
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')


if __name__ == "__main__":
    excite_call_Exmatcher()