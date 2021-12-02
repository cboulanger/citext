## Preparation

**Step 1:** [Install
Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1)
on your Linux server.

**Step 2:** Download current repository to your local system and copy all
downloaded files to your Linux server.

**Step 3:** In server, change the directory to "excite-docker" (which is the
name of repository).

```
$ cd excite-docker
```

**Step 4:** Build an image from Docker-file (The name of docker image is
excite_toolchain):

```
$ sudo docker build --no-cache -t excite_toolchain .
```

## How to run

Please follow this Step-By-Step process in sequence as described below.

**Step 1:** The input of this process is PDF file, please put your PDF files in
this directory:

```
$ cd excite-docker/Data/1-pdfs
```

**Step 2:** Extracting the layout from a PDF will be started by calling a Java
module base on "CERMINE", by executing this command:

```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```

The outputs of this step are "Layout files", which will be available in this
directory :

```
$ cd excite-docker/Data/2-layouts
```

**Step 3:** In this step "Exparser" will be called for extracting references
from "Layout files", by executing this command:

```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```

The output will be provided in these different formats: "plain text", "xml" and
"BibTex" format and will be available in this directory :

```
-extracted references in plain text format are available in this directory:
$ cd excite-docker/Data/3-refs

-extracted references in xml format are available in this directory:
$ cd excite-docker/Data/3-refs_seg

-extracted references in BibTeX format are available in this directory: 
$ cd excite-docker/Data/3-refs_bibtex 
```

**Step 4:** In this step "EXmatcher" will be called for matching references
against corresponding items in the defined target bibliographical databases,
by executing this command:

```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```

The input of EXmatcher is reference strings and segments generated in the
previous step. The output will be "matched document ids" and the "probability"
for each match and will be available in this directory :

```
$ cd excite-docker/Data/4-refs_crossref
```

## Built-in Server

This repo includes a very simple webserver which allows to run exparser on
individual files and train the model with new ground truth data.

To start the server, execute `./start-server`, then open http://localhost:8000 

## Training

You can retrain the model, using your own training data. At the moment feature
extraction is done before the model training. 

> If you want to use this feature, you need to have
[git-lfs](https://www.atlassian.com/git/tutorials/git-lfs) installed before you
check out this repository. git-lfs is necessary to download the large files that
are used during training.

Before training, run the `prepare-training` script. This will do the following:

- Ask you if you want to you download the [Excite project's ground truth
  data](https://github.com/exciteproject/Exparser/tree/master/EXparser/Dataset ),
  which provides a basis to which you can add your own data.

- Download the [EXannotator Web GUI](https://github.com/cboulanger/EXannotator) which can
  be used to correct training data or produce new training data.

Training data needs to be placed into the `Exparser/Dataset` folder. For
details, see [here](./EXparser/Dataset/README.md).

To run the training, execute

```
sudo docker run -v $(pwd):/app excite_toolchain train_extraction
```

Input files (for features extraction):
```
EXparser/Dataset/LYT/ - layout files
EXparser/Dataset/LRT/ - layout files with annotation for references <ref>
EXparser/Dataset/SEG* - segmentation data for citations 
```

Output files:
```text
#feature extraction output
EXparser/Dataset/Features/
EXparser/Dataset/RefLD/

#model training output
EXparser/Utils/SMN.npy
EXparser/Utils/FSN.npy
EXparser/Utils/rf.pkl - the model
```

