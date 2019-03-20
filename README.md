# Preparation :
### Setup Docker
In order to install Docker on your machine, please refer to This [link](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1).

### Put a Copy of files on server
Put a copy of "excite_toolchain" on your server.
```
$ cd excite_toolchain
```

## Building a Docker image
Run this command to Build an image from a Docker file
```
$ sudo docker build --no-cache -t excite_toolchain . 
```

# How to run Toolchain:
### First Step: Open Data folder 
Data Folder is located in root of source folder. Put the pdf files in this folder 1-pdfs

### Second Step:
Extracting layouts from pdfs by CERMINE

1. Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain layout
```

2. Outputs
Check This folder to find the Outputa in csv format:
```
Data/2-layouts
```
## Exparser
For Extracting References by Exparser

1. Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain exparser
```
2. Outputs
```
extracted references in plain text format:
Data/3-refs
extracted references in xml format:
Data/3-refs_seg
extracted references in BibTeX format: 
Data/3-refs_bibtex 
```

## Matching
to call Matching to get matched ID for each reference from Crossref, Run this Linux command
```
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher
```

## Outputs
extracted references in dictionary format: 
```
Data/ 4-refs_crossref
```