import os
from lib.utils import run_command
from configs import *


def call_run_layout_extractor(input_dir=None, output_dir=None):
    os.chdir(config_url_venu())
    command = 'java -jar cermine.layout.extractor-0.0.1-jar-with-dependencies.jar '
    command += f'{input_dir or config_url_pdfs()} {output_dir or config_url_Layouts()} 90000000'
    run_command(command)
