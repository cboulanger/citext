# -*- coding: utf-8 -*-
import os
import sys
import time
import traceback
from langdetect import detect
from EXparser.Segment_F1 import *
from JsonParser import *
from configs import *

reload(sys)
sys.setdefaultencoding('utf8')

logf = open(config_url_venu() + 'logfile.log', "a")

def call_Exparser(list_of_files, subfolder):
    t1 = time.time()
    i = 1
    count = len(list_of_files)
    list_of_time = []
    for filename in list_of_files:
        print("Reference Extraction:%s/%s:%s" % (i, count, filename))
        try:
            t11 = time.time()
            path_layout = config_url_Layouts() + subfolder + filename + '.csv'
            path_refs = config_url_Refs() + subfolder + filename + '.csv'
            path_segs = config_url_Refs_segment() + subfolder + filename + '.xml'
            path_refs_and_bibtex = config_url_Refs_bibtex() + subfolder + filename + '.csv'
            path_segs_prob = config_url_Refs_segment_prob() + subfolder + filename + '.csv'
            path_segs_ditc = config_url_Refs_segment_dict() + subfolder + filename + '.csv'

            file = open(path_layout, 'rb')
            reader = file.read()
            global lng
            try:
                lng = detect(reader.decode('utf-8'))
            except:
                logf.write("Cannot extract language from " + path_layout)
                lng = ""
            finally:
                file.close()
            txt, valid, _, ref_prob0 = ref_ext(reader, lng, idxx, clf1, clf2)
            refs = segment(txt, ref_prob0, valid)
            reslt, refstr, retex = sg_ref(txt, refs, 2)

            # result: segmented references # refstr: refstr references # retex: bibtex
            logf.write('Number of references: ' + str(len(refstr)))
            # create references file 
            wf = open(path_refs, 'w')
            for item in refstr:
                wf.write("%s\n" % item)
            # create refs_seg file
            wf = open(path_segs, 'w')
            for item in reslt:
                wf.write("%s\n" % item)
            # create ref_bib file
            wf = open(path_refs_and_bibtex, 'w')
            wf_ref_and_bib = open(path_refs_and_bibtex, 'w')
            j = 0
            for item in retex:
                wf.write("%s\n" % item)
                data = {}
                data["ref_bib"] = item
                ref_text_x = refstr[j]
                data["ref_text_x"] = ref_text_x
                json_dict = json.dumps(data, ensure_ascii=False, encoding='utf8')
                wf_ref_and_bib.write("%s\n" % json_dict)
                j += 1
            # create ref_seg_prob_file, ref_dict_file, ref_gws_file
            reslt, refstr, retex = sg_ref(txt, refs, 1)
            # reslt: ref_seg_prob
            wf_seg_prob = open(path_segs_prob, 'w')
            wf_ref_dic = open(path_segs_ditc, 'w')
            len_of_ref_list = len(refstr)
            j = 0
            for item in reslt:
                wf_seg_prob.write("%s\n" % item)
                data = {}
                ref_seg_dic = createJson(item)
                data["ref_seg_dic"] = json.loads(ref_seg_dic)
                ref_text_x = refstr[j]
                data["ref_text_x"] = ref_text_x
                json_dict = json.dumps(data, ensure_ascii=False, encoding='utf8')
                wf_ref_dic.write("%s\n" % json_dict)
                j += 1
            logf.write('Proccess is done for: ' + filename)
            logf.write('-' * 100)
            i += 1
            t22 = time.time()
            temp = t22 - t11
            list_of_time.append(temp)
        except:
            print(traceback.format_exc())
            logf.write('File Name: %s \n' % (filename))
            logf.write(traceback.format_exc())
            logf.write('*' * 50 + '\n')
    # **********************************************************
    t2 = time.time()
    logf.write('Sum Time: %s' % (t2 - t1))
    if (len(list_of_time) > 0):
        logf.write('Ave Time: %s' % (sum(list_of_time) / float(len(list_of_time))))


if __name__ == "__main__":
    try:
        subfolder = '/'
        dir_list = os.listdir(config_url_Layouts() + subfolder)
        list_of_files = []
        for item in dir_list:
            if not item.startswith('.') and item.endswith('.csv'):
                list_of_files.append(os.path.splitext(item)[0])

        call_Exparser(list_of_files, subfolder)
    except:
        print(traceback.format_exc())
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
