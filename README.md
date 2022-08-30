# EXcite-Docker: Tool for the annotation of training material for ML-based reference extraction and segmentation

This is a docker image that provides a web application to produce training
material for ML-based reference extraction & segmentation engines. Currently
supported are

- [AnyStyle](https://github.com/inukshuk/anystyle) (Annotation & reference extraction)
- [EXParser](http://exparser.readthedocs.io) (Only editing of existing
  annotations; EXparser reference extraction was supported in
  [v1.0.0](https://github.com/cboulanger/excite-docker/tree/v1.0.0))

Both serve to extract citation data from PDF Documents. 

The image provides a Web UI for producing training material which is needed to
improve citation recognition for particular corpora of scholarly literature
where the current models do not perform well.

A demo of the web frontend (without backend functionality) is available 
[here](https://cboulanger.github.io/excite-docker/web/index.html).

## Installation

1. Install [Docker](https://docs.docker.com/install)
2. Clone this repo with: `git clone https://github.com/cboulanger/excite-docker.git && cd excite-docker`
3. Build docker image: `./bin/build`
4. If you want to use AnyCite, please consult its GitHub page on how to install it: https://github.com/inukshuk/anystyle

## Use of the web frontend

1. Run server: `./bin/start-servers`
2. Open frontend at http://127.0.0.1:8000/web/index.html
3. Click on "Help" for instructions (also lets you download the Zotero add-ons)

## Zotero support 

> Zotero integration is currently disabled because the plugin providing the
required API is not compatible with Zotero 6. A native API is planned by the
Zotero Devs.

If a [Zotero](https://zotero.org) with the appropriate add-ins  is running, the
webapp will enable additional commands that let you retrieve the PDF
attachment(s) of the currently selected item/collection, extract references from
them and store them with the citing item.

If the Zotero storage folder is not located in `~/Zotero/storage`, you need to
rename `.env.dist` to `.env` and in this file, set the `ZOTERO_STORAGE_PATH`
environment variable to the path pointing to this directory.
