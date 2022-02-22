#!/usr/bin/env python3

import json, os, cgi, shutil, subprocess, io, sys, tempfile, time, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import *

print("Content-type: application/json")
print()

form = cgi.FieldStorage()
command = form.getvalue("command")
filename = form.getvalue("file") # without extension!
model_name = form.getvalue("model_name") or ""

result_path = None

# remove .gitkeep because cermine cannot deal with it
gitkeep_file = config_url_pdfs() + ".gitkeep"
try:
    os.remove(gitkeep_file)
except:
    pass

cleanup_dirs = [
    config_url_pdfs_no_ocr(),
    config_url_pdfs(),
    config_url_Refs(),
    config_url_Refs_segment(),
    config_url_Refs_segment_dict(),
    config_url_Refs_segment_prob(),
    config_url_Refs_bibtex(),
    config_url_Refs_crossref()
]

if command != "exparser":
    cleanup_dirs.append(config_url_Layouts())

result = {}
run_docker_command = True

try:

    # cleanup folders without removing ".gitkeep"
    for folder in cleanup_dirs:
        for fname in os.listdir(folder):
            file_path = os.path.join(folder, fname)
            if os.path.isfile(file_path) and not fname.startswith("."):
                os.unlink(file_path)

    if command is None:
        raise RuntimeError("No command")
    if filename is None and command != "train_extraction":
        raise RuntimeError("No filename")

    # OCR
    if command == "ocr":
        try:
            source = os.path.join(tempfile.gettempdir(), filename + ".pdf")
            target = os.path.join(config_url_pdfs_no_ocr(), filename + ".pdf")
            ocr_file = os.path.join(config_url_pdfs(), filename + ".pdf")
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
        target = os.path.join(config_url_pdfs(), filename + ".pdf")
        if not os.path.isfile(target):
            source = os.path.join(tempfile.gettempdir(), filename + ".pdf")
            try:
                shutil.copy(source, target)
            except FileNotFoundError as err:
                raise RuntimeError(str(err))
            except PermissionError:
                # works around Windows WSL issue
                pass
            finally:
                os.remove(source)

        result_path = os.path.join(config_url_Layouts(), filename + ".csv")

    # Identify citations
    elif command == "exparser":
        result_path = os.path.join(config_url_Refs(), filename + ".csv")

    # Segment citations
    elif command == "segmentation":
        try:
            source = os.path.join(tempfile.gettempdir(), filename + ".csv")
            target = os.path.join(config_url_Refs(), filename + ".csv")
            shutil.move(source, target)
        except FileNotFoundError as err:
            raise RuntimeError(str(err))
        result_path = os.path.join(config_url_Refs_segment(), filename + ".xml")

    elif command == "train_extraction":
        result_path = None

    else:
        raise RuntimeError("Invalid command: " + command)

    # only call docker command if file doesn't already exist
    if run_docker_command and (result_path is None or not os.path.isfile(result_path)):
        # run docker command and write output to server output
        args = ['python3', '/app/run-main.py', command, model_name]
        sys.stderr.write("Executing " + " ".join(args) + "\n")
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
            lines = [line.strip('\n') for line in proc.stderr.readlines() if line.strip('\n')]
            err_msg = '\n'.join(lines)
            raise RuntimeError(err_msg)

    if result_path is None:
        result["success"] = True
    else:
        # return result of excite command
        try:
            with open(result_path, "r") as result_file:
                content = result_file.read()
                result["success"] = content
                if command == "layout" and model_name:
                    lyt_dir = os.path.join("/app/EXparser/Dataset", model_name, "LYT")
                    sys.stderr.write(lyt_dir)
                    if os.path.isdir(lyt_dir):
                        with open(os.path.join(lyt_dir, filename + ".csv"), "w") as lyt_file:
                            lyt_file.write(content)

        except Exception as err:
            raise RuntimeError(str(err))

except RuntimeError as err:
    sys.stderr.write(traceback.format_exc())
    result["error"] = str(err).strip('\n')

except BaseException as err:
    import traceback
    traceback.print_exc()
    result["error"] = str(err).strip('\n')

finally:
    # return result
    print(json.dumps(result))

    # restore .gitkeep file
    open(gitkeep_file, 'a').close()
