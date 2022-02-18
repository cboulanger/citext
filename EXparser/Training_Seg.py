# -*- coding: UTF-8 -*- 
import csv
import time
import pickle
import sklearn_crfsuite
from .src.gle_fun import *
from .src.gle_fun_seg import *


def train_segmentation(data_dir: str, model_dir: str):
    # preparing training data
    fold = data_dir + "/SEG"
    fdir = os.listdir(fold)
    train_sents = []
    train_feat = []
    train_label = []
    total = str(len(fdir))
    for u in range(len(fdir)):
        print('>Segmentation training:' + str(u + 1) + '/' + total)
        if fdir[u].startswith("."):
            continue
        fname = fold + "/" + fdir[u]
        file = open(fname, encoding="utf-8")
        reader = csv.reader(file, delimiter='\t', quoting=csv.QUOTE_NONE)  # , quotechar='|'
        for row in reader:
            tic = time.time()
            ln = row[0]
            if ln.strip() == "":
                continue
            ln = re.sub(r'<author>|</author>', '', ln)  # remove author tag
            ln = re.sub(r'</fpage>|<lpage>', '', ln)  # change page tag
            ln = re.sub(r'<fpage>', '<page>', ln)  # change page tag
            ln = re.sub(r'</lpage>', '</page>', ln)  # change page tag
            ln = preproc(ln)
            ln = ln.split()
            l = -1  # no tag is open

            w = ln[0]
            a, b, l = findtag(w, l)
            train_sents.append([(a, b)])
            train_feat.append([word2feat(a, stopw, 0, len(ln), b1, b2, b3, b4, b5, b6)])
            train_label.append([b])

            if 1 < len(ln):
                w1 = ln[1]
                a, b, l = findtag(w1, l)
                train_sents[len(train_sents) - 1].extend([(a, b)])
                train_feat[len(train_feat) - 1].extend([word2feat(a, stopw, 1, len(ln), b1, b2, b3, b4, b5, b6)])
                train_label[len(train_label) - 1].extend([b])

            if 2 < len(ln):
                w2 = ln[2]
                a, b, l = findtag(w2, l)
                train_sents[len(train_sents) - 1].extend([(a, b)])
                train_feat[len(train_feat) - 1].extend([word2feat(a, stopw, 2, len(ln), b1, b2, b3, b4, b5, b6)])
                train_label[len(train_label) - 1].extend([b])
            # update features
            train_feat[len(train_feat) - 1] = add2feat(train_feat[len(train_feat) - 1], 0)

            for i in range(1, len(ln)):
                # add the +2 word
                if i < len(ln) - 2:
                    w = ln[i + 2]
                    a, b, l = findtag(w, l)
                    train_sents[len(train_sents) - 1].extend([(a, b)])
                    train_feat[len(train_feat) - 1].extend(
                        [word2feat(a, stopw, i + 2, len(ln), b1, b2, b3, b4, b5, b6)])
                    train_label[len(train_label) - 1].extend([b])
                # add their features to w
                # update features
                train_feat[len(train_feat) - 1] = add2feat(train_feat[len(train_feat) - 1], i)
            toc = time.time()
        # print 'processing time = '+ str(toc - tic)
        file.close()
    print("sklearn_crfsuite.CRF")
    crf = sklearn_crfsuite.CRF(
        algorithm='pa',
        # c2=0.8,
        all_possible_transitions=True,
        all_possible_states=True
    )
    print("crf.fit")
    crf.fit(train_feat, train_label)
    print("Saving segmentation model")
    with open(model_dir + '/crf_model.pkl', 'wb') as fid:
        pickle.dump(crf, fid)


# train()
