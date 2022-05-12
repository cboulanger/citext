# EXparser extraction and segmentation engine

Before being able to extract and segment files, it is important to train the
models. The following scripts are used:

- **`Feature_Extraction.py`**: Extracts the features from each line of the
  document. The input in the extracted content+layout information found in LYT/.
  Outputs data into `Features/` and `Features/tmp/` (which can be removed after
  the end of the process)
  
- **`Txt2Vec.py`**: Extracts the type of the line (0: non reference line, 1:
  first reference line, 2: intermediate reference line, 3: last reference line)

- **`Training_Seg.py`**: Creates the model for reference extraction.

- **`Training_Ext.py`**: Creates the model for reference segmentation.

- **`Training_Com.py`**: Creates the model for reference completeness
    
Note: The first time you use the tool in a new envirment, all the models have to
be trained from the beginning to avoid any ambiguity.
    
To extract and segment the references with the pretrained model, only one script
needs to be called: **`Segment_F1.py`**, which calls all the needed models,
functions and other modules.
    
    Then: 
    1) for each file do :
        fname='file.csv'                            #Name of the file that contains layout information 
        file=open(fname,'rb')
        reader=file.read()
        file.close()
        txt,valid,_,ref_prob0=ref_ext(reader)
        txt,valid,ref_prob0=filtering_ref(txt,valid,ref_prob0)   #uncomment this line if you deal with double column documents. Comment it otherwise.
        refs=segment(txt,ref_prob0,valid)
        reslt,refstr,retex=sg_ref(txt,refs,2)
        
        
    2) To segment a specific line do:
        a,b,c=main_sg(ln,op)            #in_arguments: ln is the string, op is an option (1 for output with probability, 2 for output without probability)
                                        #out_arguments:  a is a vector of probabilities corresponding to tokens
                                                        #b is a vector of labels corresponding to tokens
                                                        #c is xml output that contains probability (op=1) or without probability (op=2)
        for BibTex output do:
            d = refToBibtex(id,c.encode('utf-8'),'article',True)        #in_arguments: id is a id number, c is the output of main_sg
                                                                        #out_arguments: d is the BibTex format of c
