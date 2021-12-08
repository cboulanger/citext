#!/usr/bin/python3

# for debugging only
import cgitb
cgitb.enable();
print("Content-type: text/html")

import json, os, cgi, shutil, subprocess, io, sys

#print("Content-type: application/json")
print()

data_dir     = os.getcwd() + "/Data"

form     = cgi.FieldStorage()
command  = form.getvalue("command")
filename = form.getvalue("file") # without extension!

cleanup = []
pdf_dir      = data_dir + "/1-pdfs/"
layout_dir   = data_dir + "/2-layouts/"
refs_dir     = data_dir + "/3-refs/"
refs_seg_dir = data_dir + "/3-refs_seg/"
result_path = ""

result = {}

try:
    if command is None:
        raise RuntimeError("No command")
    if filename is None:
        raise RuntimeError("No filename")

    if command == "layout":
        try:
            shutil.move("/tmp/" + filename + ".pdf", pdf_dir + filename + ".pdf")
        except FileNotFoundError as err:
            raise RuntimeError(str(err))

        cleanup.append(pdf_dir + filename + ".pdf")
        result_path = layout_dir + filename + ".csv"

    elif command == "exparser":
        # references
        result_path = refs_dir + filename + ".csv"
        #cleanup.append(result_path)

    elif command == "segmentation":
        result_path = refs_seg_dir + filename + ".xml"
        # cleanup.append(result_path)

    else:
        raise RuntimeError("Invalid command: " + command)

    # only call docker command if file doesn't already exist
    if not os.path.isfile(result_path):
        # run docker command and write output to server output
        args = ['docker', 'run', '--rm', '-v' + os.getcwd() + ':/app', 'excite_toolchain', command]
        sys.stderr.write(" ".join(args) + "\n")
        tsk = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        while tsk.poll() is None:
            line = str(tsk.stdout.readline())
            sys.stderr.write(line)

    # return result of excite command
    try:
        result_file = io.open(result_path, mode="r", encoding="utf-8")
        result["success"] = result_file.read()
        result_file.close()

    except Exception as err:
        raise RuntimeError(str(err))

except RuntimeError as err:
    result["error"] = str(err)

except BaseException as err:
    import traceback
    traceback.print_exc()
    result["error"] = str(err)

finally:
    # return result
    print(json.dumps(result))

    # clean up temporary files
    for filepath in cleanup:
        os.remove(filepath)








