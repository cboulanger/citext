import os
from enum import Enum

venue_address = '/app/' if os.path.isdir('/app/') else os.path.dirname(os.path.abspath(__file__))
data_address = venue_address + '/Data/'

version = "2.0"


def get_version():
    return version


def config_url_log():
    return os.path.join(config_tmp_dir(), 'logfile.log')


def config_dataset_dir(model_name=None):
    if model_name:
        return os.path.join(config_dataset_dir(), model_name)
    return os.path.join(venue_address, "Dataset")


def config_model_dir():
    return os.path.join(venue_address, "Models")


def config_tmp_dir():
    return os.path.join(venue_address, "tmp")


class DatasetDirs(Enum):
    FINDER = "finder"
    PARSER = "parser"
