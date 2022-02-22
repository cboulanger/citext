# EXParser Docker image & web frontend

This is a docker image of a collection of
[tools](https://excite.informatik.uni-stuttgart.de/#software) from the [EXcite
project](https://excite.informatik.uni-stuttgart.de/) which serve to extract
citation data from PDF Documents. In particular, it provides a Web UI for
producing training material which is needed to improve citation recognition for
particular corpora of scholarly literatur where the current algorith does not
perform well.

The code has been forked from https://git.gesis.org/hosseiam/excite-docker, but
has been in many parts completely rewritten.

A demo of the web frontend (without backend functionality) is available 
[here](https://cboulanger.github.io/excite-docker/web/index.html).

## Installation

1. Install [Docker](https://docs.docker.com/install)
2. Clone this repo with: `git clone https://github.com/cboulanger/excite-docker.git && cd excite-docker`
3. Build docker image: `./bin/build`
5. If you want to connect the web app with a locally running Zotero instance,
   install the following Zotero Add-ons:
   1. [cita](zotero/cita.xpi)
   2. [zotero-apt-endpoint](zotero/zotero-api-endpoint.xpi)

## Use of the web frontend

1. Run server: `./bin/start-servers`
2. Open frontend at http://127.0.0.1:8000/web/index.html
3. Click on "Help" for instructions

## Zotero support

If a [Zotero](https://zotero.org) with the appropriate add-ins (see above) is
running, the webapp will enable additional commands that let you retrieve the
PDF attachment(s) of the currently selected item/collection, extract references
from them and store them with the citing item.

If the Zotero storage folder is not located in `~/Zotero/storage`, you need to
set the ZOTERO_STORAGE_PATH environment variable to the exact path before starting
the servers.

## Run extraction via CLI

You can also use this image as a CLI tool to extract references from a batch of
PDFs (this was the original purpose of the repo it was forked from):

1. put your PDF files in `Data/1-pdfs` 2.Run the layout analysis: `docker run -v
   $(pwd):/app excite_toolchain layout`
2. Run citation extraction: `docker run -v $(pwd):/app excite_toolchain
   exparser`. The output will be provided in these different formats: "plain
   text", "xml" and "BibTex" format and will be available in the directories
   `Data/3-refs`, `Data/3-refs_seg` and `Data/3-refs_bibtex`
3. Match references against the data in the [CrossRef
   database](https://www.crossref.org/): `docker run -v $(pwd):/app
   excite_toolchain exmatcher`. Any matched reference will be in
   `Data/4-refs_crossref`

## Training a new model

In order to train a new model from scratch, you need to do the following:

1. Run `./bin/run-command create_mdoel <model_name>` 
2. Put the PDFs with which you are going to train the model into `Data/1-pdfs`
   if they are native PDFs or contain an OCR layer. If the PDFs consist of
   scanned pages without the OCR layer, put them into `0-pdfs_no_ocr` and wait
   for the OCR server to process them and move them to `Data/1-pdfs`
3. Create the layout files with `./bin/run-command layout`
4. Move files from `Data/2-layout` into `EXparser/Dataset/<model_name>/LYT`
5. Load the web application and choose your new model from the "Model" dropdown
6. Use the web application to load and annotate the layout files from
   `EXparser/Dataset/<model_name>/LYT` in the identification and segmentation
   views. Here is more information on training [the reference extraction
   model](https://exparser.readthedocs.io/en/latest/ReferenceExtraction/) and the
   [the reference parsing model](https://exparser.readthedocs.io/en/latest/ReferenceParsing/).
7. "Save" the training files after each annotation, they will be stored
   in the model directory
8. On the command line, run `./bin/run-command training <model_name>`

> If you want to use this feature, you need to have
[git-lfs](https://www.atlassian.com/git/tutorials/git-lfs) installed **before** you
check out this repository. git-lfs is necessary to download the large files that
are used during training.

Before training, run `./bin/prepare-training`. Training data needs to be placed
into the `Exparser/Dataset/<model_name>` folder. For details, see
[here](./EXparser/Dataset/README.md).

To run the training, execute `./bin/training <model_name>`.

Input files (for features extraction):
```
Dataset/<model_name>/LYT/ - layout files
Dataset/<model_name>/LRT/ - layout files with annotation for references <ref>
Dataset/<model_name>/SEG/ - segmentation data for citations 
```

Output files:
```text
#feature extraction output
Dataset/<model_name>/Features/
Dataset/<model_name>/RefLD/

#model training output
Models/<model_name>/SMN.npy
Models/<model_name>/FSN.npy
Models/<model_name>/rf.pkl - the model
```
