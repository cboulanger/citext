import os
from difflib import SequenceMatcher


def compare_output_to_gold(gold_folder, out_folder):
    """Compares gold files with segmented references
    e.g. <author><surname>Aron</surname>, <given-names>Raymond</given-names>...
    to model output files of the same structure.
    File names should be the same."""

    nums = []
    for file in os.listdir(out_folder):
        if os.path.exists(os.path.join(gold_folder, file)):
            with open(os.path.join(out_folder, file)) as in_f, open(os.path.join(gold_folder, file)) as gold_f:
                out_lines = in_f.read()
                gold_lines = gold_f.read()

                match = SequenceMatcher(None, out_lines, gold_lines).find_longest_match(0, len(out_lines), 0,
                                                                                        len(gold_lines))
                print(file + ": Longest common sequence with the gold: " + out_lines[match.a:match.a + match.size])

                num = len(out_lines[match.a:match.a + match.size]) / len(out_lines)
                print(str(num))
                nums.append(num)
        else:
            print("The gold file is missing for: " + file)

    print("Average: " + str(sum(nums) / len(nums)))


# for test
if __name__ == '__main__':
    compare_output_to_gold("Data/test/gold/", "Data/test/")
