import os, csv
import regex as re
import numpy as np
import pickle
from sklearn.neighbors import KernelDensity
from lib.pogressbar import get_progress_bar
from lib.logger import log
from configs import *

def dist_tags(b):
    ntag = []
    dtag = []
    ltag = []
    atag = []
    gtag = []
    abv0 = ['FN', 'YR', 'AT', 'PG', 'SR', 'ED']
    b = [tmp for tmp in b if tmp in abv0]
    wtag = [1 if tmp in b else 0 for tmp in abv0]
    tmp = [b[j] for j in sorted(set([b.index(elem) for elem in b]))]
    bb = b[::-1]
    tmp2 = [bb[j] for j in sorted(set([bb.index(elem) for elem in bb]))]
    for i in range(len(abv0)):
        if abv0[i] in b:
            # a=len(re.findall(r'('+abv0[i]+')+',''.join(b)))
            # ntag.extend([1.0*a/len(b)])
            # tmp = re.finditer(r'('+abv0[i]+')+',''.join(b))
            # dtag.extend([1.0*np.mean([(m.end(0)-m.start(0))/2 for m in tmp])/len(b)])
            # tmp=[0]*2
            # tmp[0]=b.index(abv0[i])
            # tmp[1]=len(b)-list(reversed(b)).index(abv0[i])
            # a=filter(lambda a: a != abv0[i], {i for i in b[tmp[0]:tmp[1]]})
            # ltag.extend([1.0*len(a)/len(b)])
            # tmp=[b[j] for j in sorted(set([b.index(elem) for elem in b]))]
            # atag.extend([1.0*(tmp.index(abv0[i])+1)/len(tmp)])   #position of the tag in
            # ntag.extend([1.0*(tmp2.index(abv0[i])+1)/len(tmp2)])   #position of the tag in the reference string
            atag.extend([tmp.index(abv0[i]) + 1])  # position of the tag in
            ntag.extend([tmp2.index(abv0[i]) + 7 - len(tmp2)])  # position of the tag in the reference string
        else:
            ntag.extend([0])
            dtag.extend([-1])
            ltag.extend([-1])
            atag.extend([0])

    gtag = np.concatenate((ltag, atag, wtag, ntag))  # best
    # gtag=np.concatenate((ntag,[wtag]))
    return ntag, dtag, ltag, atag, wtag, gtag


def findtag(w, l):  # w is the word and l is if the tag is still open
    tag = ['given-names', 'surname', 'year', 'title', 'editor', 'source', 'publisher', 'other', 'volume', 'page',
           'issue', 'url', 'identifier']

    a = -1
    i = 0
    v = True
    while (i < len(tag)) & (v):
        tmp1 = re.findall(r'<' + tag[i] + '>', w)
        tmp2 = re.findall(r'</' + tag[i] + '>', w)
        if (bool(tmp1) & bool(tmp2)):
            v = False
            w = re.sub(r'<' + tag[i] + '>|</' + tag[i] + '>', '', w)
            a = abv[i]
            l = -1
        elif tmp2:
            v = False
            w = re.sub(r'<' + tag[i] + '>|</' + tag[i] + '>', '', w)
            a = abv[i]
            l = -1
        elif tmp1:
            v = False
            w = re.sub(r'<' + tag[i] + '>|</' + tag[i] + '>', '', w)
            a = abv[i]
            l = i
        i += 1
    if ((v) & (l != -1)):
        a = abv[l]
    elif ((v) & (l == -1)):
        a = 'XX'
    return w, a, l


def preproc(ln):
    # remove or replace strange character:
    ln = re.sub(r'\p{Pd}', '-', ln)
    ln = re.sub(r'<article-title>', '<title>', ln)
    ln = re.sub(r'</article-title>', '</title>', ln)

    # remove empty tags
    tag = 'given-names|surname|year|title|editor|source|publisher|other|page|volume|author|fpage|lpage|issue|url|identifier'
    tmp0 = re.finditer('<(' + tag + ')>\s*</(' + tag + ')>', ln)
    tmp = [(m.start(0), m.end(0)) for m in tmp0]
    while tmp:
        ln = ln[0:tmp[0][0]] + ' ' + ln[tmp[0][1]:]
        tmp0 = re.finditer('<(' + tag + ')>\s*</(' + tag + ')>', ln)
        tmp = [(m.start(0), m.end(0)) for m in tmp0]

    # add space before new tag
    tmp0 = re.finditer(r'[^\s\(\[\{]<[^/]', ln)
    tmp = [m.start(0) for m in tmp0]
    while tmp:
        ln = ln[0:tmp[0] + 1] + ' ' + ln[tmp[0] + 1:]
        tmp0 = re.finditer(r'[^\s\(\[\{]<[^/]', ln)
        tmp = [m.start(0) for m in tmp0]

    # add space before new tag with parenthese
    tmp0 = re.finditer(r'[^\s][\(\[\{]<[^/]', ln)
    tmp = [m.start(0) for m in tmp0]
    while tmp:
        ln = ln[0:tmp[0] + 1] + ' ' + ln[tmp[0] + 1:]
        tmp0 = re.finditer(r'[^\s][\(\[\{]<[^/]', ln)
        tmp = [m.start(0) for m in tmp0]

    # remove space after beginning of new tag
    tmp0 = re.finditer('<(' + tag + ')>\s', ln)
    tmp = [m.end(0) for m in tmp0]
    while tmp:
        ln = ln[0:tmp[0] - 1] + ln[tmp[0]:]
        tmp0 = re.finditer('<(' + tag + ')>\s', ln)
        tmp = [m.end(0) for m in tmp0]

    # remove space before end of tag
    tmp = ln.find(' </')
    while tmp != -1:
        ln = ln[0:tmp] + ln[tmp + 1:]
        tmp = ln.find(' </')

    # separate tow tags
    tmp = ln.find('><')
    while tmp != -1:
        ln = ln[0:tmp + 1] + ' ' + ln[tmp + 1:]
        tmp = ln.find('><')

    return ln

def train_completeness(dataset_dir: str, model_dir:str):
    # preparing training data
    global abv
    abv = ['FN', 'LN', 'YR', 'AT', 'ED', 'SR', 'PB', 'OT', 'VL', 'PG', 'IS', 'UR', 'ID']
    dtag = []
    ltag = []
    ntag = []
    atag = []
    wtag = []
    gtag = []  # general
    train_label = []
    seg_dir = os.path.join(dataset_dir, DatasetDirs.SEG.value)
    lyt_dir = os.path.join(dataset_dir, DatasetDirs.LYT.value)
    refld_folder = os.path.join(dataset_dir, DatasetDirs.REFLD.value)

    seg_files = os.listdir(seg_dir)
    total = len(seg_files)
    counter = 0
    progress_bar = get_progress_bar("Model completeness training", total)
    log("Model completeness training:")
    for curr_file in seg_files:
        counter += 1
        progress_bar.goto(int(counter/2))
        if curr_file.startswith(".") or not curr_file.endswith(".xml"):
            continue
        log(f" - {curr_file}")
        fname = os.path.join(seg_dir, curr_file)
        file = open(fname)
        reader = csv.reader(file, delimiter='\t', quoting=csv.QUOTE_NONE)  # , quotechar='|'
        for row in reader:
            ln = row[0]
            ln = re.sub(r'<author>|</author>', '', ln)  # remove author tag
            ln = re.sub(r'</fpage>|<lpage>', '', ln)  # change page tag
            ln = re.sub(r'<fpage>', '<page>', ln)  # change page tag
            ln = re.sub(r'</lpage>', '</page>', ln)  # change page tag
            ln = preproc(ln)
            ln = ln.split()
            l = -1  # no tag is open
            w = ln[0]
            a, b, l = findtag(w, l)
            train_label.append([b])

            for i in range(1, len(ln)):
                # add the +2 word
                w = ln[i]
                a, b, l = findtag(w, l)
                train_label[len(train_label) - 1].extend([b])
            tmpn, tmpd, tmpl, tmpa, tmpw, tmpg = dist_tags(train_label[len(train_label) - 1])
            ntag.append(tmpn)
            dtag.append(tmpd)
            ltag.append(tmpl)
            atag.append(tmpa)
            wtag.append(tmpw)
            gtag.append(tmpg)
        file.close()

    llen = []  # line length
    tlen = []  # length in terms of token

    for refld_file in os.listdir(refld_folder):
        counter += 1
        progress_bar.goto(int(counter / 2))
        with open(os.path.join(refld_folder, refld_file)) as file:
            reader = file.read()
        reader = re.sub(r'\.[0]+e\+00\r\n', '', reader)
        x = re.findall('12*3*', reader)
        [llen.append([len(t)]) for t in x]
        with open(os.path.join(lyt_dir, refld_file)) as file:
            reader2 = file.read()
        reader2 = reader2.split('\r\n')
        tmp0 = re.finditer('12*3*', reader)
        tmp = [(m.start(0), m.end(0)) for m in tmp0]
        for uu in tmp:
            tlen.append(
                [sum([len((y.split('\t')[0]).split()) for y in reader2[uu[0]:uu[1] + 1]])])  # number of token per ref

    kde_ltag = KernelDensity(kernel='gaussian', bandwidth=1).fit(ltag)
    kde_ntag = KernelDensity(kernel='gaussian', bandwidth=0.5).fit(ntag)
    kde_dtag = KernelDensity(kernel='gaussian', bandwidth=1).fit(dtag)
    kde_atag = KernelDensity(kernel='gaussian', bandwidth=0.5).fit(atag)
    kde_wtag = KernelDensity(kernel='gaussian', bandwidth=0.5).fit(wtag)
    kde_gtag = KernelDensity(kernel='gaussian', bandwidth=1).fit(gtag)
    kde_llen = KernelDensity(kernel='gaussian', bandwidth=1).fit(llen)
    kde_tlen = KernelDensity(kernel='gaussian', bandwidth=1).fit(tlen)

    def dump_pickle(file_name, lng, obj):
        file_path = os.path.join(model_dir, f"{file_name}_{lng}.pkl")
        with open(file_path, 'wb') as fid:
            pickle.dump(obj, fid)

    dump_pickle("kde_ntag", "de", kde_ntag) # kde_dtag
    dump_pickle("kde_ntag", "en", kde_ntag)
    dump_pickle("kde_ltag", "de", kde_ltag) # kde_ltag
    dump_pickle("kde_ltag", "en", kde_ltag)
    dump_pickle("kde_dtag", "de", kde_dtag) # kde_dtag
    dump_pickle("kde_dtag", "en", kde_dtag)
    dump_pickle("kde_atag", "de", kde_atag) # kde_atag
    dump_pickle("kde_atag", "en", kde_atag)
    dump_pickle("kde_wtag", "de", kde_wtag) # kde_wtag
    dump_pickle("kde_wtag", "en", kde_wtag)
    dump_pickle("kde_gtag", "de", kde_gtag) # kde_gtag
    dump_pickle("kde_gtag", "en", kde_gtag)
    dump_pickle("kde_wtag", "de", kde_wtag) # kde_wtag
    dump_pickle("kde_wtag", "en", kde_wtag)
    dump_pickle("kde_llen", "de", kde_llen) # kde_llen
    dump_pickle("kde_llen", "en", kde_llen)
    dump_pickle("kde_tlen", "de", kde_tlen) # kde_tlen
    dump_pickle("kde_tlen", "en", kde_tlen)

    """
    original code: 
    # with open('Utils/kde_ltag.pkl', 'wb') as fid:
    #     pickle.dump(kde_ltag, fid)
    with open('Utils/kde_ntag' + sfx + '.pkl', 'wb') as fid:
        pickle.dump(kde_ntag, fid)
    # with open('Utils/kde_dtag.pkl', 'wb') as fid:
    #     pickle.dump(kde_dtag, fid)
    with open('Utils/kde_atag' + sfx + '.pkl', 'wb') as fid:
        pickle.dump(kde_atag, fid)
    with open('Utils/kde_wtag' + sfx + '.pkl', 'wb') as fid:
        pickle.dump(kde_wtag, fid)
    # with open('Utils/kde_gtag.pkl', 'wb') as fid:
    #     pickle.dump(kde_gtag, fid)
    with open('Utils/kde_llen.pkl', 'wb') as fid:
        pickle.dump(kde_llen, fid)
    with open('Utils/kde_tlen.pkl', 'wb') as fid:
        pickle.dump(kde_tlen, fid)
    
    """

