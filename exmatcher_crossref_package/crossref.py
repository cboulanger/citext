# -*- coding: utf-8 -*-
import time
from habanero import Crossref
from configs import *
import pandas as pd
import glob
import re
import sys
import numpy as np
import string
import json
import binascii
import datetime
import traceback
import bibtexparser
import os.path #from pathlib import Path
# from cologne_phonetics import *
# import exmatcher_crossref_package.cologne_phonetics as cologne_phonetics
sys.path.insert(0, config_url_venu() +'exmatcher_crossref_package/')
import cologne_phonetics as cologne_phonetics


# #### Read files and preprocess
def read_file(bibtex_file):
    lines = []
    with open(bibtex_file, 'r', encoding='utf-8') as bf:
        for line in bf:
            lines.append(line)
    return lines


def convert_to_valid_ref_dict(js):
    key_list = list(js.keys())
    new_json = {}
    for key in key_list:
        if key in ['year', 'volume', 'page']:
            val = ""
            if len(js[key]) >= 1:
                for entry in js[key]:
                     if 'value' in entry:
                         val += entry['value']+ " "
            new_json[key] = val.strip()
        elif key == 'title':
            title_str = ""
            for word in js[key]:
                if 'value' in word:
                    title_str += word['value']+" "
            new_json[key] = title_str.strip()
        elif key == 'author':
            authors_list = []
            for aut in js[key]:
                single_aut = ""
                for entry in aut:
                    if 'surname' in entry:
                        single_aut += entry['surname']+" "
                    if 'given-names' in entry:
                        single_aut += entry['given-names']+" "
                authors_list.append(single_aut.strip())
            new_json[key] = ', '.join(authors_list)
        elif key == 'other':
            continue
        elif key == 'source':
            val = ""
            if len(js[key]) >= 1:
                for entry in js[key]:
                     if 'value' in entry:
                        val += entry['value']+ " "
            new_json["journal"] = val.strip()
    return new_json


def get_bibtex_dictionary(str_file):
    s = bibtexparser.loads(str_file)
    rs = s.entries[0]
    if 'source' in rs:
        rs['journal'] = rs['source'].copy()
    return rs


# #### call crossref API
def crossref_api(input_string, e_mail):
    cr = Crossref()
    result = ""
    try:
        x = cr.works(query =input_string, limit=1, select ="DOI,title,issued,short-container-title,ISSN,score,URL,title,page,publisher,container-title,DOI,author,volume,issued")
        result = x["message"]["items"][0]
    except:
        print("error")
        result = None
        return None
    return json.dumps(result)


# #### functions for comparison of bibtex and crossref 
def normauthors_alg(item):
    normalizedtitle = "".join(l for l in item if l not in string.punctuation)
    normalizedtitle = normalizedtitle.lower()
    normalizedtitle = normalizedtitle.replace(" ", "")

    normalizedtitle=normalizedtitle.replace(u'ü', '')
    normalizedtitle=normalizedtitle.replace(u'ä', '')
    normalizedtitle=normalizedtitle.replace(u'ö', '')
    normalizedtitle=normalizedtitle.replace(u'ß', 'ss')
    normalizedtitle =''.join([i if ord(i) < 128 else '' for i in normalizedtitle])
    return normalizedtitle


def Author_title(title,author):
    normalizedtitle = "".join(l for l in title if l not in string.punctuation)
    normalizedtitle = normalizedtitle.lower()
    normalizedtitle = normalizedtitle.replace(" ", "")
    normalizedtitle=normalizedtitle.replace(u'ü', 'u')
    normalizedtitle=normalizedtitle.replace(u'ä', 'a')
    normalizedtitle=normalizedtitle.replace(u'ö', 'o')
    normalizedtitle=normalizedtitle.replace(u'ß', 'ss')
    normalizedtitle =''.join([i if ord(i) < 128 else '' for i in normalizedtitle])

    if isinstance(author, list):
        new_autors = ','.join(l for l in author)
    else:
        new_autors = author
    norm_authors=[]
    for item in new_autors.split(','):
        norm_authors.append(normauthors_alg(item.strip()))
    return normalizedtitle, norm_authors


def normalize_input(title,author):
        temprec = {}
        ntitles, norm_authors = Author_title(title,author)
        temprec["norm_title_str"] = ntitles
        temprec["author"] = norm_authors
        return temprec


def get_shingles(text, n):
    """
    Get integer representation of each shingle of a
    text string
    @param text:    The text from which you want to get the represenation
    @param n:       The n for ngrams zou want to use
    """
    text = "" if type(text) is float else text
    return list({str_to_nr(text[max(0, p):p+n]) for
                 p in range(1-n, len(text))})


def hash_int(shingles, coeff):
    temresult=[]
    temresult.append(next_prime + 1)
    for s in shingles:
        cal=(coeff[0] * s + coeff[1]) % next_prime
        temresult.append(int(cal))
    return min(temresult)


def Crossrefdoiextractor(text):
        dictcross=json.loads(text)
        if len(dictcross)>0:
            if "DOI" in dictcross.keys():
                return dictcross["DOI"]
            else:
                return np.nan
        else:
            return np.nan


def str_to_nr(text):
    return binascii.crc32(bytes(text)) & 0xffffffff


def DistJaccard(list1, list2):
    str1 = set(list1)
    str2 = set(list2)
    return float(len(str1 & str2)) / len(str1 | str2)


def author_crossref(text):
        ls_aut=[]
        dictcross=json.loads(text)
        if len(dictcross)>0:
            if "author" in dictcross.keys():
                for item in dictcross["author"]:
                    if 'family' in item.keys():
                        ls_aut.append(item['family'])
            else:
                return np.nan
        else:
            return np.nan
        strtext=""
        if len(ls_aut):
            for item in ls_aut:
                if strtext=="":
                    pass
                else:
                    strtext=strtext+","
                strtext=strtext+item
        else:
            return np.nan
        testtitle=""
        testauthor=strtext
        Ref_norm=normalize_input(testtitle,testauthor)
        return Ref_norm['author']


def journal_crossref(text):
    ls_title = []
    dictcross = json.loads(text)
    if len(dictcross) > 0:
        if "container-title" in dictcross.keys():
            for item in dictcross["container-title"]:
                ls_title.append(item)
        else:
            return np.nan
    else:
        return np.nan
    ls_normtitle = []
    for item in ls_title:
        testtitle = item
        testauthor = ""
        Ref_norm = normalize_input(testtitle, testauthor)
        ls_normtitle.append(Ref_norm['norm_title_str'])
    return ls_normtitle


def norm_journal(text):
    testauthor=""
    testtitle=[text]
    ls_normjournal = []
    if pd.isnull(text) or len(text) == 0:
        return np.nan

    for title in testtitle:
        t, a = Author_title(title,testauthor)
        #Ref_norm=normalize_input(testtitle,testauthor)
        #Exctie_journal=Ref_norm["norm_title_str"]
        ls_normjournal.append(t)
    result = "".join(ls_normjournal)
    if len(result.strip()) > 0:
        return result
    else:
        return np.nan


def jaccard_journal(df):
    if pd.isnull(df.iloc[0]["journals_norm"]):
        return 0
    if type(df.iloc[0]["crossref_journal"]) == np.float64:
        if pd.isnull(df.iloc[0]["crossref_journal"]):
            return 0

    if len(df.iloc[0]["crossref_journal"]) > 0:
        if pd.isnull(df.iloc[0]["crossref_journal"][0]):
            return 0
    else:
        return 0

    list_titlecrossref=df.iloc[0]["crossref_journal"][0]
    Exctie_journal=df.iloc[0]["journals_norm"]

    if len(Exctie_journal)<1  or len(list_titlecrossref)<1:
        return 0
    else:
        try:
            lsminhashscore=[]
            for item in list_titlecrossref:
                lsminhashscore.append(DistJaccard(get_shingles(Exctie_journal,3),get_shingles(item,3)))

        except Exception as e:
                print (str(e))
                print ("\n")
                traceback.print_exc(file=sys.stdout)
                print("================")
        if len(lsminhashscore) > 0:
            return max(lsminhashscore)
        else: return 0


def title_crossref(text):
        ls_title=[]
        dictcross=json.loads(text)
        if len(dictcross)>0:
            if "title" in dictcross.keys():
                for item in dictcross["title"]:
                        ls_title.append(item)
            else:
                return np.nan
        else:
            return np.nan
        ls_normtitle=[]
        for item in ls_title:
            testtitle=item
            testauthor=""
            Ref_norm=normalize_input(testtitle,testauthor)
            ls_normtitle.append(Ref_norm['norm_title_str'])
        return ls_normtitle


def filter_year(list_date):
    now = datetime.datetime.now()
    currentyear=now.year
    currentyear=int(currentyear)
    ls_year=[]
    for date in list_date:
        for year in date:
            try:
                if int(year)>1200:
                    if int(year)==currentyear or currentyear>int(year):
                        ls_year.append(year)
                else:
                    pass
            except:
                pass
    return ls_year


def crossref_year(text):
        dictcross=json.loads(text)
        if len(dictcross)>0:
            if "issued" in dictcross.keys():
                if 'date-parts' in dictcross["issued"]:
                    lsyearfilter=filter_year(dictcross["issued"]["date-parts"])
                    if len(lsyearfilter)>0:
                        return lsyearfilter
                    else:
                         return np.nan
                else:
                    return np.nan
            else:
                return np.nan
        else:
                return np.nan


def jaccard_titles(df):
    if len(df["crossref_title"]) > 0:
        list_titlecrossref=df["crossref_title"][0]
        testtitle=df["title"]
        testauthor=""
        Ref_norm=normalize_input(testtitle,testauthor)
        Exctie_title=Ref_norm["norm_title_str"]
        try:
            lsminhashscore=[]
            for item in list_titlecrossref:
                lsminhashscore.append(DistJaccard(get_shingles(Exctie_title,3),get_shingles(item,3)))


        except Exception as e:
                print (str(e))
                print ("\n")
                traceback.print_exc(file=sys.stdout)
                print("================")
        if len(lsminhashscore) > 0:
            return max(lsminhashscore)
        else: return 0
    else:
        return 0


def checkyear(Year_item):
    if pd.isnull(Year_item):
        return np.nan
    listofyear=[]
    for itemyis in Year_item.split(" "):
        matches = re.findall(r'.*([1-3][0-9]{3})', itemyis)
        for e in matches:
            listofyear.append(int(e))
    if len(listofyear) > 0:
        return listofyear
    else:
        return np.nan


def intersectyear(a):
    anb = set(a['clean_year']) & set(a['crossref_year'])
    if anb:
        return True
    else:
        return False


def intersectaut(a):
    anb = set(a['norm_aut']) & set(['crossref_author'])
    if anb:
        return True
    else:
        return False


def intersectaut_cologne(a):
    anb = set(a['cr_aut_cologne']) & set(['aut_cologne'])
    if anb:
        return True
    else:
        return False


def intersectvolume_numbers(a):
    anb = set(a['volume_numbers']) & set(a['crossref_volume'])
    if anb:
        return True
    else:
        return False


def intersectpages(a):
    anb = set(a["crossref_page"]) & set(a["pages"])
    if anb:
        return True
    else:
        return False


def normalise_pages(page):
    results = [int(i) for i in re.findall(r'\d+', str(page))]
    return results


def normalise_crossref_pages(text):
    dictcross = json.loads(text)
    pages = []
    if len(dictcross) > 0:
        if "page" in dictcross.keys():
            page_str = dictcross["page"]
            pages = [int(i) for i in re.findall(r'\d+', str(page_str))]
    return pages


def normalise_crossref_volume(text):
    dictcross = json.loads(text)
    vol = []
    if len(dictcross) > 0:
        if "volume" in dictcross.keys():
            vol_str = dictcross["volume"]
            vol = [int(i) for i in re.findall(r'\d+', str(vol_str))]
    return vol


def compare_page_numbers(t_pages, cr_pages):
    return len(set(t_pages).intersection(cr_pages)) > 0


def extracted_aut(text):
    if pd.isnull(text):
        return np.nan
    testtitle=""
    testauthor=text
    Ref_norm=normalize_input(testtitle,testauthor)
    return Ref_norm["author"]


def make_cologne_phono(input_str):
    if type(input_str) == list:
        result_list = []
        for element in input_str:
            phono = cologne_phonetics.encode(element)[0][1]
            result_list.append(phono)
        return result_list
    else:
        return np.nan


def calcu_sim(joined_table):
    crossrefvalue = joined_table
    crossrefvalue["crossrefdoi"] = np.nan
    crossrefvalue["checkdoi"] = np.nan
    crossrefvalue["crossref_author"] = np.nan
    crossrefvalue["journals_norm"] = np.nan
    crossrefvalue["crossref_title"] = np.nan
    crossrefvalue["crossref_journal"] = np.nan
    crossrefvalue["crossref_year"] = np.nan
    crossrefvalue["crossref_len_title"] = np.nan
    crossrefvalue["jaccard_score_title"] = np.nan
    crossrefvalue["journal_score_85"] = np.nan
    crossrefvalue["clean_year"] = np.nan
    crossrefvalue["yearscore"] = np.nan
    crossrefvalue["norm_aut"] = np.nan
    crossrefvalue["autscore"] = np.nan
    crossrefvalue["autscore"] = np.nan
    crossrefvalue["autscore"] = np.nan
    crossrefvalue["title_score_85"] = np.nan
    crossrefvalue["final_score_yta"] = np.nan
    crossrefvalue["checkdoi"] = np.nan
    crossrefvalue["jaccard_score_journal"] = np.nan
    crossrefvalue["jaccard_score_title"] = np.nan
    crossrefvalue["crossrefdoi"] = crossrefvalue["crossref"].apply(Crossrefdoiextractor)
    crossrefvalue["author_cologne_phonetic"] = np.nan
    crossrefvalue["crossref_author_cologne_phonetic"] = np.nan
    crossrefvalue["autscore_intersect"] = np.nan
    crossrefvalue["autscore_cologne"] = np.nan


    crossrefvalue["crossrefdoi"]=crossrefvalue["crossref"].apply(Crossrefdoiextractor)

    checkdoi=crossrefvalue[~crossrefvalue["crossrefdoi"].isnull()][~crossrefvalue["doi"].isnull()]

    checkdoi["checkdoi"]=checkdoi["crossrefdoi"]==checkdoi["doi"]

    crossrefvalue["checkdoi"]=checkdoi["checkdoi"]

    # --- extract author  ---

    crossrefvalue["crossref_author"]=crossrefvalue["crossref"].apply(author_crossref)

    # --- extract title  ---
    crossrefvalue["crossref_title"]=crossrefvalue["crossref"].apply(title_crossref)

    #  --- extract journal  ---
    crossrefvalue["journals_norm"] = crossrefvalue['journal'].apply(norm_journal)
    crossrefvalue["crossref_journal"] = crossrefvalue["crossref"].apply(journal_crossref)

    # --- extract year  ---

    crossrefvalue["crossref_year"]=crossrefvalue["crossref"].apply(crossref_year)

    crossrefvalue["crossref_len_title"]=crossrefvalue[~crossrefvalue["crossref_title"].isnull()]["crossref_title"].apply(len)

    #data1 = pd.read_csv('list_of_coeeff.csv')

    # --- calculate jaccard ---
    cross_title = crossrefvalue[~crossrefvalue["crossref_title"].isnull()][~crossrefvalue["title"].isnull()]

    crossrefvalue["jaccard_score_title"]=jaccard_titles(cross_title)
    crossrefvalue["title_score_85"]=crossrefvalue["jaccard_score_title"]>=0.85

    crossrefvalue["jaccard_score_journal"] = jaccard_journal(crossrefvalue)
    crossrefvalue["journal_score_85"] = crossrefvalue["jaccard_score_journal"] >=0.85

    # --- check pages

    crossrefvalue['pages'] =crossrefvalue["pages"].apply(normalise_pages)
    crossrefvalue['volume'] = crossrefvalue['volume'].apply(normalise_pages)
    crossrefvalue['numbers'] = crossrefvalue['numbers'].apply(normalise_pages)
    crossrefvalue['volume_numbers'] = crossrefvalue['volume'] + crossrefvalue['numbers']

    crossrefvalue['crossref_page'] = crossrefvalue["crossref"].apply(normalise_crossref_pages)
    crossrefvalue['crossref_volume'] = crossrefvalue["crossref"].apply(normalise_crossref_volume)

    crossrefvalue["pagescore"] = crossrefvalue.apply(intersectpages, axis=1)
    crossrefvalue["volumescore"] = crossrefvalue.apply(intersectvolume_numbers, axis=1)

    # --- check year ---c

    crossrefvalue["clean_year"]=crossrefvalue["year"].apply(checkyear)
    crossrefvalue["yearscore"]=np.nan
    crossrefvalue["yearscore"]=crossrefvalue[~crossrefvalue["clean_year"].isnull()][~crossrefvalue["crossref_year"].isnull()].apply(intersectyear, axis=1)

    crossrefvalue["norm_aut"]=crossrefvalue["author"].apply(extracted_aut)
    crossrefvalue["autscore"] = np.nan
    crossrefvalue["author_cologne_phonetic"] = crossrefvalue["norm_aut"].apply(make_cologne_phono)
    crossrefvalue["crossref_author_cologne_phonetic"] = crossrefvalue["crossref_author"].apply(make_cologne_phono)
    crossrefvalue["autscore_intersect"] = crossrefvalue[~crossrefvalue["norm_aut"].isnull()][
        ~crossrefvalue["crossref_author"].isnull()].apply(intersectaut, axis=1)
    crossrefvalue["autscore_cologne"] = crossrefvalue[~crossrefvalue["crossref_author_cologne_phonetic"].isnull()][
        ~crossrefvalue["author_cologne_phonetic"].isnull()].apply(intersectaut, axis=1)
    crossrefvalue["autscore"] = crossrefvalue['autscore_intersect'] | crossrefvalue['autscore_cologne']

    crossrefvalue["yearscore"]=crossrefvalue["yearscore"].fillna(False)
    crossrefvalue["title_score_85"]=crossrefvalue["title_score_85"].fillna(False)
    crossrefvalue["final_score_yta"]= (crossrefvalue["autscore"] &  crossrefvalue["title_score_85"]) | (crossrefvalue["yearscore"] &  crossrefvalue["title_score_85"])
    crossrefvalue["checkdoi"]=crossrefvalue["checkdoi"].fillna(False)

    crossrefvalue["jaccard_score_journal"] = crossrefvalue["jaccard_score_journal"].fillna(0)
    crossrefvalue["jaccard_score_title"] = crossrefvalue["jaccard_score_title"].fillna(0)

    # --- shrink dataframe
    shrinked_crossvalue = crossrefvalue[['autscore', 'yearscore',
                                         'checkdoi', 'jaccard_score_title','title_score_85',
                                         'jaccard_score_journal','journal_score_85',
                                         'pagescore', 'volumescore', 'crossref']]

    #return shrinked_crossvalue

    return crossrefvalue


# #### Get Queries for matching
def get_query_by_threshold(dataframe, measure, value):
    dataframe.rename(columns={dataframe.columns[0]: 'query'}, inplace=True)
    col_name = ''
    if measure == 'r':
        col_name = 'avg_recall'
    elif measure == 'p':
        col_name = 'avg_precision'
    elif measure == 'f':
        col_name = 'fmeasure'

    dataframe["fmeasure"] = 2 * (dataframe["avg_recall"] * dataframe["avg_precision"]) / (
            dataframe["avg_recall"] + dataframe["avg_precision"])
    results = dataframe.loc[dataframe[col_name] >= float(value)]
    results.sort_values(['avg_precision', "fmeasure"], ascending=False, inplace=True)
    return results[['query', 'avg_recall', 'avg_precision', 'fmeasure']]


def generate_sets(tuple_str):
    return list(filter(None, "".join(tuple_str.split()).strip('(').strip(')').split(',')))


def intersection(lst1, lst2):
    return len((set(lst1) & set(lst2)))


def select_duplicates(df):
    for index, row in df.iterrows():
        value = row['query']
        if row['duplicate'] == False:
            for ind, row_two in df.iterrows():
                if index != ind:
                    comp_value = row_two['query']
                    if intersection(comp_value, value) == len(value):
                        df.at[ind, 'duplicate'] = True


def shrink_table(csv_file, measure='p', threshold = 0.8):
    csv_df = pd.read_csv(csv_file, encoding='utf-8')
    df = get_query_by_threshold(csv_df, measure, threshold)
    df['query'] = df['query'].apply(generate_sets)
    df['duplicate'] = False
    df.index = df['query'].str.len()
    df = df.sort_index(ascending=True).reset_index(drop=True)
    select_duplicates(df)
    df = df[df["duplicate"] == False]
    df = get_query_by_threshold(df, measure, threshold)
    return df


# ### Match queries with results
def convert_to_list(s):
    return list(filter(None, "".join(s.split()).strip('{').strip('}').split(',')))


def compare_match_with_query(match, query_df, whole_crossref=False):
    # maps column names of table query_precision_ha to column names of table  match_results_ha
    column_mapping = {'author': 'autscore',
                      'year': 'yearscore',
                      'doi': 'checkdoi',
                      'title': 'title_score_85',
                      'journal': 'journal_score_85',
                      'pages': 'pagescore',
                      'volume': 'volumescore',
                      'number': 'volumescore'}

    possiblities = ['author', 'doi', 'journal', 'number', 'pages', 'title', 'year']
    for ind, row in query_df.iterrows():
        query = row['query']
        max_positives = len(query)
        number_of_positives = 0
        for p in query:
            if p in column_mapping:
                match_col_name = column_mapping[p]
                if match is not None and match_col_name is not None:
                        if match[str(match_col_name)] is not None:
                            if match[str(match_col_name)].bool() == True:
                                number_of_positives += 1

        if number_of_positives == max_positives:
            cr_dict = json.loads(match.iloc[0]['crossref'])
            cr_doi = cr_dict['DOI'] if 'DOI' in cr_dict else ""

            if whole_crossref:
                crossref_json = json.dumps(cr_dict)
                result_tuple = (crossref_json, cr_doi, query)
            else:
                result_tuple = (cr_doi, query)
            return result_tuple

    return np.nan


def calc_crossref(input_dict, query_df, whole_crossref, email=None, ):
    results = calc_crossref_similarity(input_dict, query_df, email, whole_crossref)
    return results


def calc_crossref_similarity(input_dict, query_df, e_mail, whole_crossref):
    result_df = []
    comp_output = []
    if 'ref_bib' in input_dict and input_dict['ref_bib'] is not None:
        if 'ref_text_x' in input_dict and input_dict['ref_text_x'] is not None:
            reftext = input_dict['ref_text_x']
            crossref_output = crossref_api(reftext, e_mail)
            if crossref_output is not None:
                if len(crossref_output) > 0:
                    temp_crossref = json.loads(crossref_output)
                    if 'title' not in temp_crossref:
                        temp_crossref['title'] = [reftext]
                        crossref_output = json.dumps(temp_crossref)
                    pd_series_from_dict = pd.Series(input_dict['ref_bib'])
                    df2 = pd.DataFrame(columns=['author', 'title', 'journal', 'doi', 'year', 'publisher', 'pages', 'volume','numbers', 'crossref'])
                    df2 = df2.append(pd_series_from_dict,  ignore_index=True)
                    df2['crossref'] = crossref_output
                    df2['ref_string'] = reftext
                    df2 = df2.fillna(np.nan)
                    rs = calcu_sim(df2)
                    result_df.append(rs)
                else:
                    result_df.append(None)
            else:
                 result_df.append(None)
        else:
            result_df.append(None)
    else:
        result_df.append(None)

    if len(result_df) > 0:
        for entry in result_df:
            comp_output.append(compare_match_with_query(entry, query_df, whole_crossref))
    return comp_output[0]