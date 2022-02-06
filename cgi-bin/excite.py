#!/usr/bin/env python3

import json, os, cgi, shutil, subprocess, io, sys, tempfile, time

print("Content-type: application/json")
print()

form = cgi.FieldStorage()
command = form.getvalue("command")
filename = form.getvalue("file") # without extension!

data_dir = os.getcwd() + "/Data"
pdfs_no_ocr_dir = data_dir + "/0-pdfs_no_ocr/"
pdfs_dir = data_dir + "/1-pdfs/"
layout_dir = data_dir + "/2-layouts/"
refs_dir = data_dir + "/3-refs/"
refs_seg_dir = data_dir + "/3-refs_seg/"
refs_dict_dir = data_dir + "/3-refs_seg_dict/"
refs_prob_dir = data_dir + "/3-refs_seg_prob/"
refs_bibtex_dir = data_dir + "/3-refs_seg_bibtex/"
result_path = None

# remove .gitkeep because cermine cannot deal with it
gitkeep_file = pdfs_dir + ".gitkeep"
try:
    os.remove(gitkeep_file)
except:
    pass

cleanup = []
result = {}
run_docker_command = True

try:
    if command is None:
        raise RuntimeError("No command")
    if filename is None and command != "train_extraction":
        raise RuntimeError("No filename")

    # OCR
    if command == "ocr":
        try:
            source = tempfile.gettempdir() + "/" + filename + ".pdf"
            target = pdfs_no_ocr_dir + filename + ".pdf"
            ocr_file = pdfs_dir + filename + ".pdf"
            shutil.move(source, target)
            run_docker_command = False
            # wait for OCR to complete
            timer = 0
            while not os.path.isfile(ocr_file):
                time.sleep(1)
                timer += 1
                if timer > 60 * 10:
                    raise RuntimeError("Waited more than 10 minutes for OCR to finish. Aborting")

        except FileNotFoundError as err:
            raise RuntimeError(str(err))

    # Extract layout
    elif command == "layout":
        target = pdfs_dir + filename + ".pdf"
        if not os.path.isfile(target):
            source = tempfile.gettempdir() + "/" + filename + ".pdf"
            try:
                shutil.move(source, target)
            except FileNotFoundError as err:
                raise RuntimeError(str(err))

        cleanup.append(pdfs_dir + filename + ".pdf")
        result_path = layout_dir + filename + ".csv"

    # Identify citations
    elif command == "exparser":
        result_path = refs_dir + filename + ".csv"
        cleanup.append(result_path)
        # also clean up segmentation and bibtex data, which we will re-produce in a seprate step
        cleanup.append(refs_dict_dir + filename + ".csv")
        cleanup.append(refs_prob_dir + filename + ".csv")
        cleanup.append(refs_bibtex_dir + filename + ".csv")

    # Segment citations
    elif command == "segmentation":
        try:
            source = tempfile.gettempdir() + "/" + filename + ".csv"
            target = refs_dir + filename + ".csv"
            shutil.move(source, target)
            cleanup.append(target)
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
    if run_docker_command and (result_path is None or not os.path.isfile(result_path)):
        # run docker command and write output to server output
        args = ['docker', 'run', '--rm', '-v' + os.getcwd() + ':/app', 'excite_toolchain', command]
        sys.stderr.write(" ".join(args) + "\n")
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # check for process completion and copy output to stderr
        return_code = 0
        while True:
            return_code = proc.poll()
            if return_code is not None:
                break
            line = proc.stdout.readline().strip()
            if line != "":
                # write to stderr so that it is printed in the server output
                sys.stderr.write(line)

        # subprocess returned with error
        if return_code != 0:
            raise RuntimeError("\n".join(proc.stderr.readlines()))

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

    # restore .gitkeep file
    open(gitkeep_file, 'a').close()

    # clean up temporary files
    for filepath in cleanup:
        try:
            os.remove(filepath)
            pass
        except OSError:
            pass
