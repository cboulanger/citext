from configs import *

logf = open(config_url_venu() + 'tmp/logfile.log', "w")

def log(msg):
    logf.write(msg + "\n")
