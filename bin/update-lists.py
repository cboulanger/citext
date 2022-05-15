#! bin/env python3

import sys, os, json, requests, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import urllib.parse
from configs import *
from EXparser.src.word_lists import stopw

# get data from DNB authority files via lobid.org
def get_lobid_data(filter: dict):
    dnb_api_url = "http://lobid.org/gnd/search?filter="
    filter_string = " and ". join([ key + ':"' + filter[key] + '"' for key in filter])
    data_url = dnb_api_url + urllib.parse.quote(filter_string) + "&format=jsonl"
    print("Querying data from " + data_url)
    r = requests.get(data_url, allow_redirects=True)
    content = r.text
    entries = []
    for jsondata in content.split('\n'):
        if not jsondata: continue
        data = json.loads(jsondata)
        entries.append(data['preferredName'].lower())
        variants = data['variantName'] if 'variantName' in data else []
        for variant in variants:
            entries.append(variant.lower())
    print("Retrieved " + str(len(entries)) + " entries")
    return entries

def make_word_list(entries:list):
    words = []
    for entry in entries:
        entry_words = [ word.strip(",.-'\"()") for word in entry.split(" ") if len(word) > 3 and not re.match(r'[0-9]{2,}', word) ]
        words.extend([ word for word in entry_words if word not in words])
    words.sort()
    return [ word for word in words if word not in stopw]


def make_publishers_list():
    entries = get_lobid_data({
        "broaderTermInstantial.id": "https://d-nb.info/gnd/4063004-3" # = Publisher
    })
    for i in range(len(entries)):
        entries[i] = re.sub(r'\([^)]+\)', '', entries[i]).strip()
    entries = list(dict.fromkeys(entries))
    word_list = make_word_list(entries)
    with open(os.path.join(config_lists_dir(), 'publishers.csv'), 'w') as file:
        file.write('\n'.join(word_list).strip())

def make_journals_list():
    entries = get_lobid_data({
        "broaderTermInstantial.id": "https://d-nb.info/gnd/4067488-5" # == Academic Journal
    })
    entries = list(dict.fromkeys(entries))
    word_list = make_word_list(entries)
    with open(os.path.join(config_lists_dir(), 'journals.csv'), 'w') as file:
        file.write('\n'.join(word_list).strip())

if __name__ == '__main__':
    print("Creating word list of journal titles...")
    make_journals_list()
    print("Creating word list of publisher names...")
    make_publishers_list()

