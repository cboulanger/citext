# EXParser Docker Image

This is a docker image of a collection of [tools](https://excite.informatik.uni-stuttgart.de/#software) 
from the [EXcite project](https://excite.informatik.uni-stuttgart.de/)
which serve to extract citation data from PDF Documents. In particular, it provides a Web UI 
for producing training material which is needed to improve citation recognition for
particular corpora of scholarly literatur where the current algorith does not perform well.

The code has been forked from https://git.gesis.org/hosseiam/excite-docker, but parts of the frontend 
have been completely rewritten. 

Demos of the training frontends are available here (no backend functionality):

- [Reference String Extraction](https://cboulanger.github.io/excite-docker/EXannotator/EXRef-Identifier/index.html) 
- [Reference Segmentation](https://cboulanger.github.io/excite-docker/EXannotator/EXRef-Segmentation/index.html)

## Installation

1. Install prerequisites: [Docker](https://docs.docker.com/install) and [Python v3](https://www.python.org/downloads/)
2. Clone this repo: `git clone https://github.com/cboulanger/excite-docker.git && cd excite-docker`
3. Build docker image: `sudo docker build --no-cache -t excite_toolchain .`
4. Run server: `./start-server`
5. Open frontend at http://127.0.0.1:8000/index.html

## Run extraction via CLI

You can also use this image as a CLI tool to extract references from a batch of PDFs (this was the original 
purpose of the repo it was forked from):

1. put your PDF files in `Data/1-pdfs`
2.Run the layout analysis: `docker run -v $(pwd):/app excite_toolchain layout`
2. Run citation extraction: `docker run -v $(pwd):/app excite_toolchain exparser`. 
The output will be provided in these different formats: "plain text", "xml" and
"BibTex" format and will be available in the directories `Data/3-refs`, `Data/3-refs_seg` 
and `Data/3-refs_bibtex`
3. Match references against the data in the [CrossRef database](https://www.crossref.org/): 
`docker run -v $(pwd):/app excite_toolchain exmatcher`. Any matched reference will be in 
`Data/4-refs_crossref`

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

