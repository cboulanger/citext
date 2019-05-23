venue_address = '/app/'
data_address = '/app/Data/'

def config_url_venu():
    return venue_address

def config_url_log():
    return venue_address + '/logfile.log'

def config_url_pdfs():
    return data_address +'1-pdfs/'

def config_url_Layouts():
    return data_address +'2-layouts/'

def config_url_Refs():
    return data_address +'3-refs/'
    
def config_url_Refs_segment():
    return data_address + '3-refs_seg/'

def config_url_Refs_bibtex():
    return data_address + '3-refs_bibtex/'

def config_url_Refs_segment_prob():
    return data_address + '3-refs_seg_prob/'

def config_url_Refs_segment_dict():
    return data_address + '3-refs_seg_dict/'

def config_url_Refs_crossref():
    return data_address + '4-refs_crossref/'

def config_url_exmatcher_crossref_package():
    return venue_address +'exmatcher_crossref_package/' 

def email_address():
    return 'azam.hosseini@gesis.org'

def config_url_layout_extractor():
    return venue_address + 'cermine-layout-extractor/'

def config_layout_extractor_function_name():
    return 'gesis.cermine.layout.extractor.CermineLineLayoutExtractor'