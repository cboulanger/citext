import sys
import time
import traceback
from langdetect import detect
from EXparser.Segment_F1 import *
from JsonParser import *
from configs import *
from lib.logger import *
from lib.pogressbar import get_progress_bar


def call_exparser_extraction(model_dir: str, input_base_dir: str = None):
    load_model(model_dir)
    if input_base_dir is None:
        input_base_dir = config_url_data()

    list_of_files = []
    for item in os.listdir(os.path.join(input_base_dir, config_dirname_layouts())):
        if not item.startswith('.') and item.endswith('.csv'):
            list_of_files.append(os.path.splitext(item)[0])

    t1 = time.time()
    i = 1
    total = len(list_of_files)
    list_of_time = []
    progress_bar = get_progress_bar("Extracting references", total)
    log("Extracting references")
    counter = 0
    for filename in list_of_files:
        counter += 1
        progress_bar.goto(counter)
        log(f" - {filename}")
        t11 = time.time()
        path_layout = os.path.join(input_base_dir, config_dirname_layouts(), filename + '.csv')
        path_refs = os.path.join(input_base_dir, config_dirname_refs(), filename + '.csv')
        path_segs = os.path.join(input_base_dir, config_dirname_refs_seg(), filename + '.xml')
        path_refs_and_bibtex = os.path.join(input_base_dir, config_dirname_bibtex(), filename + '.bib')
        path_segs_prob = os.path.join(input_base_dir, config_dirname_seg_prob(), filename + '.csv')
        path_segs_dict = os.path.join(input_base_dir, config_dirname_seg_dict(), filename + '.csv')

        file = open(path_layout, encoding="utf-8")
        reader = file.read()
        global lng
        try:
            lng = detect(reader)
        except:
            log("Cannot extract language from " + path_layout)
            lng = ""
        finally:
            file.close()
        # todo: pass one model: rf as we have one model now for extraction for de and en
        try:
            txt, valid, _, ref_prob0 = ref_ext(reader, lng, idxx, rf, rf)
        except RuntimeWarning as warning:
            log(warning)
            continue
        refs = segment(txt, ref_prob0, valid)
        reslt, refstr, retex = sg_ref(txt, refs, 2)

        # result: segmented references # refstr: refstr references # retex: bibtex
        log('Number of references: ' + str(len(refstr)))
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
            json_dict = json.dumps(data, ensure_ascii=False)
            wf_ref_and_bib.write("%s\n" % json_dict)
            j += 1
        # create ref_seg_prob_file, ref_dict_file, ref_gws_file
        reslt, refstr, retex = sg_ref(txt, refs, 1)
        # reslt: ref_seg_prob
        wf_seg_prob = open(path_segs_prob, 'w')
        wf_ref_dic = open(path_segs_dict, 'w')
        len_of_ref_list = len(refstr)
        j = 0
        for item in reslt:
            wf_seg_prob.write("%s\n" % item)
            data = {}
            ref_seg_dic = createJson(item)
            data["ref_seg_dic"] = json.loads(ref_seg_dic)
            ref_text_x = refstr[j]
            data["ref_text_x"] = ref_text_x
            json_dict = json.dumps(data, ensure_ascii=False)
            wf_ref_dic.write("%s\n" % json_dict)
            j += 1
        i += 1
        t22 = time.time()
        temp = t22 - t11
        list_of_time.append(temp)
    t2 = time.time()
    log('Sum time: %s' % (t2 - t1))
    if len(list_of_time) > 0:
        log('Average Time: %s' % (sum(list_of_time) / float(len(list_of_time))))
