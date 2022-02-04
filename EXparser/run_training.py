import subprocess, traceback


def _call_extraction_training():
    try:
        proc = subprocess.Popen(['python /app/EXparser/Feature_Extraction.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)

        proc = subprocess.Popen(['python /app/EXparser/Txt2Vec.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)

        proc = subprocess.Popen(['python /app/EXparser/Training_Ext.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)
    except:
        print(traceback.format_exc())


def _call_extraction_segmentation():
    try:
        proc = subprocess.Popen(['python /app/EXparser/Feature_Extraction.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)

        proc = subprocess.Popen(['python /app/EXparser/Txt2Vec.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)

        proc = subprocess.Popen(['python /app/EXparser/Training_Seg.py'], stdout=subprocess.PIPE, shell=True)
        (output, err) = proc.communicate()
        print(output)
    except:
        print(traceback.format_exc())
