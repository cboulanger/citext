# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from configs import *
# from exmatcher_crossref_package.crossref import *
sys.path.insert(0, config_url_venu() +'exmatcher_crossref_package/')
from crossref import *
import json, ast
import pprint


# matching references from a file with crossref API.
def crossref_from_file(bibtex_ref_lines, query_df):
    """
    calculate crossref from a file
    @param:     bibtex_ref_lines    List of strings, containing json dumps of references
    @param:     query_df            pandas dataframe with feature combinations like (author, title). Is used for matching
    """
    list_of_results = []
    for ind, element in enumerate(bibtex_ref_lines):
        result_dict = {}
        temp_dict = json.loads(element)

        input_dict = {}
        input_dict['ref_bib'] = get_bibtex_dictionary(temp_dict['ref_bib'])
        input_dict['ref_text_x'] = temp_dict['ref_text_x']
        rs = calc_crossref(input_dict, query_df, whole_crossref, email)
        result_dict['ref_string'] = temp_dict['ref_text_x']

        if type(rs) == tuple:
            if whole_crossref:
                result_dict['crossref'] = rs[0]

            result_dict['doi'] = rs[0]
            result_dict['fields'] = rs[1]

        else:
            if whole_crossref:
                result_dict['crossref'] = None
            result_dict['doi'] = None
            result_dict['fields'] = None
        list_of_results.append(result_dict.copy())

    with open ("results.csv","w") as rf:
        for e in list_of_results:
            json_result = json.dumps(e)
            #print (json_result)
            rf.write(json_result)
            rf.write("\n")


def crossref_from_json(ref_json, ref_text, email=None, whole_crossref=False):
    """
        calculate crossref from a file
        @param:     ref_json            json string: contains a reference as a dictionary. Used for matching with crossref.
        @param:     ref_text            reference string. Used to call crossref api with.
        @param:     email               E-mail address for Crossref API. Status reports are sent to that address, if someting goes wrong with the API call. Can be None.
        @param:     whole_crossref      if set to True, functions also returns whole crossref output. If false (default), functions returns only the DOI of matched crossref result
    """
    result_dict = {}
    query_file = config_url_venu() + 'exmatcher_crossref_package/precision_00_dict_main.csv'
    query_df = shrink_table(query_file)

    ref_dict = json.loads(ref_json)

    input_dict = {
        'ref_bib': convert_to_valid_ref_dict(ref_dict),
        'ref_text_x': ref_text
    }
    rs = calc_crossref(input_dict, query_df, whole_crossref, email)
    result_dict['ref_string'] = ref_text

    if type(rs) == tuple:
        if whole_crossref:
            result_dict['crossref'] = rs[0]
            result_dict['doi'] = rs[1]
            result_dict['fields'] = rs[2]
        else:
            result_dict['doi'] = rs[0]
            result_dict['fields'] = rs[1]
    else:
        if whole_crossref:
            result_dict['crossref'] = None
        result_dict['doi'] = None
        result_dict['fields'] = None

    return result_dict


def crossref_json_main():
    csv_file = "listofreftex_prosses-segmented-20180702-2.csv"
    df = pd.read_csv(csv_file)
    for ind, row in df.iterrows():
        ref_text = row['ref_text']
        json_str = row['ref_seg_dic']
        crossref_results = crossref_from_json(json_str, ref_text)
        pprint.pprint(crossref_results)
        print ("\n")


# path to csv with feature combinations
# query_file = config_url_venu() + 'exmatcher_crossref_package/precision_00_dict_main.csv'
# function reads csv with feature combinations into dataframe.
# query_df = shrink_table(query_file)


# # path, where csv with references is located
# input_path = 'C:/Users/akyuerhr/Desktop/Crossref_from_JSON/exmatcher_crossref_package/'

# # first argument of python script call is retrieved. Argument should contain file name of references csv.
# file_name = sys.argv[1]

# # E-mail address for Crossref API. Status reports are sent to that address, if someting goes wrong with the API call
# email = None

# # if set to True, functions return whole crossref output. If false (default), functions returns only the DOI of matched crossref result
# whole_crossref = False

# # reads  strings with references, from a csv, into a list.
# bibtex_ref_lines = read_file(input_path+file_name)

# crossref_from_file(bibtex_ref_lines, query_df)

file_name = sys.argv[1]
# subfolder_name = sys.argv[2]

print(file_name)
f = open(config_url_Refs_segment_dict() + file_name , 'r')
x = f.readlines()
i = 0 
list_of_results = []
result_dict = {}
for item in x:
    try:
        # print (i)
        temp_dic = ast.literal_eval(item)
        ref_seg_dic = temp_dic['ref_seg_dic']
        ref_text_x = temp_dic['ref_text_x']
        # print('*' *100)
        # print(ref_seg_dic)
        # print('*' *100)
        # print(ref_text_x.encode("utf-8"))
        
        crossref_results  = crossref_from_json(json.dumps(ref_seg_dic), ref_text_x, email_address(), False)
        result_dict = crossref_results
        result_dict['ref_string'] = ref_text_x
        # result_dict["Crossref_id"] = []
        # result_dict["probib"] = []
        # print('*' *100)
        # print(result_dict)
        list_of_results.append(result_dict.copy())
    except:
        print(traceback.format_exc())
        logf.write('File Name: %s \n' %(filename))
        logf.write(traceback.format_exc())
        logf.write('*' * 50 + '\n')
    i+= 1

with open (config_url_Refs_crossref() + file_name,"w") as rf:
    for e in list_of_results:
        json_result = json.dumps(e)
        #print (json_result)
        rf.write(json_result)
        rf.write("\n")