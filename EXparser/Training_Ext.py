import random, os, re, sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
from sklearn.cluster import KMeans
from lib.logger import log
from lib.pogressbar import get_progress_bar
from configs import *


def vec2crfeat(vec, prefix):
    feat = {}
    [feat.update({prefix + 'f' + str(i): vec[i], }) for i in range(len(vec))]
    return feat


def row_count(filename):
    with open(filename) as in_file:
        return sum(1 for row in in_file)


def train_extraction(dataset_dir: str, model_dir: str):
    idxx = np.load(os.path.join(config_exparser_dir(), 'idxx.npy'))

    # Training
    FS = np.empty((0, 50 * 3), float)  # feature space
    SM = np.empty((0, 1), float)  # feature space
    lyt_dir = os.path.join(dataset_dir, DatasetDirs.LYT.value)
    lyt_files = os.listdir(lyt_dir)
    total = len(lyt_files)
    counter = 0
    progress_bar = get_progress_bar("Extraction training", total)
    log("Extraction training...")
    for u in range(total):
        counter += 1
        progress_bar.goto(counter)
        curr_file = lyt_files[u]
        if curr_file.startswith(".") or not curr_file.endswith(".csv"):
            continue
        log(f" - {curr_file}")
        try:
            fpath = os.path.join(dataset_dir, "Features", curr_file)
            with open(fpath) as file:
                reader = str(file.read())
        except FileNotFoundError:
            errmsg = fpath + " does not exist, skipping..."
            sys.stderr.write('\n' + errmsg + '\n')
            log(errmsg)
            continue
        reader = re.sub(r'[\r\n]+', '\r', reader)
        reader = reader.split('\r')
        reader = reader[0:-1] if len(reader) > 0 and reader[-1] == '' else reader
        try:
            fpath = os.path.join(dataset_dir, DatasetDirs.REFLD.value, curr_file)
            with open(fpath) as file:
                reader2 = str(file.read())
        except FileNotFoundError:
            errmsg = fpath + " does not exist, skipping..."
            sys.stderr.write('\n' + errmsg + '\n')
            log(errmsg)
            continue
        reader2 = re.sub(r'[\r\n]+', '|', reader2)
        reader2 = reader2.split('|')
        reader2 = reader2[0:-1] if len(reader2) > 0 and reader2[-1] == '' else reader2

        Fs = np.empty((0, 50 * 3), float)  # feature space
        Sm = np.empty((0, 1), float)  # feature space
        for uu in range(len(reader)):
            try:
                row2 = reader2[uu]
                r_2 = int(float(row2[0]))
                Sm = np.append(Sm, [[r_2]], 0)
                row = reader[uu]
                r = np.array(row.split(' ')).astype(float)
                if uu == 0:
                    r1 = np.array(reader[uu + 1].split(' ')).astype(float)
                    r2 = np.array([0] * 65)
                elif uu == (len(reader) - 1):
                    r1 = np.array([0] * 65)
                    r2 = np.array(reader[uu - 1].split(' ')).astype(float)
                else:
                    r1 = np.array(reader[uu + 1].split(' ')).astype(float)
                    r2 = np.array(reader[uu - 1].split(' ')).astype(float)
                r = r[idxx]
                r1 = r1[idxx]
                r2 = r2[idxx]
                r = np.concatenate((r, r1, r2))
                Fs = np.append(Fs, [r], 0)
            except IndexError:
                continue

        Fs[np.isinf(Fs)] = 1
        # Uncomment for Normalisation
        # Fs=np.transpose([(x-min(x))/(max(x)-min(x)) for x in np.transpose(Fs)])
        Fs[np.isnan(Fs)] = 1

        tmp = Fs[np.where(Sm == 0)[0]]
        n_clus = min([len(tmp) - 1, 8 * (len(Fs) - len(tmp))])
        if n_clus < 1:
            n_clus = 1
        kmeans = KMeans(n_clusters=n_clus).fit(tmp)
        Fs = Fs[np.where(Sm != 0)[0]]
        Sm = Sm[np.where(Sm != 0)[0]]
        tmp2 = kmeans.labels_
        Fs = np.append(Fs, [tmp[tmp2 == x][0] for x in range(max(tmp2) + 1)], 0)
        Sm = np.append(Sm, [[0]] * len(kmeans.cluster_centers_), 0)

        FS = np.append(FS, Fs, 0)
        SM = np.append(SM, Sm, 0)
    progress_bar.finish()

    SM = np.transpose(SM)[0]
    # balance the data (random over sampling)
    P1 = sum(SM == 1)  # number of positives =1
    P2 = sum(SM == 2)  # number of positives =2
    P3 = sum(SM == 3)  # number of positives =3
    N = sum(SM == 0)  # number of negatives
    tmp = np.asarray([i for i, c in enumerate(SM) if c == 0])
    tmp1 = np.asarray([i for i, c in enumerate(SM) if c == 1])
    tmp2 = np.asarray([i for i, c in enumerate(SM) if c == 2])
    tmp3 = np.asarray([i for i, c in enumerate(SM) if c == 3])
    tmp4 = max([P1, P2, P3])
    tmp0 = [random.randint(0, len(tmp) - 1) for x in range(tmp4)]
    tmp = tmp[tmp0]
    tmp0 = [random.randint(0, len(tmp1) - 1) for x in range(tmp4 - len(tmp1))]
    tmp1 = np.concatenate((tmp1, tmp1[tmp0]), axis=0)
    tmp0 = [random.randint(0, len(tmp2) - 1) for x in range(tmp4 - len(tmp2))]
    tmp2 = np.concatenate((tmp2, tmp2[tmp0]), axis=0)
    tmp0 = [random.randint(0, len(tmp3) - 1) for x in range(tmp4 - len(tmp3))]
    tmp3 = np.concatenate((tmp3, tmp3[tmp0]), axis=0)
    FSN = np.concatenate((FS[tmp], FS[tmp1], FS[tmp2], FS[tmp3]), axis=0)
    SMN = np.concatenate((SM[tmp], SM[tmp1], SM[tmp2], SM[tmp3]), axis=0)
    FSN[np.isinf(FSN)] = 1
    np.save(model_dir + '/FSN.npy', FSN)
    np.save(model_dir + '/SMN.npy', SMN)
    # Uncomment for Non-considering I-Line
    # FSN=np.delete(FSN,np.where(SMN==2)[0],0)
    # SMN=np.delete(SMN,np.where(SMN==2)[0])
    clf1 = RandomForestClassifier(n_estimators=500)
    clf1.fit(FSN, SMN)
    # save the classifier
    with open(os.path.join(model_dir, 'rf.pkl'), 'wb') as file:
        pickle.dump(clf1, file)

# train_extraction()
