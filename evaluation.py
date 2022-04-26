import os
from enum import Enum
import re
from difflib import SequenceMatcher


class Modes(Enum):
    EXTRACTION = "extr"
    SEGMENTATION = "seg"


def compare_output_to_gold(gold_folder, out_folder, mode):
    if mode == Modes.EXTRACTION.value:
        eval_extraction(gold_folder, out_folder)
    elif mode == Modes.SEGMENTATION.value:
        eval_segmentation(gold_folder, out_folder)


def eval_extraction(gold_folder, out_folder):
    """Compares gold files with files with extracted references.
    Finds longest common sequence between each extracted reference and the whole gold file
    represented as a single string.

    Gold and model output's file names should be the same (except for the last extension)."""

    nums = []
    for file in os.listdir(out_folder):
        if not file.endswith(".csv"):
            continue

        gold_file_name = file.replace(".csv", ".xml")
        if os.path.exists(os.path.join(gold_folder, gold_file_name)):
            with open(os.path.join(out_folder, file)) as in_f, open(os.path.join(gold_folder, gold_file_name)) as gold_f:
                gold_lines = gold_f.read()
                # todo: look into other punctuation
                gold_no_tags = re.sub('<[^<]+>', "", gold_lines).replace(" ", "").replace(",", "").replace(".", "")

                out_lines = in_f.readlines()

                file_nums = []
                for o_line in out_lines:
                    o_line_no_spaces = o_line.replace(" ", "").replace(",", "").replace(".", "")
                    match = SequenceMatcher(None, o_line_no_spaces, gold_no_tags).find_longest_match(0, len(
                        o_line_no_spaces), 0, len(gold_no_tags))
                    print(file + ": Longest common sequence with the gold: " + o_line_no_spaces[
                                                                               match.a:match.a + match.size])

                    num = len(o_line_no_spaces[match.a:match.a + match.size]) / len(o_line_no_spaces)
                    print(str(num))
                    file_nums.append(num)
                nums.append(sum(file_nums) / len(file_nums))
        else:
            print("The gold file is missing for: " + file)

    print("Average: " + str(sum(nums) / len(nums)))


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


def eval_segmentation(gold_folder, out_folder):
    """Compares gold files with segmented references
    e.g. <author><surname>Aron</surname>, <given-names>Raymond</given-names>...
    to model output files of the same structure.
    File names should be the same."""

    nums = []
    for file in os.listdir(out_folder):
        if not file.endswith(".xml"):
            continue

        if os.path.exists(os.path.join(gold_folder, file)):
            with open(os.path.join(out_folder, file)) as in_f, open(os.path.join(gold_folder, file)) as gold_f:
                # token-to-tags maps
                out_maps = []
                for l in in_f:
                    out_maps.append(get_value_tag_map(l))

                gold_maps = []
                for l in gold_f:
                    gold_maps.append(get_value_tag_map(l))

                if len(out_maps) != len(gold_maps):
                    print("Segmentation evaluation: different number of lines for: " + file)
                    print("The file will be skipped")
                    continue

                acc_per_line = []
                for i in range(len(gold_maps)):
                    out_map = out_maps[i]
                    gold_map = gold_maps[i]

                    correct_value_tag_pairs = 0
                    gold_value_tag_pairs = len(gold_map.keys())
                    for k, v in gold_map.items():
                        if k in out_map:
                            if v == out_map[k]:
                                correct_value_tag_pairs += 1
                    acc_per_line.append(correct_value_tag_pairs / gold_value_tag_pairs)

                print("Average accuracy for " + file + ": " + str(sum(acc_per_line) / len(acc_per_line)))
                nums.append(sum(acc_per_line) / len(acc_per_line))
        else:
            print("The gold file is missing for: " + file)

    print("Average for all files: " + str(sum(nums) / len(nums)))


# for test
if __name__ == '__main__':
    # compare_output_to_gold("Data/test/extract/gold/", "Data/test/extract/", Modes.EXTRACTION.value)
    compare_output_to_gold("Data/test/segment/gold/", "Data/test/segment/", Modes.SEGMENTATION.value)
