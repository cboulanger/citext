import os
from enum import Enum
import re
from difflib import SequenceMatcher
from datetime import datetime


class Modes(Enum):
    EXTRACTION = "extr"
    SEGMENTATION = "seg"


def compare_output_to_gold(gold_folder, out_folder, mode, log_folder=""):
    if mode == Modes.EXTRACTION.value:
        eval_extraction(gold_folder, out_folder, log_folder)
    elif mode == Modes.SEGMENTATION.value:
        eval_segmentation(gold_folder, out_folder, log_folder)


def eval_extraction(gold_folder: str, out_folder:str, log_folder="") -> str:
    """Compares gold files with files with extracted references.
    Finds longest common sequence between each extracted reference and the whole gold file
    represented as a single string.

    Gold and model output's file names should be the same (except for the last extension).
    :returns Path to the CSV file that contains a list of file names and accuracies
    """
    date_string = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    logfile = os.path.join(log_folder, f"{date_string}_extraction_evaluation.txt")
    csvfile = os.path.join(log_folder, f"{date_string}_extraction_evaluation.csv")
    with open(logfile, "w") as o, open(csvfile, "w") as c:
        o.write("Gold folder: " + gold_folder + ", Results folder: " + out_folder)

        nums = []
        for filename in os.listdir(out_folder):
            if filename.startswith(".") or not filename.endswith(".csv"):
                print(f"Ignoring {filename}")
                continue

            eval_file_path = os.path.join(out_folder, filename)
            gold_file_name = filename.replace(".csv",".xml")
            gold_file_path = os.path.join(gold_folder, gold_file_name)

            if not os.path.exists(gold_file_path):
                print("The gold file is missing for: " + filename)
                continue

            o.write(f"Comparing {eval_file_path} with gold {gold_file_path}: \n  - longest common sequence:")

            with open(eval_file_path) as in_f, open(gold_file_path) as gold_f:
                gold_lines = gold_f.read()
                # todo: look into other punctuation
                gold_no_tags = re.sub('<[^<]+>', "", gold_lines).replace(" ", "").replace(",", "").replace(".", "")

                out_lines = in_f.readlines()

                file_nums = []
                for o_line in out_lines:
                    o_line_no_spaces = o_line.replace(" ", "").replace(",", "").replace(".", "")
                    match = SequenceMatcher(None, o_line_no_spaces, gold_no_tags).find_longest_match(0, len(
                        o_line_no_spaces), 0, len(gold_no_tags))
                    o.write(o_line_no_spaces[match.a:match.a + match.size] + "\n")
                    num = len(o_line_no_spaces[match.a:match.a + match.size]) / len(o_line_no_spaces)
                    file_nums.append(num)
                nums.append(sum(file_nums) / len(file_nums))

        if len(nums) == 0:
            print(f"No accuracy information for files in {gold_folder}")
        else:
            accuracy = sum(nums) / len(nums)
            o.write(f"Average accuracy for {filename}: {str(accuracy)}\n")
            c.write(f'"{filename}",{accuracy}\n')
    return csvfile


tags = ["surname", "given-names", "title", "source", "year", "editor", "publisher", "volume", "issue", "other"]


def get_value_tag_map(ref_string):
    value_tag_map = {}

    for tag in tags:
        for item in ref_string.split("</" + tag + ">"):
            br_tag = "<" + tag + ">"
            if "<" + tag + ">" in item:
                value = item[item.find(br_tag) + len(br_tag):]
                value_tag_map[value] = tag

    return value_tag_map


def eval_segmentation(gold_folder: str, out_folder: str, log_folder="") -> str:
    """Compares gold files with segmented references
    e.g. <author><surname>Aron</surname>, <given-names>Raymond</given-names>...
    to model output files of the same structure.
    File names should be the same.

    :returns Path to the CSV file that contains a list of file names and accuracies
    """

    date_string = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    logfile = os.path.join(log_folder, f"{date_string}_segmentation_evaluation.txt")
    csvfile = os.path.join(log_folder, f"{date_string}_segmentation_evaluation.csv")
    with open(logfile, "w") as o, open(csvfile, "w") as c:
        o.write("Gold folder: " + gold_folder + ", Results folder: " + out_folder)

        nums = []
        for file in os.listdir(out_folder):
            if file.startswith(".") or not file.endswith(".xml"):
                continue

            if os.path.exists(os.path.join(gold_folder, file)):
                extracted_file_path = os.path.join(out_folder, file)
                gold_file_path = os.path.join(gold_folder, file)
                with open(extracted_file_path) as in_f, open(gold_file_path) as gold_f:
                    # token-to-tags maps
                    out_maps = []
                    for l in in_f:
                        out_maps.append(get_value_tag_map(l))

                    gold_maps = []
                    for l in gold_f:
                        if l.startswith("<?xml") or l.startswith("<seganno>") or l.startswith("</seganno>"):
                            continue
                        gold_maps.append(get_value_tag_map(l))

                    if len(out_maps) != len(gold_maps):
                        print(f"Skipping {file} for segmentation evaluation: different number of lines in extracted vs. gold file." )
                        continue

                    acc_per_line = []
                    for i in range(len(gold_maps)):
                        out_map = out_maps[i]
                        gold_map = gold_maps[i]

                        if len (out_map.keys()) == 0 or len(gold_map.keys()) == 0:
                            continue

                        correct_value_tag_pairs = 0
                        gold_value_tag_pairs = len(gold_map.keys())
                        for k, v in gold_map.items():
                            if k in out_map:
                                if v == out_map[k]:
                                    correct_value_tag_pairs += 1
                        acc_per_line.append(correct_value_tag_pairs / gold_value_tag_pairs)

                    if len(acc_per_line) == 0:
                        print(f"{file} does not contain any accuracy information")
                        continue

                    accuracy = sum(acc_per_line) / len(acc_per_line)
                    o.write("Average accuracy for " + file + ": " + str(accuracy))
                    c.write(f'"{file}",{accuracy}\n')
                    nums.append(sum(acc_per_line) / len(acc_per_line))
            else:
                print("The gold file is missing for: " + file)

        print("Average accuracy for all files: " + str(sum(nums) / len(nums)))
        o.write(f"Average accuracy for all files: {str(sum(nums) / len(nums))}\n")
        return csvfile

# for test
if __name__ == '__main__':
    compare_output_to_gold("Data/test/extract/gold/", "Data/test/extract/", Modes.EXTRACTION.value)
    # compare_output_to_gold("Data/test/segment/gold/", "Data/test/segment/", Modes.SEGMENTATION.value)
