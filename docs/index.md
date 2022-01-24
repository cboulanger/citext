# EXcite Citation Identification and Segmentation 

With this app, you can mark up citation data in text extracted from a PDF. The reference data can then be exported to 
[Zotero](https://zotero.org) or can be used to train the EXcite reference extraction model. 

For information on installing the application, see [here](../README.md).

## Mark up citation data 

1. Load a text to mark up. This can be done in several ways:

   1. Load a PDF with the "Load" button and extract text and references using the "Identification" button. If your model is
      good, you can choose the "Extract references from PDF" option. This will try to automatically identify the references in
      the document. In case the model does not yet recognize the references correctly, choose "Extract text from PDF" to do
      the mark up manually.
   2. Load a PDF using the "Load from Zotero" button in the dropdown of the "Load button". This will load the PDF
      attachment of the currently selected item in Zotero - then proceed with 1.1
   3. Load a previously processed file (.csv) to continue working on it.
   4. Load a textfile (.txt) containing OCR data. 
   5. Load an XML file with segmented references.
   
2. Mark up the text or correct the automatically produced markup by selecting the parts of the text that contains
   citation/reference data.

   1. After selecting text, a menu popup is shown with the available options. Long-clicking or
      tapping on a marked up section of a text will select it. 
   2. To see the resulting markup, click on the ![](/Users/cboulanger/Code/excite-docker/docs/images/button-preview.png) 
      button.
   3. details, see the [information on training the reference extraction
      model](https://exparser.readthedocs.io/en/latest/ReferenceExtraction/). 
   
4. After you have finished identifying the references, save the training document to the backend. You can also download
   it to your computer using the "Export" button.

5. Switch to segmentation mode by clicking the "Segmentation" button.

   1. To automatically segment the references, click on the "Auto-Segmentation" option from the "Segmentation" dropdown.
      Correct the segmentation or mark up the individual segments of the citations. 

   2. To see the resulting markup, click on
      the ![](/Users/cboulanger/Code/excite-docker/docs/images/button-preview.png) button. For details, see the [information
      on training the reference parsing model](https://exparser.readthedocs.io/en/latest/ReferenceParsing/). 
   
   3. When you are finished, click on "Save" or "Export" to save your changes to the training backend or to your computer.
      You can also export the citation data to Zotero using the "Export to Zotero" button in the dropdown menu.

