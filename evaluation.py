import os, sys, re
from difflib import SequenceMatcher

def eval_extraction(
        gold_dir:str,
        exparser_result_dir:str,
        output_dir:str=None,
        add_logfile=False,
        output_filename_prefix="") -> str:

    """Compares gold files with files with extracted references.
    Finds longest common sequence between each extracted reference and the whole gold file
    represented as a single string.

    Gold and model output's file names should be the same (except for the last extension).
    :returns Path to the CSV file that contains a list of file names and accuracies
    """

    logfile = os.path.join(output_dir, f"{output_filename_prefix}extraction.log")
    csvfile = os.path.join(output_dir, f"{output_filename_prefix}extraction.csv")
    with open(logfile, "w") as o, open(csvfile, "w") as c:
        o.write("Gold folder: " + gold_dir + ", Results folder: " + exparser_result_dir)

        nums = []
        for file_name in os.listdir(exparser_result_dir):
            if file_name.startswith(".") or not file_name.endswith(".csv"):
                continue

            eval_file_path = os.path.join(exparser_result_dir, file_name)
            gold_file_path = os.path.join(gold_dir, file_name)

            if not os.path.exists(gold_file_path):
                raise RuntimeError(f"The extraction gold file {gold_file_path} is missing.")

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
                accuracy = sum(file_nums) / len(file_nums)
                nums.append(accuracy)
                o.write(f"Average accuracy for {file_name}: {str(accuracy)}\n")
                c.write(f'"{file_name}",{accuracy}\n')

        if len(nums) == 0:
            raise RuntimeError(f"No accuracy information for files in {gold_dir}")
        accuracy = sum(nums) / len(nums)
        o.write(f"Average accuracy for all files: {str(accuracy)}\n")
        c.write(f'"{file_name}",{accuracy}\n')
    if not add_logfile:
        os.remove(logfile)
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


def eval_segmentation(
        gold_dir: str,
        exparser_result_dir: str,
        output_dir: str = None,
        add_logfile=False,
        output_filename_prefix="") -> str:

    """Compares gold files with segmented references
    e.g. <author><surname>Aron</surname>, <given-names>Raymond</given-names>...
    to model output files of the same structure.
    File names should be the same.

    :returns Path to the CSV file that contains a list of file names and accuracies
    """

    logfile = os.path.join(output_dir, f"{output_filename_prefix}segmentation.log")
    csvfile = os.path.join(output_dir, f"{output_filename_prefix}segmentation.csv")
    with open(logfile, "w") as o, open(csvfile, "w") as c:
        o.write("Gold folder: " + gold_dir + ", Results folder: " + exparser_result_dir)

        nums = []
        for file in os.listdir(exparser_result_dir):
            if file.startswith(".") or not file.endswith(".xml"):
                continue

            if not os.path.exists(os.path.join(gold_dir, file)):
                raise RuntimeError("The segmentation gold file is missing for: " + file)

            extracted_file_path = os.path.join(exparser_result_dir, file)
            gold_file_path = os.path.join(gold_dir, file)
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
                    raise RuntimeError(f"Different number of lines in extracted {extracted_file_path} ({len(out_maps)}) vs. gold file {gold_file_path} ({len(gold_maps)}).")

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
                    sys.stderr.write(f"{file} does not contain any accuracy information!\n")
                    continue

                accuracy = sum(acc_per_line) / len(acc_per_line)
                o.write("\nAverage accuracy for " + file + ": " + str(accuracy))
                c.write(f'"{file}",{accuracy}\n')
                nums.append(sum(acc_per_line) / len(acc_per_line))

        avg_msg = f"\nAverage accuracy for all files: {str(sum(nums) / len(nums))}\n"
        sys.stderr.write(avg_msg)
        o.write(avg_msg)
        if not add_logfile:
            os.remove(logfile)
        return csvfile


# for test
if __name__ == '__main__':
    compare_output_to_gold("Data/test/extract/gold/", "Data/test/extract/", Modes.EXTRACTION.value)
    # compare_output_to_gold("Data/test/segment/gold/", "Data/test/segment/", Modes.SEGMENTATION.value)
