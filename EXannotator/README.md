## Annotator tools Introduction
### EXRef-Identifier: Reference String Identifier
The goal of this EXRef-Identifier Tool is **"Reference String Identifying"**. 

#### How To Run
1. Put a copy of **"EXRef-Identifier"** folder in the localhost directory. 
2. Use this URL ```http://localhost/EXRef-Identifier/index.html``` to run the tool.

#### How To Use
1. Upload two file. The paper in .pdf format and the layout file in .txt fromat.
2. Scroll down to find the reference section in both file.
3. Select reference strings in text file, 
compare it with the original text in pdf 
and add ```<ref>``` and ```</ref>``` tags to the beginning and the 
end of each reference by click on related button.
4. Finlay save annotated Layout file as a XML file.
5. A live demo is available [here](https://excite.informatik.uni-stuttgart.de/refanno/)
6. A video tutorial to learn how to use this tool is available [here](https://www.youtube.com/watch?v=QSiqIHts23I&t=21s)

#### Sample File To Use
* Sample files to test are available [here](https://github.com/exciteproject/EXannotator/tree/master/Files_for_test/EXRef-Segmentation).
* The layout file extracted from pdf file by using [Refex](https://github.com/exciteproject/refext).

#### Output Sample
Output File will be in XML Format. The following is part of sample output:
```html
.
..
<ref>1971: Theorie der Subkultur. Frankfurt a.M.</ref>
<ref>1976: Rosa Luxemburg im botanischen Garten, gesungen im Kulturzelt aufdem Pfingst­
kongress, Booklet zur Kassette „Pfingstkongreß 1976“, Sozialistisches Bürol985</ref>
<ref>1978/1982: Zur Geschichte der Zukunft. Zukunftsforschung und Sozialismus, Band 1.
Frankfurt a.M.</ref>
..
.
```

### EXRef-Segmentation: Meta Data Segmentation
The goal of EXRef-Segmentation is **"Meta Data Segmentation"**.
This annotator gives assessors this possibility to tag meta data in each reference string.
Which could be include these Meta data: ```<author>, <surname>, <given-names>, <title>, <editor>, <publisher>, <year>, <volume>, <issue>, <identifier>,
             <source>, <url>, <fpage>, <lpage>, <other>,  ... ``` .

#### How To Run
There are two ways of using EXRef-Segmentation:

* Put a copy of **"EXRef-Segmentation"** folder in localhost directory. 
* Use this URL ```http://localhost:8080/EXRef-Segmentation/index.html``` to run the tool.

#### How To Use
1. Upload a text file which contain references (each reference should be in one line).
2. Select meta data in text and tagged them by click on related buttons.
3. Navigate between references.
4. Save it as a XML file.
5. A live demo is available [here](https://excite.informatik.uni-stuttgart.de/seganno/)
6. A video tutorial to learn how to use this tool is available [here](https://www.youtube.com/watch?v=xwed_XugR7E)

#### Sample File To Use
* Sample files to test are available [here](https://github.com/exciteproject/EXannotator/tree/master/Files_for_test/EXRef-Identifier)
* The layout file extracted from pdf file by using [Refex](https://github.com/exciteproject/refext).

#### Output Sample
Output File will be in XML Format. The following is part of output for a segmented reference string:

```html
...
<author><surname>er</surname>, W./Gürtler, <given-names>M.</given-names></author> (<year>2006</year>)
<article-title>: “Performance Evaluation, Portfolio Selection, and HARA Utility”</article-title>, 
<source>European Journal of Finance</source>, Vol. <volume>18</volume>, pp. 
<fpage>649</fpage>-<lpage>669</lpage>. - Breuer, W./Gürtler, M./Schuhmacher,
...
```
