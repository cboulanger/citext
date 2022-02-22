import builtins
from progress.bar import Bar
from configs import *
from lib.logger import log

# This will reformat output that has the form ">task:index/total:additional_text_for_logfile"
# as a progress bar by monkey-patching the print command (quick & dirty, ad-hoc implementation).

progressbar = None
currtask = ""
oldprint = builtins.print
total = len(os.listdir(config_url_pdfs()))
index = 0

def progress_disable():
    builtins.print = oldprint

def progress_print(string="", end="\n", file=None):
    global progressbar, currtask, oldprint, total, index

    progress_disable()
    if string.startswith(">") or string.startswith("processing"):
        if string.startswith(">"):
            task, progress, *_ = string[1:].split(":")
            index, total = progress.split("/")
        else:
            task = "Extracting layout features"
            index = index + 1
        if not progressbar or task != currtask:
            if progressbar:
                progressbar.finish()
            currtask = task
            progressbar = Bar(task, bar_prefix=' [', bar_suffix='] ', empty_fill='.',
                              suffix='%(index)d/%(max)d: %(eta_td)s remaining...',
                              max=int(total))
        progressbar.goto(int(index))
        if int(index) == int(total):
            total = None
            index = 0
            progressbar.finish()
    elif string.startswith("Used memory is megabytes"):
        # ignore cermine output
        pass
    else:
        if progressbar:
            progressbar.finish()
            progressbar = None
            total = None
            index = 0
        print(string, end = end)
    log(string + end)
    progress_enable()

def progress_enable():
    builtins.print = progress_print
