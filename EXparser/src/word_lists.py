import os
from configs import *

list_dir = config_lists_dir()

def read_csv(filename):
    path = os.path.join(list_dir, filename)
    # check for local override
    if os.path.isfile(path + ".local.csv"):
        path += ".local"
    with open(path + ".csv", "r", encoding="utf-8") as file:
        return file.readlines()


# read word lists into variables

stopw = r'\b' + (r'\b|\b'.join(read_csv("stopwords"))) + r'\b' # todo: use from nlp module according to language
wl_names = set(read_csv("names"))
wl_abbrev = set(read_csv("abv"))
wl_cities = set(read_csv("cities"))
wl_editors = set(read_csv("edt")) # not used, editors can reuse names
wl_journals = set(read_csv("journals"))
wl_publishers = set(read_csv("publishers"))

word_lists = [wl_names, wl_abbrev, wl_cities, wl_editors, wl_journals, wl_publishers]
