## Preparation
1. [Install Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1) on your server.
2. Download this repository and copy all downloaded files to your server.
3. Change the directory to "excite-docker" (which is the name of repository):
    - $ cd excite-docker
4. Build an image from a Dockerfile:
    - $ sudo docker build --no-cache -t excite_toolchain . 
```

## How to run
**1. First step:** Put your pdf files in this directory:
```
cd excite-docker/Data/1-pdfs
```
**2. Second step:** Extracting Layout 
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```
The Outputs will be in This folder :
```
cd excite-docker/Data/2-layouts
```
**3. Third step:** Calling Exparser
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