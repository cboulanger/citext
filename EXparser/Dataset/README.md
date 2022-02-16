# Training data

This directory contains the training data of different models in directories having the name/id of the model, 
which in turn contain the following directories

```text
LYT/        .csv files with the extracted contents and layout from the corresponding PDF file (using Cermine), having
            the following columns0
            1 Line's content.
            2 The horizontal distance from the left margin to the beginning of the line.
            3 The vertical distance from the top margin to the line (of the same page).
            4 Width of the line.
            5 Length of the line.
            6 The index of the paragraph.

LRT/        Contains the corresponding (.csv) files of "LYT/*.csv", with annotated reference strings. 
            Each reference string is started with  <ref> and terminated with </ref>

SEG/        Marked up files having an .xml extension (no valid xml content), each of which contains all the extracted 
            reference strings. A reference string is parsed into its components (e.g. author, title, etc.).

Features/   Contains the extracted features from "LYT/*.csv"

RefLD/      Contains the types of lines extracted from "LRT/*csv"
```

