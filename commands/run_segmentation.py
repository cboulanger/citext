import time
from langdetect import detect
from EXparser.Segment_F1 import *
from lib.JsonParser import *
from lib.logger import *
from lib.pogressbar import get_progress_bar

def call_exparser_segmentation(model_dir: str, input_base_dir=None):
    load_model(model_dir)
    if input_base_dir is None:
        input_base_dir = config_url_data()
    list_of_files = []
    for item in os.listdir(os.path.join(input_base_dir, config_dirname_refs())):
        if not item.startswith('.'):
            list_of_files.append(os.path.splitext(item)[0])
            #list_of_files.append(item)

    t1 = time.time()
    i = 1
    total = len(list_of_files)
    list_of_time = []
    progress_bar = get_progress_bar("Segmenting references", total)
    log(f"Segmenting references")
    counter = 0
    for filename in list_of_files:
        filename = str(filename)
        counter += 1
        progress_bar.goto(counter)
        log(f" - {filename}")
        t11 = time.time()
        path_refs = os.path.join(input_base_dir, config_dirname_refs(), filename + ".csv")
        path_segs = os.path.join(input_base_dir, config_dirname_refs_seg(), filename + ".xml")
        path_refs_and_bibtex = os.path.join(input_base_dir, config_dirname_bibtex(), filename + '.bib')
        path_segs_prob = os.path.join(input_base_dir, config_dirname_seg_prob(), filename + '.csv')
        path_segs_dict = os.path.join(input_base_dir, config_dirname_seg_dict(), filename + '.csv')

        with open(path_refs) as file:
            reader = str(file.read())
            # what do we need language detection for, anyways?
            global lng
            try:
                lng = detect(reader)
            except:
                log(f"Cannot detect language in {path_refs}")

        # txt, valid, _, ref_prob0 = ref_ext(reader)
        reader = re.sub(r'[\r\n]+', '\n', str(reader))
        reader = reader.split('\n')
        reader = reader[0:-1] if reader[-1] == '' else reader

        txt = []
        for row in reader:
            row = row.split('\t')
            txt.append(row[0])

        valid = [1] * len(txt)
        ref_prob0 = [(0, 1, 0, 0)] * len(txt)

        refs = segment(txt, ref_prob0, valid)
        # refs = list(range(0, len(txt)))
        reslt, refstr, retex = sg_ref(txt, refs, 2)

        # reslt: segmented references # refstr: refstr references # retex: bibtex
        #print ('Number of references: ' + str(len(refstr)))
        # create references file
        # wf = open(path_refs, 'w')
        # for item in refstr:
        #     wf.write("%s\n" % item)

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
        wf_ref_dict = open(path_segs_dict, 'w')
        #len_of_ref_list = len(refstr)
        j = 0
        for item in reslt:
            wf_seg_prob.write("%s\n" % item)
            data = {}
            ref_seg_dic = createJson(item)
            data["ref_seg_dic"] = json.loads(ref_seg_dic)
            ref_text_x = refstr[j]
            data["ref_text_x"] = ref_text_x
            json_dict = json.dumps(data, ensure_ascii=False)
            wf_ref_dict.write("%s\n" % json_dict)
            j += 1
        i += 1
        t22 = time.time()
        temp = t22 - t11
        list_of_time.append(temp)
    t2 = time.time()
    log('Sum time: %s' % (t2 - t1))
    if len(list_of_time) > 0:
        log('Average time: %s' % (sum(list_of_time) / float(len(list_of_time))))

