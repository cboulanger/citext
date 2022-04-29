import sys, os, json, requests, re
import urllib.parse


# get data from DNB authority files via lobid.org
def get_lobid_data(filter: dict):
    dnb_api_url = "http://lobid.org/gnd/search?filter="
    filter_string = " and ". join([f'{key}:"{filter[key]}"' for key in filter])
    data_url = dnb_api_url + urllib.parse.quote(filter_string) + "&format=jsonl"
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
    return entries


def make_publishers_list():
    entries = get_lobid_data({
        "broaderTermInstantial.id": "https://d-nb.info/gnd/4063004-3" # = Publisher
    })
    with open('EXparser/Lists/publishers.csv', 'w') as file:
        for i in range(len(entries)):
            entries[i] = re.sub(r'\([^)]+\)','', entries[i]).strip()
        entries = list(dict.fromkeys(entries))
        entries.sort()
        file.write('\n'.join(entries).strip())
    del entries

def make_journals_list():
    entries = get_lobid_data({
        "broaderTermInstantial.id": "https://d-nb.info/gnd/4016222-9" # == Academic Journal
    })
    with open('EXparser/Lists/journals-gnd.csv', 'w') as file:
        entries = list(dict.fromkeys(entries))
        entries.sort()
        file.write('\n'.join(entries).strip())
    del entries

#make_publishers_list()

#make_journals_list()
