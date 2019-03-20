## Preparation :
**1. Setup Docker:** 

In order to install Docker on your machine, please refer to This [link](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1).

**2. Put a Copy of source files on server:** 

Put a copy of "excite_toolchain" on your server.
```
$ cd excite_toolchain
```
**3. Building a Docker image:**

Run this command to Build an image from a Docker file
```
$ sudo docker build --no-cache -t excite_toolchain . 
```

## How to run Toolchain:
**1. Put pdf files in "Data folder":**

Data Folder is located in root of source folder. Put the pdf files in this folder 
```
cd excite_toolchain/Data/1-pdfs
```
**1. Layout Extracting:** 

Extracting layouts from pdfs by CERMINE Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```
The Outputs will be in This folder to find the Outputa in csv format:
```
cd excite_toolchain/Data/2-layouts
```
**2. Exparser**

For Extracting References by Exparser Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```

Outputs
```
extracted references in plain text format:
cd excite_toolchain/Data/3-refs
extracted references in xml format:
cd excite_toolchain/Data/3-refs_seg
extracted references in BibTeX format: 
cd excite_toolchain/Data/3-refs_bibtex 
```

**3. Matching**

to call Matching to get matched ID for each reference from Crossref, Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```

Outputs extracted references in dictionary format: 
```
cd excite_toolchain/Data/4-refs_crossref
```