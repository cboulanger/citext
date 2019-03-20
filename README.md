## Preparation
1. [Install Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1).
2. Download this repository and copy all downloaded files to the server.
3. Change the directory to "excite_toolchain" (which is the name of repository):
```
$ cd excite_toolchain
```
4. Build an image from a Dockerfile: 
```
$ sudo docker build --no-cache -t excite_toolchain . 
```

## How to run
**1. First step:** Put your pdf files in this directory:
```
cd excite_toolchain/Data/1-pdfs
```
**2. Second step:** ExtractingLayout 
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```
The Outputs will be in This folder :
```
cd excite_toolchain/Data/2-layouts
```
**3. Third step:** calling Exparser**
```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```
The Outputs will be in This folders :
```
extracted references in plain text format:
cd excite_toolchain/Data/3-refs
extracted references in xml format:
cd excite_toolchain/Data/3-refs_seg
extracted references in BibTeX format: 
cd excite_toolchain/Data/3-refs_bibtex 
```
**4. forth step:** Calling Matching
```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```
The Outputs will be in This folders :
```
cd excite_toolchain/Data/4-refs_crossref
```