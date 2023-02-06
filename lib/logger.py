import logging
import os
import socket

from dotenv import load_dotenv
from configs import config_url_log

load_dotenv()

def setup_papertrail(host, port):
    from logging.handlers import SysLogHandler
    class ContextFilter(logging.Filter):
        hostname = socket.gethostname()

        def filter(self, record):
            record.hostname = ContextFilter.hostname
            return True

    syslog = SysLogHandler(address=(host, port))
    syslog.addFilter(ContextFilter())
    format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
    formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
    syslog.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(syslog)


def log(msg):
    log_file.write(msg + "\n")


log_file = open(config_url_log(), "w")

if os.environ.get('PAPERTRAIL_HOST'):
    setup_papertrail(os.environ.get('PAPERTRAIL_HOST'), int(os.environ.get('PAPERTRAIL_PORT')))

logger = logging.getLogger()
level = os.environ.get('LOG_LEVEL') or 'INFO'
logger.setLevel(getattr(logging, level))
