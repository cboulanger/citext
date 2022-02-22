from configs import *

logf = open(config_url_venu() + 'logfile.log', "a")

def log(msg):
    logf.write(msg)
