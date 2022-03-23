# EXParser Docker image & web frontend

This is a docker image of a collection of
[tools](https://excite.informatik.uni-stuttgart.de/#software) from the [EXcite
project](https://excite.informatik.uni-stuttgart.de/) which serve to extract
citation data from PDF Documents. In particular, it provides a Web UI for
producing training material which is needed to improve citation recognition for
particular corpora of scholarly literature where the current algorithm does not
perform well.

The code has been forked from https://git.gesis.org/hosseiam/excite-docker, but
has been in many parts completely rewritten.

A demo of the web frontend (without backend functionality) is available 
[here](https://cboulanger.github.io/excite-docker/web/index.html).

## Installation

1. Install [Docker](https://docs.docker.com/install)
2. Clone this repo with: `git clone https://github.com/cboulanger/excite-docker.git && cd excite-docker`
3. Build docker image: `./bin/build`
4. If you want to connect the web app with a locally running Zotero instance,
   install the following Zotero add-ons from the files shipped with this repo:
   - [cita](zotero/cita.xpi)
   - [zotero-apt-endpoint](zotero/zotero-api-endpoint.xpi)

## Use of the web frontend

1. Run server: `./bin/start-servers`
2. Open frontend at http://127.0.0.1:8000/web/index.html
3. Click on "Help" for instructions (also lets you download the Zotero add-ons)

## Zotero support

If a [Zotero](https://zotero.org) with the appropriate add-ins (see above) is
running, the webapp will enable additional commands that let you retrieve the
PDF attachment(s) of the currently selected item/collection, extract references
from them and store them with the citing item.

If the Zotero storage folder is not located in `~/Zotero/storage`, you need to
rename `.env.dist` to `.env` and in this file, set the `ZOTERO_STORAGE_PATH`
environment variable to the path pointing to this directory.

## CLI

You can control the extraction and segmentation process via the CLI. 
CLI commands can be executed like so:

`./bin/run-command <command>`

Available commands are: 

- `layout`: run layout analysis of any PDF file in `Data/1-pdfs` and put the
  result into `Data/2-layout`
- `exparser`: process all the files in `Data/2-layout`. The output will be
  provided in  csv (plain text), xml and BibTex format in the directories
  `Data/3-refs`, `Data/3-refs_seg` and `Data/3-refs_bibtex`
- `exmatcher`: Match this data against the data in the [CrossRef
  database](https://www.crossref.org/): `docker run -v $(pwd):/app
  excite_toolchain exmatcher`. Any matched reference will be in
  `Data/4-refs_crossref`
- `segmentation`: process the references that are in the csv files in the
  `Data/3-refs` directory and output xml and BibTex files in 
  `Data/3-refs_seg` and `Data/3-refs_bibtex`

For more CLI commands, see the sections below.

## Training a new model

> If you want to use this feature, you need to have
[git-lfs](https://www.atlassian.com/git/tutorials/git-lfs) installed **before** you
check out this repository. git-lfs is necessary to download the large files that
are used during training.

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
8. On the command line, run `./bin/training <model_name>`. If
you want to train extraction and segmentation models separately, use
`./bin/run-command train_extraction <model_name>` or `train_segmentation
<model_name>`

Training data lives in the `EXparser/Dataset/<model_name>`
folder. For details, see [here](./EXparser/Dataset/README.md).

For training, you need to populate the following folders with training data:
```
Dataset/<model_name>/LYT/ - layout files
Dataset/<model_name>/LRT/ - layout files with annotation for references <ref>
Dataset/<model_name>/SEG/ - segmentation data for citations 
```

To run the training, execute `./bin/training <model_name>`.

This will generate data in the following folders:
```text
#feature extraction output
Dataset/<model_name>/Features/
Dataset/<model_name>/RefLD/

#model training output
Models/<model_name>/SMN.npy
Models/<model_name>/FSN.npy
Models/<model_name>/rf.pkl - the model
```

You can list all existing models with `list_models` and delete a model with
`delete_model <model_name>`.

## WebDAV model storage

You can store model and training data on a WebDAV server, which is particularly
useful for sharing data and collaborative training. To enable this, rename `/.env.dist`
to `.env` and configure the required environment variables.

To upload training or model data to the WebDAV server, do the following

```shell
./bin/run-command upload_model <model name> <package name> (model|training|extraction|segmentation|all)
```

The `package_name` is an arbitrary string which should express the content of
the package, such as `mymodel-training-segmentation`. After the package name,
you can either add "all" to upload the complete set of data, including both
model and training data, or specify parts that you want to include, such as
`training extraction segmentation` (to have both extraction and segmentation
training data) or `model` to just upload the model data.

You can then later `download_model other_model package_name` to load the package
contents into the new model.

Display the list of remotely stored packages with `list_packages` and delete a
package with `delete_package <package_name>`.
