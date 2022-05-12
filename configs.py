import os
from enum import Enum

venue_address = '/app/' if os.path.isdir('/app/') else os.path.dirname(os.path.abspath(__file__))
data_address = venue_address + '/Data/'

version = "0.2.0"


def get_version():
    return version


def config_url_venu():
    return venue_address


def config_url_data():
    return data_address


def config_url_log():
    return os.path.join(config_tmp_dir(), 'logfile.log')


def config_dirname_pdfs_no_ocr():
    return '0-pdfs_no_ocr/'


def config_url_pdfs_no_ocr():
    return os.path.join(data_address, config_dirname_pdfs_no_ocr())


def config_dirname_pdfs():
    return '1-pdfs/'


def config_url_pdfs():
    return os.path.join(data_address, config_dirname_pdfs())


def config_dirname_layouts():
    return '2-layouts/'


def config_url_Layouts():
    return os.path.join(data_address, config_dirname_layouts())


def config_dirname_refs():
    return '3-refs/'


def config_url_Refs():
    return os.path.join(data_address, config_dirname_refs())


def config_dirname_refs_seg():
    return '3-refs_seg/'


def config_url_Refs_segment():
    return os.path.join(data_address, config_dirname_refs_seg())


def config_dirname_bibtex():
    return '3-refs_bibtex/'


def config_url_Refs_bibtex():
    return os.path.join(data_address, config_dirname_bibtex())


def config_dirname_seg_prob():
    return '3-refs_seg_prob/'


def config_url_Refs_segment_prob():
    return os.path.join(data_address, config_dirname_seg_prob())


def config_dirname_seg_dict():
    return '3-refs_seg_dict/'


def config_url_Refs_segment_dict():
    return os.path.join(data_address, config_dirname_seg_dict())


def config_dirname_crossref():
    return '4-refs_crossref/'


def config_url_Refs_crossref():
    return os.path.join(data_address, config_dirname_crossref())


def config_url_exmatcher_crossref_package():
    return venue_address + 'exmatcher_crossref_package/'


def email_address():
    return 'azam.hosseini@gesis.org'


def config_url_layout_extractor():
    return venue_address + 'cermine-layout-extractor/'


def config_layout_extractor_function_name():
    return 'gesis.cermine.layout.extractor.CermineLineLayoutExtractor'


def config_data_dirnames():
    return [
        config_dirname_pdfs_no_ocr(),
        config_dirname_pdfs(),
        config_dirname_layouts(),
        config_dirname_refs(),
        config_dirname_refs_seg(),
        config_dirname_seg_prob(),
        config_dirname_seg_dict(),
        config_dirname_bibtex(),
        config_dirname_crossref()
    ]


def config_url_git_repo():
    return "https://github.com/cboulanger/excite-docker"


def config_exparser_dir(version=None):
    if version:
        return os.path.join(config_tmp_dir(), os.path.basename(config_url_git_repo()) + "-" + version)
    return os.path.join(venue_address, "EXparser")


def config_exparser_version_file():
    return os.path.join(config_tmp_dir(), "exparser-version.txt")


def config_dataset_dir():
    return os.path.join(venue_address, "Dataset")


def config_model_dir():
    return os.path.join(venue_address, "Models")


def config_lists_dir():
    return os.path.join(venue_address, "Lists")


def config_tmp_dir():
    return os.path.join(venue_address, "tmp")


class DatasetDirs(Enum):
    FEATURES = "Features"
    LAYOUT = "LYT"
    TRAIN_LYT = "LRT"
    REFLD = "RefLD"
    TRAIN_SEG = "SEG"
    TEST_LYT = "TEST_LYT"
    TEST_REFS = "TEST_REFS"
    TEST_SEG = "TEST_SEG"
