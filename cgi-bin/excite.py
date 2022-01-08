#!/usr/bin/env python3

import json, os, cgi, shutil, subprocess, io, sys, tempfile

print("Content-type: application/json")
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
refs_dict_dir = data_dir + "/3-refs_seg_dict/"
refs_prob_dir = data_dir + "/3-refs_seg_prob/"
refs_bibtex_dir = data_dir + "/3-refs_seg_bibtex/"
result_path = ""

result = {}

try:
    if command is None:
        raise RuntimeError("No command")
    if filename is None and command != "train_extraction":
        raise RuntimeError("No filename")

    if command == "layout":
        # remove .gitkeep because cermine cannot deal with it
        gitkeep_file = pdf_dir + ".gitkeep"
        try:
            os.remove(gitkeep_file)
        except:
            pass
        try:
            source = tempfile.gettempdir() + "/" + filename + ".pdf"
            target = pdf_dir + filename + ".pdf"
            shutil.move(source, target)
        except FileNotFoundError as err:
            raise RuntimeError(str(err))
        finally:
            # restore .gitkeep file
            open(gitkeep_file, 'a').close()

        cleanup.append(pdf_dir + filename + ".pdf")
        result_path = layout_dir + filename + ".csv"

    elif command == "exparser":
        result_path = refs_dir + filename + ".csv"
        cleanup.append(result_path)
        cleanup.append(refs_dict_dir + filename + ".csv")
        cleanup.append(refs_prob_dir + filename + ".csv")
        cleanup.append(refs_bibtex_dir + filename + ".csv")

    elif command == "segmentation":
        try:
            source = tempfile.gettempdir() + "/" + filename + ".csv"
            target = refs_dir + filename + ".csv"
            shutil.move(source, target)
            #cleanup.append(target)
        except FileNotFoundError as err:
            raise RuntimeError(str(err))
        result_path = refs_seg_dir + filename + ".xml"
        cleanup.append(result_path)
        cleanup.append(refs_dict_dir + filename + ".csv")
        cleanup.append(refs_prob_dir + filename + ".csv")
        cleanup.append(refs_bibtex_dir + filename + ".csv")

    elif command == "train_extraction":
        result_path = None

    else:
        raise RuntimeError("Invalid command: " + command)

    # only call docker command if file doesn't already exist
    if result_path is None or not os.path.isfile(result_path):
        # run docker command and write output to server output
        args = ['docker', 'run', '--rm', '-v' + os.getcwd() + ':/app', 'excite_toolchain', command]
        sys.stderr.write(" ".join(args) + "\n")
        tsk = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        # check for process completion and copy output to stderr
        last_line = ""
        return_code = 0
        while True:
            return_code = tsk.poll()
            if return_code is not None: break
            line = str(tsk.stdout.readline())
            if line.strip() != "":
                last_line = line.strip()
            sys.stderr.write(line)

        # subprocess returned with error
        if return_code != 0:
            raise RuntimeError(last_line)

    if result_path is None:
        result["success"] = True

    else:
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
        try:
            os.remove(filepath)
        except OSError:
            pass








