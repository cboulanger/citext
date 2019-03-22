## Preparation
**Step 1:** [Install Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1) on your server.

**Step 2:** Download current repository to your local system and copy all downloaded files to your Linux server.

**Step 3:** In server, change the directory to "excite-docker" (which is the name of repository).
```
$ cd excite-docker
```

**Step 4:** Build an image from Docker-file (name of docker image is excite_toolchain):
```
$ sudo docker build --no-cache -t excite_toolchain .
```

## How to run
Please Follow this Step-By-Step Process in Sequence as Described Below.

**Step 1:** the input of this process is PDF file, please put the PDF files in this directory:
```
cd excite-docker/Data/1-pdfs
```
**Step 2:** Extracting the layout from a PDF will be started by calling a Java module base on CERMINE by executing this command:
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```
The outputs of this step are "Layout files", which will be located in this directory :
```
cd excite-docker/Data/2-layouts
```
**Step 3:** In this step Exparser will be called for extracting references from Layout file by executing this command:
```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```
The output will be provided in these different formats: plain text, xml and BibTex format and will be located in this directory :
```
-extracted references in plain text format are available in this directory:
cd excite-docker/Data/3-refs

-extracted references in xml format are available in this directory:
cd excite-docker/Data/3-refs_seg

-extracted references in BibTeX format are available in this directory: 
cd excite-docker/Data/3-refs_bibtex 
```
**Step 4:** Calling EXMatcher, .
```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```
The input of EXmatcher is reference strings and segments generated in the previous step. 
The output will be "matched document ids" and the "probability" for each match and will be located in this directory :
```
cd excite-docker/Data/4-refs_crossref
```