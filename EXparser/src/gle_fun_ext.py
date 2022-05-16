# General functions for extraction
#
# TODO rename functions to make clearer what they acutally do
# TODO move hardcoded language strings into configurable lists

import regex as re
import numpy as np
from .word_lists import *

def get_cc(ln):  # [1]
    """
    Returns ratio of capital characters per line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\p{Lu}]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    cc = 1.0 * len(tmp) / len(ss)
    return cc


def get_sc(ln):  # [2]
    """
    Return ration of lower-case letters per line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\p{Ll}]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    sc = 1.0 * len(tmp) / len(ss)
    return sc


def get_cw(ln):  # [3]
    """
    Returns ration of capital characters per line
    :param ln:
    :return:
    """
    tmp = re.findall(
        r'(?u)\b[\{Lu}][\p{L}]+\b', ln)
    if (len(ln.split()) != 0):
        cw = 1.0 * len(tmp) / len(ln.split())
    else:
        cw = 0
    return cw


def get_sw(ln):  # [4]
    """
    Returns ratio of words starting with a lower-case letter, per number of words in a line
    :param ln:
    :return:
    """
    tmp = re.findall(
        r'(?u)\b[\p{Ll}][\p{L}]+\b', ln)
    if (len(ln.split()) != 0):
        sw = 1.0 * len(tmp) / len(ln.split())
    else:
        sw = 0
    return sw


def get_yr_re(ln):  # [5]
    """
    Returns 1 if the line contains a year between 1000 and 2099, otherwise 0
    :param ln:
    :return:
    """
    yr = re.findall(r'1[8-9]{1}[0-9]{2}|20[0-2]{1}[0-9]{1}', ln)
    yr = int(bool(yr))
    return yr


def get_qm(ln):  # [6]
    """
    Returns the ratio of opening and closing punctuation such as "|“|”|‘|’|«|», per non-whitespace characters in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\p{Pi}\p{Pf}]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    qm = 1.0 * (len(tmp)) / len(ss)
    return qm


def get_cl(ln):  # [7]
    """
    Returns the ratio of colons, per non-whitespace characters in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^:]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    cl = 1.0 * len(tmp) / len(ss)
    return cl


def get_sl(ln):  # [8]
    """
    Returns the number of forward or backward slashes, per non-whitespace character in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\\|/]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    sl = 1.0 * len(tmp) / len(ss)
    return sl


def get_bs(ln):  # [9,10]
    """
    Returns the ratio of opening and closing brackets of any kine, per non-whitespace character in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\p{Ps}\p{Pe}]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    bs = 1.0 * len(tmp) / len(ss)
    return bs


def get_dt(ln) -> float:  # [11]
    """
    Returns the ration of periods/dots per non-whitespace charactes in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\.]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    dt = 1.0 * len(tmp) / len(ss)
    return dt


def get_cm(ln):  # [12]
    """
    Returns the ration of commas per non-whitespace charactes in a line
    :param ln:
    :return:
    """
    tmp = re.sub(r'[^\,]', '', ln)
    ss = re.sub(r'[\s\b\t]+', '', ln)
    if len(ss) == 0:
        return 0
    cm = 1.0 * len(tmp) / len(ss)
    return cm


def get_cd_re(ln):  # [13]   re=reference extraction
    """
    Returns the ratio of abbreviated first names ("J." Doe), per words in a line
    :param ln:
    :return:
    """
    tmp = re.findall(r'(?<![\p{L}\p{N}])([\p{Lu}][.]){1,2}(?![\p{L}\p{N}])', ln)
    if (len(ln.split()) != 0):
        cd = 1.0 * len(tmp) / len(ln.split())
    else:
        cd = 0
    return cd


def get_lh(ln, bins, alh):  # [14]
    """
    TODO document, something with word length
    :param ln:
    :param bins:
    :param alh:
    :return:
    """
    # bins=[0,3,6,8,12,np.inf]      # it is important to note that the ranges are: from 0 to 3, from 3 to 6 and so on
    tmp = map(len, ln.split())
    tmp2 = [np.argmin(abs(np.array(bins) - x)) for x in tmp]
    lh = np.array([tmp2.count(x) for x in range(len(bins))])

    if sum(lh) == 0:
        return lh, lh

    lh2 = 1.0 * lh / sum(lh)
    lh = [x for _, x in sorted(zip(alh, lh), reverse=True)]
    lh = 1.0 * np.array(lh) / sum(lh)
    return lh, lh2


def get_ch(ln, bins, ach):  # [15]
    """
    TODO document
    :param ln:
    :param bins:
    :param ach:
    :return:
    """
    tmp = np.asarray([i for i, c in enumerate(ln) if c.isupper()]) + 1
    if len(tmp) <= 1:
        tmp = [1, 1]
    tmp = [x - tmp[i - 1] for i, x in enumerate(tmp)][1:]
    # bins=[0,3,6,8,12,np.inf]      # it is important to note that the ranges are: from 0 to 3, from 3 to 6 and so on
    tmp2 = [np.argmin(abs(np.array(bins) - x)) for x in tmp]
    ch = np.array([tmp2.count(x) for x in range(len(bins))])
    ch2 = 1.0 * ch / sum(ch)
    ch = [x for _, x in sorted(zip(ach, ch), reverse=True)]
    ch = 1.0 * np.array(ch) / sum(ch)
    return ch, ch2


def get_pg_re(ln):  # [16]   re=reference extraction
    """
    TODO document
    :param ln:
    :return:
    """
    tmp = re.findall(r'[0-9]+[^0-9\.\(\)\[\]\{\}]+[0-9]+', ln)
    pg = int(bool(tmp))
    return pg


def get_hc(hp, cl):  # [17]
    """
    TODO document
    :param hp:
    :param cl:
    :return:
    """
    hc = (float(hp) - cl[0]) / (cl[1] - cl[0])
    return hc


def get_pb(pb, cl):  # [18]
    """
    TODO document
    :param pb:
    :param cl:
    :return:
    """
    pb = 1.0 * pb / cl
    return pb


def get_wc(wd, cl):  # [19]
    """
    TODO document
    width class
    :param wd:
    :param cl:
    :return:
    """
    wc = (float(wd) - cl[0]) / (cl[1] - cl[0])
    return wc


def get_spl(sp, pl):  # [19]
    """
    width class
    TODO document
    :param sp:
    :param pl:
    :return:
    """
    sc = (float(sp) - pl[0]) / (pl[1] - pl[0])
    return sc


def get_ll(ln, bins):  # [1bis]
    """
    length of lines in term of characters (histogram)
    :param ln:
    :param bins:
    :return:
    """
    tmp = len(re.sub(r'\s', '', ln))
    ll = (float(tmp) - bins[0]) / (bins[1] - bins[0])
    return ll


def get_llw(ln, bins):  # [2bis]
    """
    length of lines in term of words (histogram)
    :param ln:
    :param bins:
    :return:
    """
    tmp = len(ln.split())
    llw = (float(tmp) - bins[0]) / (bins[1] - bins[0])
    return llw


def get_lv(lv, lvg):  # [3bis]
    """
    the position of the line in terms of the entire file
    :param lv:
    :param lvg:
    :return:
    """
    lv = 1.0 * lv / lvg
    return lv


def get_lex1_re(ln):  # [20]
    """
    Returns 1 if the line contains a token indicating that a referenced text is contained in
    a container ("source") reference ("xx, in: YY"), otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(r'[ ]+(In[:]*|in:)[ ]*', ln)  # to be checked
    lex1 = int(bool(tmp))
    return lex1


def get_lex2_re(ln):  # [21]
    """
    Returns 1 if the line contains a token indicating an editor (e.g. "Hrsg", "eds"), otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(r'Hg\.|Hrsg\.|[eE]d[s]*\.', ln)
    lex2 = int(bool(tmp))
    return lex2


def get_lex3_re(ln):  # [22]
    """
    Returns 1 if the line contains a token indicating a publisher (e.g. "verlag", "press"), otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(
        r'(verlag)|(press)|(universit(y|ät))|(publi(cation[s]*|shing|sher[s]*))|(book[s]*)|(intitut[e]*)',
        ln.casefold())
    lex3 = int(bool(tmp))
    return lex3


def get_lex4_re(ln):  # [23]
    """
    Returns 1 if the line contains "&"
    :param ln:
    :return:
    """
    tmp = re.findall(r'\&', ln)
    lex4 = int(bool(tmp))
    return lex4


def get_lex5_re(ln):  # [24]
    """
    Returns 1 if the line contains "Journal" (???)
    :param ln:
    :return:
    """
    tmp = re.findall(r'Journal', ln)
    lex5 = int(bool(tmp))
    return lex5


def get_lex6_re(ln):  # [25]   re=reference extraction
    """
    Returns 1 if the line contains a token indicating a volume
    :param ln:
    :return:
    """
    tmp = re.findall(r'[Bb]d\.|[Bb]and', ln)
    lex6 = int(bool(tmp))
    return lex6


def get_vol_re(ln):  # [*2]   #is vol.   re=reference extraction
    """
    Returns 1 if the line contains a token indicating a volume, otherwise 0
    TODO should be merged with get_lex6_re()
    :param ln:
    :return:
    """
    tmp = re.findall(r'[Vv]ol\.|[Jj]g\.', ln)
    vol = int(bool(tmp))
    return vol


def get_lex7_re(ln):  # [26]
    """
    Returns 1 if the line contains a token indicating page numbers, otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(r'S\.|PP\.|pp\.|ss\.|SS\.|[Pp]ages[\.]', ln)
    lex7 = int(bool(tmp))
    return lex7


def get_lnk_re(ln):  # [*1]
    """
    Returns 1 if the line contains an internet link, otherwise 0
    :param ln:
    :return:
    """
    # tmp=re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ln)
    tmp = re.findall(
        r'(http://|ftp://|https://|www\.)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', ln)
    lnk = int(bool(tmp))
    return lnk


def get_und_re(ln):  # [*2]
    """
    Returns 1 if the line contains a token indicating "and", otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(r'[\b\s]u\.[\b\s]|[\s]*and[\s]*|[\s]*und[\s]*', ln)
    und = int(bool(tmp))
    return und


def get_amo_re(ln):  # [*2]
    """
    Returns 1 if the line contains a token indicating "among others", otherwise 0
    TODO improve regex, add English
    :param ln:
    :return:
    """
    tmp = re.findall(
        r'[^\p{L}\p{N}]u\.a\.[^\p{L}\p{N}]',
        ln)
    amo = int(bool(tmp))
    return amo


def get_num_re(ln):  # [*2]
    """
    Returns 1 if the line contains a token indicating "number", otherwise 0
    :param ln:
    :return:
    """
    tmp = re.findall(r'[Nn][ro][\.\:]*', ln)
    num = int(bool(tmp))
    return num


def vector_from_word_lists(ln):
    """
    Given a
    :param words:
    :return:
    """
    a = [0] * len(word_lists)
    words = [ word for word in ln.casefold().split(" ") if len(word) > 3 and word not in stopw ]
    nw = len(words)
    if nw > 0:
        for (i, word_list) in enumerate(word_lists):
            for word in words:
                if word.strip(",.()'\"") in word_list:
                    a[i] = a[i] + 1
            a[i] = 1.0 * a[i] / nw
    return a


def get_index(ln):
    """
    TODO document
    :param ln:
    :return:
    """
    tmp = re.findall(r'^([\[]*[0-9][\.\)\]]*[\s\b\t ]+)', ln)
    tmp1 = re.findall(r'^([\p{Lu}]+[\p{Ll}])', ln)
    if bool(tmp):
        idx = 1
    elif bool(tmp1):
        idx = 1
    else:
        idx = 0
    return idx


def check_literature(row, rfidx, u):
    """
    TODO checks if the row contains the title of the bibliography section, what does the return value mean?
    :param ln:
    :return:
    """
    # textlow of ln and last reference index and current position
    x = re.findall(r'literatur[e]*|references|bibliografie|bibliography|referenz|verweise', row[0].casefold())
    y = re.findall(r'Bold|Italic', row[6].split('+')[-1])
    x = x[0] if bool(x) else ''
    if ((len(x) > 0) & ((len(row[0]) - len(x)) <= 6) & bool(y)):
        rfidx[0] = u
        rfidx[2] = row[6].split('+')[-1]
        rfidx[3] = round(float(row[3]), 2)
    elif ((rfidx[1] < rfidx[0]) & (len(re.sub(r'[^\p{L}]*', '', row[0])) > 5)):  # find the next title after literatur
        c1 = ((rfidx[2] == row[6].split('+')[-1]) & (rfidx[3] == round(float(row[3]), 2)))
        c2 = (bool(re.findall(r'Bold', row[6].split('+')[-1])))
        if (c1 | c2):  # either they have same font and size or different size but both bolds
            rfidx[1] = u
    return rfidx


def get_pos_lit(rfidx, u):
    """
        TODO document
        :param ln:
        :return:
        """
    if rfidx[0] == 0:
        pdx = 0
    elif u <= rfidx[0]:
        pdx = -1
    else:
        pdx = 1
    if ((u > rfidx[1]) & (rfidx[1] > rfidx[0])):
        pdx = -1
    return pdx


def min_ver_dist(vsl, pvsl, nvsl):
    """
    TODO minimal vertical distance (between what?)
    :param vsl:
    :param pvsl:
    :param nvsl:
    :return:
    """
    pd = vsl - pvsl if pvsl != 0 else -1
    pd = 500 if pd < 0 else pd
    nd = nvsl - vsl if nvsl != 0 else -1
    nd = 500 if nd < 0 else nd
    mspl = min([pd, nd])
    return mspl


def get_ffm(fm, ffm):
    """
    TODO document
    :param vsl:
    :param pvsl:
    :param nvsl:
    :return:
    """
    list_fmm = list(ffm)
    if len(list_fmm) == 0:
        return -1, 0
    if fm in list_fmm[0]:
        ff = list_fmm[0].index(fm)
    else:
        ff = -1
    tmp = int(bool(re.findall(r'Bold', fm)))
    tmp1 = int(bool(re.findall(r'Italic', fm)))
    fbi = tmp + tmp1
    # fbi=tmp
    return ff, fbi
