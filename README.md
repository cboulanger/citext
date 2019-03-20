Preparation :
0: Setup Docker
In order to install Docker on your machine, please refer to This link.

1: put a Copy of code on server
First of all,  we need to put a copy of excite_toolchain “source files” on server:
Name of source files folder is: excite_toolchain
Path of source files on server(for Example): /path_of_source_folder/excite_toolchain

2: Change the directory
Go to the source code directory in server by this command
$ cd /path_of_source_folder/excite_toolchain

3: Building an image from a Docker file
Run this command to Build an image from a Docker file
$ sudo docker build --no-cache -t excite_toolchain . 

How to run Toolchain:
First Step:

1 : Open Data folder (which is located in root of source folder)
Put the pdf files in this folder  1-pdfs

Second Step:
2 : Extracting layouts from pdfs by CERMINE

2-1 :
Run this Linux command
$ sudo docker run -v $(pwd):/app excite_toolchain layout

2-2: Outputs
Check This folder to find the Outputa in csv format:
Data/2-layouts
Third Step:
3 : For Extracting References by Exparser

3-1 :
Run this Linux command
$ sudo docker run -v $(pwd):/app excite_toolchain exparser

3-2 : Outputs
extracted references in plain text format:
Data/3-refs

extracted references in xml format:
Data/3-refs_seg

extracted references in BibTeX format: 
Data/3-refs_bibtex 
Last Step:
4: Finding Crossref matched ID for each reference
Run this Linux command
$ sudo docker run -v $(pwd):/app excite_toolchain exmatcher

3-2 : Outputs
extracted references in dictionary format: 

Data/ 4-refs_crossref
