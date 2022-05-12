from configs import *

logf = open(config_url_log(), "w")

def log(msg):
    logf.write(msg + "\n")
