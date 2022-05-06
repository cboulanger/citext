from progress.bar import Bar

def get_progress_bar(task, max):
    progressbar = Bar(task, bar_prefix=' [', bar_suffix='] ', empty_fill='_',
                      suffix='%(index)d/%(max)d',
                      max=max)
    return progressbar
