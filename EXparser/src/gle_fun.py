# -*- coding: UTF-8 -*- 
# Definition: general function for extraction and segmentation

import os

list_dir = '/app/EXparser/Lists'

def read_csv(filename):
    path = os.path.join(list_dir, filename)
    # check for local override
    if os.path.isfile(path + ".local.csv"):
        path += ".local"
    with open(path + ".csv", "r", encoding="utf-8") as file:
        return file.readlines()


# read word lists into variables
stopw = r'\b' + (r'\b|\b'.join(read_csv("stopwords"))) + r'\b'
b1 = set(read_csv("names"))
b2 = set(read_csv("abv"))
b3 = set(read_csv("cities"))
b4 = set(read_csv("edt"))
b5 = set(read_csv("journals"))
b6 = set(read_csv("publishers"))


# make text lower
def textlow(ln):
    # string method that converts a string to a case-insensitive form following
    # an algorithm described by the Unicode Standard
    return ln.casefold()
