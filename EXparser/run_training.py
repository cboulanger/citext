import subprocess, traceback

def pipe_stdout(proc):
    for line in proc.stdout:
        print(line.strip())

def _call_extraction_training():
    try:
        proc = subprocess.Popen(['python /app/EXparser/Feature_Extraction.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
        proc = subprocess.Popen(['python /app/EXparser/Txt2Vec.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
        proc = subprocess.Popen(['python /app/EXparser/Training_Ext.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
    except:
        print(traceback.format_exc())


def _call_segmentation_training():
    try:
        proc = subprocess.Popen(['python /app/EXparser/Feature_Extraction.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
        proc = subprocess.Popen(['python /app/EXparser/Txt2Vec.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
        proc = subprocess.Popen(['python /app/EXparser/Training_Seg.py'], stdout=subprocess.PIPE, shell=True)
        pipe_stdout(proc)
    except:
        print(traceback.format_exc())
