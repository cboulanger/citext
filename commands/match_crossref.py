import sys, importlib, json, ast, traceback
from configs import *
from lib.crossref import *
from lib.logger import log
from lib.pogressbar import get_progress_bar

def crossref_from_json(ref_json, ref_text, email=None, whole_crossref=False):
    """
        calculate crossref from a file
        @param:     ref_json            json string: contains a reference as a dictionary. Used for matching with crossref.
        @param:     ref_text            reference string. Used to call crossref api with.
        @param:     email               E-mail address for Crossref API. Status reports are sent to that address, if someting goes wrong with the API call. Can be None.
        @param:     whole_crossref      if set to True, functions also returns whole crossref output. If false (default), functions returns only the DOI of matched crossref result
    """
    result_dict = {}
    query_file = config_url_exmatcher_crossref_package() + 'precision_00_dict_main.csv'
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

def match_with_crossref(file_name):
    with open(os.path.join(config_url_refs_segment_dict(), file_name)) as f:
        lines = f.readlines()
    i = 0
    list_of_results = []
    for item in lines:
        try:
            temp_dic = ast.literal_eval(item)
            ref_seg_dic = temp_dic['ref_seg_dic']
            ref_text_x = temp_dic['ref_text_x']
            result_dict  = crossref_from_json(json.dumps(ref_seg_dic), ref_text_x, email_address(), False)
            result_dict['ref_string'] = ref_text_x
            list_of_results.append(result_dict.copy())
        except Exception as result:
            sys.stderr.write(f"{file_name}:{i}: {str(result)}")
        i+= 1

    with open(os.path.join(config_url_refs_crossref(), file_name), "w") as rf:
        for result in list_of_results:
            json_result = json.dumps(result)
            rf.write(json_result + '\n')

def execute(input_base_dir=None):
    dir_path = os.path.join(input_base_dir or data_address, config_dirname_seg_dict())
    files = os.listdir(dir_path)
    total = len(files)
    progress_bar = get_progress_bar("Matching with Crossref", total)
    log("Matching with crossref...")
    for i, file_name in enumerate(files):
        progress_bar.goto(i+1)
        if file_name.startswith(".") or not file_name.endswith(".csv"):
            continue
        log(f" - {file_name}")
        try:
            match_with_crossref(file_name)
        except Exception as e:
            sys.stderr.write(f"\n{str(e)}\n")
            log(traceback.format_exc())
    progress_bar.finish()
