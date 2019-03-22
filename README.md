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
**Step 1:** Put your pdf files in this directory:
```
cd excite-docker/Data/1-pdfs
```
**Step 2:** Extracting Layout by executing this command:
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```
The outputs of this step are "Layout files", which will be located in this folder :
```
cd excite-docker/Data/2-layouts
```
**Step 3:** Calling Exparser
```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```
The Outputs will be in This folders :
```
-extracted references in plain text format:
cd excite-docker/Data/3-refs

-extracted references in xml format:
cd excite-docker/Data/3-refs_seg

-extracted references in BibTeX format: 
cd excite-docker/Data/3-refs_bibtex 
```
**4. forth step:** Calling EXMatcher
```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```
The Outputs will be in This folders :
```
cd excite-docker/Data/4-refs_crossref
```