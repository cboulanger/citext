import os
import regex as re
from lxml import etree
from configs import *

# def convert_lrt_to_fasttext(doc: str) -> str:
#     text= ""
#     doc = doc.replace("\r\n", "\n")
#     # remove linebreaks
#     for line in doc.split("\n"):
#         if line == "":
#             continue
#         if re.match(r'.*\p{Pd}$', line) is None:
#             text += " " + line
#         else:
#             text += line



def convert_lrt_to_anystyle(doc: str) -> str:
    ttx = []
    within_ref = False
    curr_line_type = None
    doc = doc.replace("\r\n", "\n")
    for line in doc.split("\n"):
        if line == "":
            continue
        if "\t" not in line:
            # no layout info
            text = line
        else:
            # remove layout info
            text = line.strip().split("\t")[0]
        if within_ref is True:
            # we are in a reference
            line_type = "ref"
        else:
            # otherwise, default line type is text
            line_type = "text"
        # determine positions of <ref>/</ref> tags
        idx_ref = text.rindex("<ref>") if "<ref>" in text else -1
        idx_end_ref = text.rindex("</ref>") if "</ref>" in text else -1
        # fix missing <ref>
        if not within_ref and "<author>" in text:
            idx_ref = 0
        # determine if ref starts and/or ends in line
        if idx_ref >= 0:
            line_type = "ref"
            if idx_ref > idx_end_ref:
                within_ref = True
        if idx_end_ref >= 0:
            line_type = "ref"
            if idx_end_ref > idx_ref:
                within_ref = False
        if text.isdigit():
            # if line contains a numer, assume line number (will produce some false positives)
            line_type = "meta"
        if line_type == curr_line_type:
            # do not output line type if it hasn't changed
            line_type = ""
        else:
            curr_line_type = line_type
        # remove all xml tags
        text = re.sub(r'</?[a-zA-Z-]+>', '', text)
        line = f"{line_type.ljust(14, ' ')}| {text}"
        ttx.append(line)
    # work around bug that crashes anystyle if last line(s) are blank
    while len(ttx):
        if ttx[-1].startswith("blank"):
            ttx.pop(-1)
        else:
            break
    return "\n".join(ttx)


def convert_seg_to_anystyle(source_dir) -> etree.ElementTree:
    files = os.listdir(source_dir)
    target_root = etree.Element("dataset")
    for file in files:
        source_xml = etree.parse(os.path.join(source_dir, file))
        source_root = source_xml.getroot()
        for ref in source_root.iter("ref"):
            sequence = etree.SubElement(target_root, "sequence")
            authors_done = False
            editors_done = False
            for i, child in enumerate(ref):
                tag = child.tag
                if tag == "author":
                    if not authors_done:
                        # merge authors
                        author = "".join([etree.tostring(node).decode() for node in ref.findall("author")])
                        last_node = etree.SubElement(sequence, "author")
                        last_node.text = re.sub(r'</?[^>]+>', '', author)
                        authors_done = True
                    continue
                if tag == "editor":
                    if not editors_done:
                        # merge editors
                        editor = "".join([str(node.text) + str(node.tail) for node in ref.findall("editor")])
                        last_node = etree.SubElement(sequence, "editor")
                        last_node.text = editor
                        editors_done = True
                    continue
                elif tag == "other":
                    tag = "note"
                elif tag == "fpage":
                    last_node = etree.SubElement(sequence, "pages")
                    lpage = ref.find("lpage")
                    last_node.text = str(child.text) + str(child.tail)
                    if lpage is not None:
                        last_node.text = str(last_node.text) + str(lpage.text) + str(lpage.tail)
                    continue
                elif tag == "lpage":
                    continue
                elif tag == "source":
                    if ref.find("editor") is not None:
                        tag = "container-title"
                    else:
                        tag = "journal"
                elif tag == "year":
                    tag = "date"
                elif tag == "issue":
                    vol_node = sequence.find("volume")
                    if vol_node is not None:
                        vol_node.text = str(vol_node.text) + str(child.text) + str(child.tail)
                        continue
                    tag = "volume"
                elif tag == "identifier":
                    if "10." in child.text:
                        tag = "doi"
                    else:
                        tag = "isbn"
                # add node
                last_node = etree.SubElement(sequence, tag)
                last_node.text = str(child.text) + str(child.tail)
    return etree.ElementTree(target_root)

def convert_extraction_file(source_path, target_dir, target_format):
    source_name = os.path.basename(source_path)
    with open(source_path, "r", encoding="utf-8") as f:
        text = f.read()
    if target_format == "anystyle":
        target_text = convert_lrt_to_anystyle(text)
        target_path = os.path.join(target_dir, source_name.replace(".csv", ".ttx"))
    else:
        raise ValueError(f"Format {target_format} not supported")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(target_text)


def convert_extraction_files(model_name, target_format, target_dir=None):
    model_dir = config_dataset_dir(model_name)
    source_dir = os.path.join(model_dir, "LRT")
    if target_dir is None:
        target_dir = os.path.join(model_dir, target_format, "finder")
        os.makedirs(target_dir, exist_ok=True)
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"Directory {target_dir} does not exist")
    count = 0
    for file_name in os.listdir(source_dir):
        if file_name.endswith(".csv"):
            source_path = os.path.join(source_dir, file_name)
            convert_extraction_file(source_path, target_dir, target_format)
            count += 1
    print(f"Converted {count} LRT files.")

def convert_segmentation_files(model_name, target_format, target_dir=None):
    if target_format != "anystyle":
        raise NotImplemented("Only anystyle implemented!")
    model_dir = config_dataset_dir(model_name)
    source_dir = os.path.join(model_dir, "SEG")
    if target_dir is None:
        target_dir = os.path.join(model_dir, target_format, "parser")
        os.makedirs(target_dir, exist_ok=True)
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"Directory {target_dir} does not exist")
    tree = convert_seg_to_anystyle(source_dir)
    target_file = os.path.join(target_dir, model_name + ".xml")
    tree.write(target_file, pretty_print=True, method='xml', encoding="UTF-8", xml_declaration=True)
    print(f"Converted {len(os.listdir(source_dir))} SEG files.")

def dataset_convert(model_name, target_format, target_dir=None):
    convert_extraction_files(model_name, target_format, target_dir=target_dir)
    convert_segmentation_files(model_name, target_format, target_dir=target_dir)
