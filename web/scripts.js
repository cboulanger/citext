// noinspection JSJQueryEfficiency

let zoteroAttachmentFilepath;
let modelName = "default"

class Config {
  /* The url of the exparser backend */
  static SERVER_URL = "/cgi-bin/";
  /* The url of the server endpoint that proxies the zotero connection server */
  static ZOTERO_PROXY_URL = Config.SERVER_URL + "zotero/proxy.py";
  static ENGINES = {
    ANYSTYLE: "anystyle",
    EXPARSER: "exparser"
  }
  static LOCAL_STORAGE = {
    DOCUMENT: "excite_document",
    REFERENCES: "excite_references",
    TEXT_FILE_NAME: "excite_text_file_name",
    PDF_IFRAME_SRC: "excite_pdf_iframe_source",
    DISPLAY_MODE: "excite_display_mode",
    LAST_LOAD_URL: "excite_last_load_url",
    LAST_MODEL_NAME: "excite_last_model_name"
  }
  static REGEX = {
    TAG: /<\/?[^>]+>/g,
    SPAN: /<\/?span[^>]*>/ig,
    DIV: /<\/?div[^>]*>/ig,
    BR: /<br[^>]*>/ig,
    PUNCTUATION: /\p{P}/gu,
    LAYOUT: /(\t[^\t]+){6}/g,
    EMPTY_NODE: /<[^>]+><\/[^>]+>/g,
    DATA_TAG_SPAN: /<span data-tag="([^"]+)"[^<]*>([^<]*)<\/span>/gm
  }
  static KNOWN_IDENTIFIERS = [
    {
      startsWith: "10.",
      cslJson: "doi",
      zoteroField: "DOI"
    },
    {
      startsWith: "978",
      cslJson: "isbn",
      zoteroField: "ISBN"
    }
  ]
}

class Actions {
  static parserEngine;

  static setParserEngine(parser) {
    if (parser === this.parserEngine) {
      return
    }
    GUI.update()
    this.parserEngine = parser
  }

  static load() {
    const uploadBtn = document.getElementById("btn-upload");
    switch (uploadBtn.files.length) {
      case 0:
        alert("Please select at least one file.");
        return false;
      case 1:
      case 2:
        break;
      default:
        alert('Please select less than 3 files.');
        return false;
    }
    for (let file of uploadBtn.files) {
      this.loadFile(file);
    }
  }

  static async loadFromUrl(url, filename) {
    url = url || prompt(
      "Please enter a URL from which to load the file:",
      localStorage.getItem(Config.LOCAL_STORAGE.LAST_LOAD_URL) || "");
    if (url === null) return;
    localStorage.setItem(Config.LOCAL_STORAGE.LAST_LOAD_URL, url);
    let here = new URL(document.URL);
    let there = new URL(url);
    let res;
    if (here.host === there.host) {
      res = await fetch(url);
    } else {
      res = await fetch(`/cgi-bin/load-from-url.py?url=${url}`)
    }
    let blob = await res.blob();
    filename = filename || url.split("/").pop();
    let file = new File([blob], filename, {lastModified: 1534584790000});
    this.loadFile(file);
  }

  static async loadFromZotero() {
    try {
      GUI.showSpinner("Loading PDF of first selected Zotero item...");
      let {libraryID, selectedItems} = await Zotero.getSelection();
      if (selectedItems.length === 0) {
        throw new Error("No item selected in Zotero");
      }
      // if attachment is selected, use this, otherwise retrieve attachment
      let firstSelectedItem = selectedItems[0];
      /** @type {{filepath, title, editor, fpage, lpage}} **/
      let attachment;
      let filename;
      if (firstSelectedItem.itemType === "attachment") {
        attachment = firstSelectedItem;
        filename = attachment.key + ".pdf"
      } else {
        let key = firstSelectedItem.key;
        let attachments = await Zotero.getItemAttachments(libraryID, [key]);
        if (attachments[key].length === 0) {
          throw new Error(`The item titled "${firstSelectedItem.title}" has no attachments`);
        }
        attachment = attachments[key].find(attachment => attachment.contentType === "application/pdf");
        if (!attachments) {
          throw new Error(`The item titled "${firstSelectedItem.title}" has no PDF attachment`);
        }
        if (firstSelectedItem.DOI) {
          filename = firstSelectedItem.DOI.replace(/\//g, "_") + ".pdf"
        } else {
          filename = attachment.key + ".pdf"
        }
      }
      if (!attachment.filepath) {
        throw new Error(`Attachment ${attachment.title} has not been downloaded`);
      }
      let filepath = attachment.filepath;
      let s;
      if (filepath.match(/\\/)) {
        // windows filepath
        s = filepath.split(/\\/)
      } else {
        // linux/mac
        s = filepath.split("/");
      }
      zoteroAttachmentFilepath = s.slice(s.indexOf("storage") + 1).join("/");
      await this.loadFromUrl("file://zotero-storage/" + zoteroAttachmentFilepath, filename)
    } catch (e) {
      alert(e.message);
    } finally {
      GUI.hideSpinner()
    }
  }

  static loadFile(file) {
    let fileName = file.name;
    // FIXME ad-hoc filename fix to remave ".pdfa" infix, needs to be configurable
    fileName = fileName.replace(/\.pdfa\./, ".")
    let fileType = file.type;
    let fileExt;
    if (fileName) {
      fileType = fileExt = fileName.split('.').pop();
    } else if (fileType) {
      // remove encoding etc.
      fileType = fileType.split(";").shift().trim();
    } else {
      alert("Cannot determine file type for " + fileName);
      return;
    }
    console.log(`Loading ${fileName} of type ${fileType}`)
    let annotation;
    switch (fileType) {
      case "pdf":
      case "application/pdf":
        GUI.pdfFileName = fileName;
        GUI.pdfFile = file;
        let objectURL = URL.createObjectURL(file);
        GUI.loadPdfFile(objectURL);
        GUI.setPdfFileName(fileName)
        return;
      case "xml":
      case "application/xml":
      case "txt":
      case "text/plain":
      case "csv":
      case "text/csv":
      case "ttx":
        break;
      default:
        alert("Invalid file extension: " + fileExt);
        return;
    }
    // load file and determine type of Annotation
    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      let text = String(e.target.result);
      switch (fileType) {
        case "xml":
        case "text/xml":
        case "application/xml":
          if (text.includes("<dataset>")) {
            annotation = new AnystyleParserAnnotation(text, fileName)
          } else if (text.includes("<surname>")) {
            annotation = new ExparserSegmentationAnnotation(text, fileName)
          } else {
            alert("Unknown XML format")
            return
          }
          break;
        case "csv":
        case "text/csv":
          annotation = new ExparserExtractionAnnotation(text, fileName)
          break
        case "text/plain":
        case "txt":
        case "ttx":
          annotation = new AnystyleFinderAnnotation(text, fileName)
          break;
        default:
          alert("Unknown file type: " + fileType);
          return;
      }
      GUI.loadAnnotation(annotation);
    }
    fileReader.readAsText(file, "UTF-8");
  }

  static addTag(tag_name, wholeLine = false) {
    GUI.addTag(tag_name, wholeLine);
  }

  static removeTag() {
    GUI.saveState();
    let sel = window.getSelection();
    if (!sel) return;
    let el = sel.focusNode;
    while (el) {
      if (el.dataset && el.dataset.tag) break;
      el = el.parentElement;
    }
    if (!el) return;
    $(el).contents().unwrap();
    GUI.updateMarkedUpText();
  }

  static removeAllTags(wholeLine = false) {
    GUI.saveState()
    let sel = window.getSelection();
    if (!sel) return;
    if (wholeLine) {
      let startNode = sel.anchorNode;
      while (startNode.previousSibling && startNode.previousSibling.nodeName !== "BR") {
        startNode = startNode.previousSibling;
      }
      let endNode = sel.focusNode;
      while (endNode.nextSibling && endNode.nextSibling.nodeName !== "BR") {
        endNode = endNode.nextSibling;
      }
      if (startNode && endNode) {
        sel.setBaseAndExtent(startNode, 0, endNode, 1);
      }
    }
    if (sel.rangeCount) {
      let container = document.createElement("div");
      for (let i = 0, len = sel.rangeCount; i < len; ++i) {
        container.appendChild(sel.getRangeAt(i).cloneContents());
      }
      let replacementText = container.innerHTML
        .replace(Config.REGEX.BR, "\n")
        .replace(Config.REGEX.TAG, "");
      GUI.replaceSelection(replacementText);
    }
    GUI.updateMarkedUpText();
  }

  static checkResult(result) {
    if (result.error) {
      let error = result.error;
      if (error.split("\n").length > 1) {
        error = error.split("\n").pop();
      }
      console.error(result.error);
      throw new Error(error);
    }
    if (result.success === undefined) {
      throw new Error("Invalid response.");
    }
    return result;
  }

  static previewCitationData() {
    let refs = GUI
      .getTextToExport()
      .split("\n")
      .map(line => Zotero.convertRefsToJson(line));
    let html = `<pre>${JSON.stringify(refs, null, 2)}</pre>`;
    $("#citation-data-preview-body").html(html);
    $("#modal-citation-data-preview").show();
  }

  static async run_cgi_script(name, params) {
    let querystring = Object.keys(params).map(key => key + '=' + params[key]).join('&');
    const url = `${Config.SERVER_URL}/${name}?${querystring}`
    try {
      return await fetch(url)
    } catch (e) {
      console.error(e)
      alert(e.message)
    }
  }

  static async run_excite_command(command) {
    let confirmMsg;
    switch (command) {
      case "ocr":
        confirmMsg = "Are you sure you want to run OCR, and then layout analysis?";
        break;
      case "layout":
        confirmMsg = "Do you want to run layout analysis?";
        break;
      case "exparser":
        confirmMsg = "Do you want to run layout analysis and reference extraction?";
        break;
      case "segmentation":
        if (GUI.displayMode !== GUI.DISPLAY_MODES.REFERENCES) {
          alert("Segmentation can only be run in references view");
          return;
        }
        confirmMsg = "Do you want to run reference text segmentation?";
        break;
      default:
        alert("Invalid command: " + command);
        return;
    }
    confirmMsg += " This will overwrite the current document.";
    if (!confirm(confirmMsg)) {
      return;
    }

    // file upload
    let file;
    let filename;
    if (command === "segmentation") {
      let refs = GUI.getTextToExport().replace(Config.REGEX.TAG, "");
      file = new Blob([refs], {type: "text/plain;charset=utf8"});
      filename = GUI.getAnnotation().getFileName().split('.').slice(0, -1).join(".") + ".csv";
    } else if (GUI.pdfFile) {
      file = GUI.pdfFile;
      filename = GUI.pdfFileName;
    }
    let filenameNoExt = filename.split('.').slice(0, -1).join(".");
    if (file) {
      let formData = new FormData();
      formData.append("file", file, filename);
      GUI.showSpinner("Uploading...");
      try {
        this.checkResult(await (await fetch(`${Config.SERVER_URL}/upload.py`, {
          method: 'post', body: formData
        })).json());
      } catch (e) {
        return alert(e.message);
      } finally {
        GUI.hideSpinner();
      }
    }
    let result;
    let url;
    let textContent;

    // OCR
    if (command === "ocr") {
      GUI.showSpinner("Running OCR, please be patient...");
      url = `${Config.SERVER_URL}/excite.py?command=ocr&file=${filenameNoExt}`
      try {
        this.checkResult(await (await fetch(url)).json());
      } catch (e) {
        return alert(e.message);
      } finally {
        GUI.hideSpinner();
      }
    }

    // layout
    if (command === "layout" || command === "exparser" || command === "ocr") {
      GUI.showSpinner("Analyzing Layout...");
      url = `${Config.SERVER_URL}/excite.py?command=layout&file=${filenameNoExt}&model_name=${modelName}`
      try {
        result = this.checkResult(await (await fetch(url)).json());
      } catch (e) {
        return alert(e.message);
      } finally {
        GUI.hideSpinner();
      }
      if (result.success === "") {
        if (confirm("No text could be found in document. Run OCR?")) {
          await this.run_excite_command("ocr");
        }
        return;
      }
      GUI.setTextFileName(filenameNoExt + ".csv");
      textContent = result.success;
      GUI.setDisplayMode(GUI.DISPLAY_MODES.DOCUMENT);
      $("#btn-run-exparser").removeClass("ui-state-disabled")
    }

    // reference identification
    if (command === "exparser") {
      GUI.showSpinner("Identifying references, this will take a while...");
      url = `${Config.SERVER_URL}/excite.py?command=exparser&file=${filenameNoExt}&model_name=${modelName}`
      try {
        result = this.checkResult(await (await fetch(url)).json());
      } catch (e) {
        return alert(e.message);
      } finally {
        GUI.hideSpinner();
      }
      let refs = result.success;
      textContent = this.combineLayoutAndRefs(textContent, refs);
      GUI.setDisplayMode(GUI.DISPLAY_MODES.DOCUMENT);
    }
    // segmentation
    if (command === "segmentation") {
      GUI.showSpinner("Segmenting references...");
      url = `${Config.SERVER_URL}/excite.py?command=segmentation&file=${filenameNoExt}&model_name=${modelName}`;
      try {
        result = await (await fetch(url)).json();
        this.checkResult(result)
      } catch (e) {
        return alert(e.message);
      } finally {
        GUI.hideSpinner();
      }
      textContent = result.success;
      GUI.setDisplayMode(GUI.DISPLAY_MODES.REFERENCES);
    }
    GUI.setHtmlContent(textContent);
  }

  static extractReferences(markedUpText) {
    let textLines = markedUpText.split("\n");
    // remove cermine layout info if exists
    textLines = textLines.map(line => line.split('\t').shift())
    let tmp = textLines
      //  .map(line => line.trim().replace(/[-]$/, "~~HYPHEN~~"))
      .join(" ")
    //  .replace(/~~HYPHEN~~ /g, "");
    textLines = [];
    for (let match of tmp.matchAll(/<ref[^>]*>(.*?)<\/ref[^>]*>/g)) {
      textLines.push(match[1]);
    }
    let text = textLines.filter(line => Boolean(line.trim())).join("\n");
    // redundant?
    while (text.match(/\n\n/)) {
      text = text.replace(/\n\n/g, "\n");
    }
    return text;
  }

  static combineLayoutAndRefs(layoutDoc, refs) {
    // combine layout doc and references
    let words = layoutDoc.replace(/\n/g, "~~~CR~~~ ").split(" ");
    refs = refs.split('\n').filter(Boolean);
    for (let ref of refs) {
      let refWords = ref.split(" ");
      // try to match each occurrence of the first word of the reference
      // this currently misses words of the end of line
      let indices = words.map((word, index) => word === refWords[0] ? index : '').filter(String);
      for (let index of indices) {
        let i;
        for (i = 1; i < refWords.length; i++) {
          // compare ref word with tags and punctuation removed ...
          let refWord = refWords[i]
            .replace(Config.REGEX.TAG, "")
            .replace(Config.REGEX.PUNCTUATION, "")
            .trim();
          // ... with current word without tags. punctuation and layout info
          let currWord = words[index + i]
            .replace(Config.REGEX.TAG, "")
            .replace(Config.REGEX.PUNCTUATION, "")
            .replace(Config.REGEX.LAYOUT, "")
            .trim();
          // if word ends with a hyphen, join with next word if exists
          if (currWord.match(/\p{Pd}/gu) && words[index + i + 1]) {
            currWord = currWord + words[index + i + 1]
              .replace(Config.REGEX.TAG, "")
              .replace(Config.REGEX.PUNCTUATION, "")
              .replace(Config.REGEX.LAYOUT, "")
              .trim();
          }
          if (refWord === currWord) continue;
          // not found
          break;
        }
        if (i === refWords.length) {
          // found! add tags
          words[index] = "<ref>" + words[index];
          words[index + i - 1] += "</ref>";
        }
      }
    }
    layoutDoc = words
      .join(" ")
      .replace(/~~~CR~~~/g, "\n")
    return layoutDoc
  }

  static _export() {
    let textToExport;
    let filename;
    let filenameNoExt = GUI.getAnnotation().getFileName().split('.').slice(0, -1).join(".");
    switch (GUI.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        if (this.parserEngine === "exparser") {
          textToExport = GUI.getTextToExport();
          filename = filenameNoExt + ".csv";
        } else {

          textToExport = ttxLines.join("\n")
          filename = filenameNoExt + ".ttx";
        }
        break;
      case GUI.DISPLAY_MODES.REFERENCES:
        let rootTag, sequenceTag;
        if (this.parserEngine === "exparser") {
          sequenceTag = "ref"
          rootTag = "seganno"
        } else {
          // anystyle
          sequenceTag = "sequence"
          rootTag = "dataset"
        }
        textToExport = GUI.getTextToExport(false)
          .split("\n")
          .map(line => `<${sequenceTag}>${line}</${sequenceTag}`)
          .join("\n");
        textToExport = `<?xml version="1.0" encoding="utf-8"?>\n<${rootTag}>\n${textToExport}\n</${rootTag}>`
        filename = filenameNoExt + ".xml";
        break;
    }
    return {textToExport, filename};
  }

  static export() {
    if (!GUI.getAnnotation().getFileName()) return;
    let {textToExport, filename} = this._export()
    Utils.download(textToExport, filename);
  }

  static async exportToZotero() {
    if (GUI.displayMode !== GUI.DISPLAY_MODES.REFERENCES) {
      alert("You must be in segmentation mode to export references");
      return;
    }
    let refs = GUI.getTextToExport(false);
    if (!refs.match(Config.REGEX.TAG)) {
      alert("No references to export");
      return;
    }
    let id = GUI.getAnnotation().getFileName().split(".").slice(0, -1).join(".");
    let identifier;
    for (let knownIdentifier of Config.KNOWN_IDENTIFIERS) {
      if (id.startsWith(knownIdentifier.startsWith)) {
        identifier = knownIdentifier;
        break;
      }
    }
    // work around DOIs in filenames where the illegal "/" has been replaced by underscore
    if (identifier && identifier.zoteroField === "DOI" && !id.includes("/") && id.includes("_")) {
      id = id.replace("_", "/"); // only replaces first occurrence
    }
    refs = refs.split("\n");
    let msg;
    // abort requests on escape key  press
    const abortFunc = e => e.key === "Escape" && Zotero.controller.abort();
    $(document).on('keydown', abortFunc);
    try {
      GUI.showSpinner("Connecting to Zotero...");
      let zSelection = await Zotero.getSelection();
      let libraryID = zSelection.libraryID;
      let targetItem = zSelection.selectedItems.length ? zSelection.selectedItems[0] : null;
      if (identifier) {
        if (!libraryID) {
          throw new Error("Please select a library in Zotero");
        }
        let query = {};
        let field = identifier.zoteroField;
        query[field] = ["is", id];
        GUI.showSpinner(`Searching Zotero for ${field} ${id}`);
        let items = await Zotero.search(libraryID, query);
        if (items.length === 0) {
          throw new Error(`Identifier ${identifier.zoteroField} ${id} cannot be found in the library.`);
        } else if (items.length > 1) {
          throw new Error(`Identifier ${identifier.zoteroField} ${id} exists twice - please merge items manually first.`);
        }
        targetItem = items[0];
      } else if (!targetItem) {
        throw new Error("No identifier or selected item can be determined.");
      }
      GUI.showSpinner(`Retrieving citations...`);
      const citations = await Zotero.listCitations(libraryID, targetItem.key);
      console.log({citations});
      msg = `Do you want to export ${refs.length} references to "${targetItem.title}"?`;
      if (!confirm(msg)) return;
      let total = refs.length;
      // loop through all the cited references
      for (let [count, ref] of refs.entries()) {
        let msg = ` item ${count + 1} of ${total} cited references. Press the Escape key to abort.`;
        GUI.showSpinner("Identifying " + msg);
        let item = Zotero.convertRefsToJson(ref);
        let {creators, title, date} = item;
        let creator = creators?.[0]?.lastName || "";
        // search
        let wc = 0;
        let titleWords = title
            ?.split(" ")
            .filter(w => w.length > 4 && ++wc < 4)
            .map(w => w.replace(/^\p{P}|\p{P}$/gu, ""))
            .join(" ")
          || title;
        let query = {
          "quicksearch-titleCreatorYear": ["contains", `${creator || ""} ${titleWords || ""} ${date || ""}`]
        }
        let itemKey;
        let foundItems = await Zotero.search(libraryID, query, "items");
        if (foundItems.length) {
          // if we have several entries, user should select but we're taking the first matching one for now
          let foundItem = foundItems.find(foundItem => item.itemType === foundItem.itemType);
          if (foundItem) {
            // merge properties from exparser into found item without overwriting any existing ones
            let newItem = Object.assign(item, foundItem);
            // update only if properties have been added
            let newItemHasMoreProperties =
              Object.values(newItem).filter(Boolean).length > Object.values(item).filter(Boolean).length;
            if (newItemHasMoreProperties) {
              console.log({info: "Updating item", item});
              GUI.showSpinner("Updating" + msg);
              await Zotero.updateItems(libraryID, [newItem]);
            }
            itemKey = foundItem.key;
          }
        }
        if (!itemKey) {
          GUI.showSpinner("Creating" + msg);
          console.log({info: "Creating item", item});
          ([itemKey] = await Zotero.createItems(libraryID, [item]));
        }
        if (citations.find(citation => citation.zotero === itemKey)) {
          console.log("Citation already linked.");
          continue;
        }
        GUI.showSpinner("Linking" + msg);
        let result = await Zotero.addCitations(libraryID, targetItem.key, [itemKey]);
        console.log(result);
      }
    } catch (e) {
      console.error(e);
      alert(e.message);
    } finally {
      $(document).off('keypress', abortFunc);
      GUI.hideSpinner();
    }
  }

  static async save() {
    let filename = GUI.getAnnotation().getFileName();
    if (!filename) return;
    let data;
    let type;
    let filenameNoExt = filename.split('.').slice(0, -1).join(".");
    switch (GUI.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        data = GUI.getTextToExport();
        localStorage.setItem(Config.LOCAL_STORAGE.DOCUMENT, data);
        localStorage.setItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME, filename);
        if (this.parserEngine === "exparser") {
          type = "layout"
          break
        }
        type = "anystyle_finder";
        data = this._export().textToExport;
        break;
      case GUI.DISPLAY_MODES.REFERENCES:
        data = GUI.getTextToExport(false);
        localStorage.setItem(Config.LOCAL_STORAGE.REFERENCES, data);
        filename = filenameNoExt + ".xml";
        if (this.parserEngine === "exparser") {
          type = "ref_xml"
          break
        }
        type = "anystyle_parser"
        data = this._export().textToExport;
        break;
    }
    if (!confirm(`Save training data to model '${modelName}?'`)) return
    GUI.showSpinner(`Saving training data.`);
    let body = JSON.stringify({filename, type, data, modelName}) + "\n\n";
    let result = await (await fetch(`${Config.SERVER_URL}/save.py`, {
      method: 'post', body
    })).json();
    GUI.hideSpinner();
    if (result.error) alert(result.error);
  }

  static undo() {
    if (this.versions.length) {
      $("#text-content").html(this.versions.pop());
      GUI.updateMarkedUpText();
    }
    if (!this.versions.length) {
      $("#btn-undo").addClass("ui-state-disabled")
    }
  }

  static setDisplayMode(nextDisplayMode) {
    if (this.displayMode === nextDisplayMode) {
      return;
    }
    let text
    switch (this.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        let document = GUI.getTextToExport();
        localStorage.setItem(Config.LOCAL_STORAGE.DOCUMENT, document);
        text = this.extractReferences(document);
        localStorage.setItem(Config.LOCAL_STORAGE.REFERENCES, text);
        break;
      case GUI.DISPLAY_MODES.REFERENCES:
        if (this.versions.length > 0) {
          let confirmMsg = `This will switch the display to ${nextDisplayMode} view and discard any changes. Do you want to proceed?`;
          if (!confirm(confirmMsg)) {
            $("#btn-identification").removeClass("active");
            return;
          }
        }
        text = localStorage.getItem(Config.LOCAL_STORAGE.DOCUMENT) || "";
        break;
    }
    GUI.setDisplayMode(nextDisplayMode);
    GUI.setHtmlContent(text);
    this.versions = [];
    $("#btn-undo").addClass("ui-state-disabled");

  }

  static changeModel(name) {
    $("#btn-model-" + modelName).removeClass("btn-dropdown-radio-selected");
    modelName = name;
    $("#btn-model-" + modelName).addClass("btn-dropdown-radio-selected");
    localStorage.setItem(Config.LOCAL_STORAGE.LAST_MODEL_NAME, name);
  }
}

class Zotero {

  /** @type {AbortController} */
  static controller;

  // timeout 2 minutes
  static timeout = 2 * 60 * 1000;
  static isTimeout = false;
  static numberTimeouts = 0;

  static API_ENDPOINT = "zotero-api-endpoint";

  static API = {
    SELECTION_GET: this.API_ENDPOINT + "/selection/get",
    ITEM_ATTACHMENT_GET: this.API_ENDPOINT + "/attachment/get",
    LIBRARY_SEARCH: this.API_ENDPOINT + "/library/search",
    ITEM_CREATE: this.API_ENDPOINT + "/item/create",
    ITEM_UPDATE: this.API_ENDPOINT + "/item/update",
    CITATION_ADD: "cita/citation/add",
    CITATION_LIST: "cita/citation/list"
  }

  /**
   * Call the local Zotero server
   * @param {string} endpoint
   * @param {any} postData
   * @returns {Promise<*>}
   */
  static async callEndpoint(endpoint, postData = null) {
    this.controller = new AbortController();
    this.isTimeout = false;
    const timeoutFunc = () => {
      this.isTimeout = true;
      this.controller.abort();
    };
    const id = setTimeout(timeoutFunc, this.timeout);
    let result;
    try {
      let response = await fetch(Config.ZOTERO_PROXY_URL + "?" + endpoint, {
        method: postData ? "POST" : "GET",
        cache: 'no-cache',
        signal: this.controller.signal,
        headers: {
          'Content-Type': 'application/json'
        },
        body: postData ? JSON.stringify(postData) + '\r\n' : null
      });
      result = await response.text();
      if (result.includes("Endpoint")) {
        throw new Error(result.replace("Endpoint", "Endpoint " + endpoint));
      }
      result = JSON.parse(result);
      if (result.error) {
        throw new Error(result.error);
      }
      return result;
    } catch (e) {
      if (e.name === "AbortError" && this.isTimeout) {
        if (++this.numberTimeouts < 3) {
          return await this.callEndpoint(endpoint, postData);
        }
        this.numberTimeouts = 0;
        e = new Error(`Timeout trying to reach ${endpoint} (tried 3 times).`);
      }
      throw e;
    } finally {
      clearTimeout(id);
    }
  }

  /**
   * @param {string} ref
   * @returns {{date: *, volume: *, pages: (*|undefined), issue: *, ISBN: (*|undefined), creators: *[], publisher: *, title: *, publicationTitle: *, URL: *, DOI: (*|undefined)}}
   */
  static convertRefsToJson(ref) {
    function extract(tagName, text) {
      let regexp = new RegExp(`<${tagName}>(.*?)</${tagName}>`, "g");
      let m;
      let result = [];
      while (m = regexp.exec(text)) {
        result.push(m[1])
      }
      return result.length ? result : undefined;
    }

    let tags = [
      "author", "title", "source",
      "editor", "year", "volume", "issue",
      "publisher", "fpage", "lpage", "url", "identifier"
    ];
    const r = {};
    for (let tag of tags) {
      r[tag] = extract(tag, ref);
    }
    let creators = [];
    if (r.author) {
      for (let author of r.author) {
        const firstName = extract("given-names", author)?.[0];
        const lastName = extract("surname", author)?.[0];
        if (firstName && lastName) {
          creators.push({
            "creatorType": "author",
            firstName,
            lastName
          });
        } else {
          creators.push({
            "creatorType": "author",
            "name": lastName || firstName
          });
        }
      }
    }
    if (r.editor) {
      for (let editor of r.editor) {
        creators.push({
          "creatorType": "editor",
          "name": editor
        });
      }
    }
    let item = {
      creators,
      "title": r.title?.[0],
      "date": r.year?.[0],
      "volume": r.volume?.[0],
      "issue": r.issue?.[0],
      "publisher": r.publisher?.[0],
      "pages": r.fpage?.[0] ? (r.fpage?.[0] + (r.lpage?.[0] ? "-" + r.lpage?.[0] : "")) : undefined,
      "URL": r.url?.[0],
      "DOI": r.identifier?.[0]?.startsWith("10.") ? r.identifier?.[0] : undefined,
      "ISBN": r.identifier?.[0]?.startsWith("978") ? r.identifier?.[0] : undefined,
    };
    let source = r.source?.[0];
    if (!source) {
      item.itemType = "book";
      delete item.pages;
      delete item.issue;
    } else if (item.publisher || !item.volume) {
      item.itemType = "bookSection";
      item.bookTitle = source;
      delete item.issue;
    } else {
      item.itemType = "journalArticle";
      item.publicationTitle = source;
      delete item.publisher;
    }
    return item;
  }

  /**
   * Returns a map of keys and items
   * @param {number} libraryID
   * @param {string[]} keys
   * @returns {Promise<{}>}
   */
  static async getItemAttachments(libraryID, keys) {
    return await this.callEndpoint(this.API.ITEM_ATTACHMENT_GET, {
      libraryID, keys
    });
  }

  /**
   * @returns {Promise<{libraryID: number|null, groupID: number|null, selectedItems: object[], collection: string|null, childItems: object[]}>}
   */
  static async getSelection() {
    return await this.callEndpoint(this.API.SELECTION_GET);
  }

  /**
   * @param {number} libraryID
   * @param {object} query
   * @param {string} resultType
   * @returns {Promise<object[]>}
   */
  static async search(libraryID, query, resultType = "items") {
    return await this.callEndpoint(this.API.LIBRARY_SEARCH, {
      libraryID,
      query,
      resultType
    })
  }

  /**
   * Create one or more new items in a Zotero library
   * @param {number} libraryID
   * @param {object[]} items
   * @param {string[]|null} collections
   * @returns {Promise<string[]>}
   */
  static async createItems(libraryID, items, collections = null) {
    return await this.callEndpoint(this.API.ITEM_CREATE, {
      libraryID,
      collections,
      items
    });
  }

  /**
   * Update one or more new items in a Zotero library
   * @param {number} libraryID
   * @param {object[]} items
   * @returns {Promise<string[]>}
   */
  static async updateItems(libraryID, items) {
    return await this.callEndpoint(this.API.ITEM_UPDATE, {
      libraryID,
      items
    });
  }


  /**
   * Add items in a Zotero library as citations to a source item
   * @param {number} libraryID  The library ID for the source and cited items
   * @param {string} sourceItemKey The item key of the source item
   * @param {string[]} citedItemKeys An array of the item keys for the cited items
   * @returns {Promise<string>} statusMessage - Result of the operation.
   */
  static async addCitations(libraryID, sourceItemKey, citedItemKeys) {
    return await this.callEndpoint(this.API.CITATION_ADD, {
      libraryID,
      sourceItemKey,
      citedItemKeys
    });
  }

  /**
   * list the cited references of an item
   * @param {number} libraryID  The library ID for the source and cited items
   * @param {string} sourceItemKey The item key of the source item
   * @returns {Promise<object[]>} statusMessage - Result of the operation.
   */
  static async listCitations(libraryID, sourceItemKey) {
    return await this.callEndpoint(this.API.CITATION_LIST, {
      libraryID,
      sourceItemKey
    });
  }
}

class Utils {

  static download(data, filename) {
    const file = new Blob([data], {type: 'text/xml;charset=utf-8;'});
    const a = document.createElement("a");
    const url = URL.createObjectURL(file);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 0);
  }
}

class Excite {
  static async trainCurrentModel() {
    await Actions.run_cgi_script("train.py", {id: Config.channel_id, model_name: modelName})
  }

  static async evalCurrentModel() {
    await Actions.run_cgi_script("eval.py", {id: Config.channel_id, model_name: modelName})
  }
}

Config.channel_id;

class GUI {
  static annotation;
  static displayMode;
  static versions;
  static DISPLAY_MODES = {
    DOCUMENT: "document",
    REFERENCES: "references"
  }
  static pdfFile;
  static pdfFileName;

  static init() {
    // internal vars
    this.__numPages = 0;
    this.__currentPage = 1;
    this.__currentRefNode = null;
    this.__markupViewState = false;
    this.__pdfJsApplication = null;

    $(() => {
      this._setupEventListeners();
      GUI.toggleMarkedUpView(false);
      let hash = (new URL(document.URL)).hash;
      let lastLoadUrl = localStorage.getItem(Config.LOCAL_STORAGE.LAST_LOAD_URL) || false;
      let downloadUrl = hash.startsWith("#load=") && hash.substr(6).trim();
      let textInLocalStorage = this._hasTextInLocalStorage();
      if (textInLocalStorage && !(downloadUrl !== lastLoadUrl)) {
        console.log("Loading document from local storage.");
        this._loadTextFromLocalStorage();
        return;
      } else if (lastLoadUrl && (!downloadUrl || downloadUrl === lastLoadUrl)) {
        console.log("Loading document from stored URL: " + lastLoadUrl)
        Actions.loadFromUrl(lastLoadUrl).catch(console.error);
        return;
      } else if (downloadUrl) {
        console.log("Loading document from URL hash: " + downloadUrl)
        Actions.loadFromUrl(downloadUrl).catch(console.error);
        return;
      }
      $("#modal-help").show();
    });

    // save text before leaving the page
    window.onbeforeunload = Actions.saveToLocalStorage;

    // check if we have a backend and intialize UI
    fetch(Config.SERVER_URL + "status.py")
      .then(response => response.json())
      .then(result => GUI._configureStatus(result))

    // check if Zotero is running
    fetch(Config.SERVER_URL + "zotero/proxy.py?connector/ping")
      .then(response => response.text())
      .then(result => $(".visible-if-zotero-connection")
        .toggleClass("hidden", !result.includes("Zotero Connector Server is Available")));

    // SSE
    const channel_id = Config.channel_id = Math.random().toString().slice(2)
    const source = new EventSource(Config.SERVER_URL + "sse.py?" + channel_id);
    let toasts = {};
    source.addEventListener("open", () => {
      console.log("Initialized SSE connection with id " + channel_id)
    })
    for (let type of ['success', 'info', 'warning', 'error']) {
      source.addEventListener(type, evt => {
        let data = evt.data;
        let title, text;
        let sepPos = data.indexOf(":")
        if (sepPos !== -1) {
          title = data.slice(0, sepPos) || type
          text = data.slice(sepPos + 1)
        } else {
          title = type
          text = data
        }
        //console.log({title, text})
        let toastId = type + "|" + title;
        let toast = toasts[toastId];
        if (toast && toast.css("visibility")) {
          if (text.trim()) {
            toast.find(".toast-message").text(text)
          } else {
            toastr.clear(toast)
          }
        } else if (text.trim()) {
          const onCloseClick = type === "info" ? () => {
            if (confirm("Cancel the current server process?")) {
              Actions.run_cgi_script("abort.py", {id: channel_id})
            }
          } : undefined;
          toast = toastr[type](text, title, {
            positionClass: "toast-bottom-full-width",
            timeOut: 0,
            extendedTimeOut: 0,
            closeButton: true,
            onCloseClick
          })
          toasts[toastId] = toast
        }
      });
      source.addEventListener("debug", evt => {
        console.log(evt.data);
      })
    }

    source.addEventListener("error", evt => {
      console.error("EventSource failed:", evt);
    });
  }

  static _configureStatus(status) {
    $(".visible-if-backend").toggleClass("hidden", false);
    let model_name = localStorage.getItem(Config.LOCAL_STORAGE.LAST_MODEL_NAME) || "default";
    if (status.model_names.length > 1) {
      $("#btn-model").removeClass("hidden");
      status.model_names
        .reverse()
        .forEach(name => $("#model-names").append($(`<li>` +
          `<a class="dropdown-item" href="#" id="btn-model-${name}" onclick="Actions.changeModel('${name}')">${name}</a>` +
          `</li>`)));
    }
    Actions.changeModel(model_name);
  }

  static _setupEventListeners() {
    // show popup on select
    const contextMenu = $("#context-menu");
    const textContent = $("#text-content");
    textContent.on("pointerup", GUI._showPopupOnSelect);
    contextMenu.on("pointerup", () => setTimeout(() => {
      contextMenu.hide();
      window.getSelection().removeAllRanges();
    }, 100));

    // prevent context menu
    textContent.on("contextmenu", e => {
      e.preventDefault();
      e.stopPropagation();
      GUI._showPopupOnSelect(e)
      return false;
    });

    // prevent drag & drop
    $('body').on('dragstart drop', function (e) {
      e.preventDefault();
      return false;
    });

    // remove whitespace from selection after double-click
    textContent.on("dblclick", () => {
      // trim leading or trailing spaces
      let sel = window.getSelection();
      let text = sel.toString();
      let range = sel.getRangeAt(0);
      let endContainer = range.endContainer;
      if (!text.includes(endContainer.textContent)) {
        endContainer = sel.anchorNode;
      }
      let startOffset = text.length - text.trimStart().length;
      let endOffset = text.length - text.trimEnd().length;
      if (startOffset) {
        range.setStart(range.startContainer, range.startOffset + startOffset);
      }
      if (endOffset) {
        range.setEnd(endContainer, Math.max(range.endOffset - endOffset, 0));
      }
      sel.removeAllRanges();
      sel.addRange(range);
    });

    // long-pressing selects span
    let longpress = false;
    textContent.on('click', e => {
      if (!longpress) return;
      let sel = window.getSelection();
      //if (sel.toString().length) return; // so that <oth> element can be inserted into selection
      if (!sel.focusNode || !sel.focusNode.parentElement) return;
      let p = sel.focusNode.parentElement;
      if (e.target !== p) return;
      if (p.dataset && p.dataset.tag) {
        sel.removeAllRanges();
        let range = document.createRange();
        range.selectNodeContents(p);
        sel.addRange(range);
        GUI._showPopupOnSelect(e);
      }
    });
    let startTime, endTime;
    $(document).on('pointerdown', function () {
      startTime = new Date().getTime();
    });
    $(document).on('pointerup', function () {
      endTime = new Date().getTime();
      longpress = (endTime - startTime >= 500);
    });

    // synchronize scroll positions
    textContent.on('scroll', e => {
      $('#markup-content-container').scrollTop(e.currentTarget.scrollTop);
    });

    // force remove PDF because loading saved src doesn't work yet
    //let dataUrl = localStorage.getItem(Config.LOCAL_STORAGE.PDF_IFRAME_SRC);
    //if (dataUrl) {
    //  fetch(dataUrl)
    //    .then(res => res.blob())
    //    .then(objectURL => GUI.loadPdfFile(objectURL));
    //} else {
    GUI.showPdfView(false);
    //}

    // disable checkbox state caching
    $(":checkbox").attr("autocomplete", "off");

    // tooltips
    //$('[data-toggle="tooltip"]').tooltip();
  }

  static _hasTextInLocalStorage() {
    return Boolean(localStorage.getItem(Config.LOCAL_STORAGE.DISPLAY_MODE)) &&
      (Boolean(localStorage.getItem(Config.LOCAL_STORAGE.DOCUMENT)) ||
        Boolean(localStorage.getItem(Config.LOCAL_STORAGE.REFERENCES)));
  }

  static _loadTextFromLocalStorage() {
    let savedDisplayMode = localStorage.getItem(Config.LOCAL_STORAGE.DISPLAY_MODE);
    let savedTextFileName = localStorage.getItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME);
      let text;
    if (savedDisplayMode) {
      switch (savedDisplayMode) {
        case GUI.DISPLAY_MODES.DOCUMENT:
          text = localStorage.getItem(Config.LOCAL_STORAGE.DOCUMENT);
          break;
        case GUI.DISPLAY_MODES.REFERENCES:
          text = localStorage.getItem(Config.LOCAL_STORAGE.REFERENCES);
          break;
        default:
          savedDisplayMode = GUI.DISPLAY_MODES.DOCUMENT;
          text = "";
          break;
      }
      GUI.setDisplayMode(savedDisplayMode);
      if (text) {
        let type = savedTextFileName.endsWith(".xml") ? "text/xml" : "text/plain"
        let file = new File([text], savedTextFileName, {
          lastModified: 1534584790000,
          type: `${type};charset=utf8`
        });
        Actions.loadFile(file)
        return true;
      }
    }
    return false;
  }

  static update() {
    switch (Actions.parserEngine) {
      case Config.ENGINES.EXPARSER:
        $(`li > a.exparser`).removeClass("excluded")
        $(`li > a.anystyle`).addClass("excluded")
        break
      case Config.ENGINES.ANYSTYLE:
        $(`li > a.exparser`).addClass("excluded")
        $(`li > a.anystyle`).removeClass("excluded")
    }
    switch (GUI.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        switch (Actions.parserEngine) {
          case Config.ENGINES.EXPARSER:
            $(".exparser,.visible-in-refs-mode").addClass("excluded")
            $(".exparser,.visible-in-document-mode").removeClass("excluded")
            $(".anystyle,.visible-in-refs-mode").addClass("excluded")
            break
          case Config.ENGINES.ANYSTYLE:
            $(".anystyle,.visible-in-refs-mode").addClass("excluded")
            $(".anystyle,.visible-in-document-mode").removeClass("excluded")
            $(".exparser,.visible-in-refs-mode").addClass("excluded")
        }
        break
      case GUI.DISPLAY_MODES.REFERENCES:
        switch (Actions.parserEngine) {
          case Config.ENGINES.EXPARSER:
            $(".exparser,.visible-in-document-mode").addClass("excluded")
            $(".exparser,.visible-in-refs-mode").removeClass("excluded")
            $(".anystyle,.visible-in-document-mode").addClass("excluded")
            break
          case Config.ENGINES.ANYSTYLE:
            $(".anystyle,.visible-in-document-mode").addClass("excluded")
            $(".anystyle,.visible-in-refs-mode").removeClass("excluded")
            $(".exparser,.visible-in-document-mode").addClass("excluded")
        }
        break
    }
  }

  static showSpinner(text) {
    $("#spinner").attr("data-text", text).addClass("is-active");
  }

  static hideSpinner() {
    $("#spinner").removeClass("is-active");
  }

  static loadAnnotation(annotation) {
    if (!(annotation instanceof Annotation)) {
      throw new Error("Argument must be annotation")
    }
    this.annotation = annotation;
    Actions.setParserEngine(annotation.constructor.engine)
    this.setTextFileName(annotation.getFileName())
    this.setDisplayMode(annotation.type === Annotation.TYPE.FINDER ? GUI.DISPLAY_MODES.DOCUMENT : GUI.DISPLAY_MODES.REFERENCES)
    if (annotation.numPages && annotation.numPages > 0) {
      $("#label-page-number").html("1");
      $(".visible-if-pages").removeClass("hidden").removeClass("excluded");
    } else {
      $("#label-page-number").html("");
      $(".visible-if-pages").addClass("hidden");
    }
    this.setHtmlContent(annotation.toHtml())
    this.saveToLocalStorage()
  }

  static saveToLocalStorage() {
    let text;
    switch (GUI.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        text = GUI.getTextToExport();
        localStorage.setItem(Config.LOCAL_STORAGE.DOCUMENT, text);
        break;
      case GUI.DISPLAY_MODES.REFERENCES:
        text = GUI.getTextToExport();
        localStorage.setItem(Config.LOCAL_STORAGE.REFERENCES, text);
        break;
    }
    localStorage.setItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME, GUI.getAnnotation().getFileName());
    localStorage.setItem(Config.LOCAL_STORAGE.DISPLAY_MODE, GUI.displayMode);
  }

  static setTextFileName(filename) {
    $(".enabled-if-document").addClass("ui-state-disabled");
    $("#text-label").html(filename);
  }

  static setPdfFileName(filename) {
    GUI.pdfFileName = filename
    $("#pdf-label").html(filename);
  }

  static removeTextFile() {
    if (!confirm("Do you really want to clear the document?")) {
      return;
    }
    $("#text-content").html("");
    $("#markup-content").html("");
    $(".view-text-buttons").hide();
    this.setTextFileName("");
    this.annotation = null
    this.versions = [];
    localStorage.removeItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME);
    localStorage.removeItem(Config.LOCAL_STORAGE.DOCUMENT);
    localStorage.removeItem(Config.LOCAL_STORAGE.REFERENCES);
    localStorage.removeItem(Config.LOCAL_STORAGE.LAST_LOAD_URL);
    document.location.href = document.URL.replace(/#.*$/, "#");
    GUI.setDisplayMode(GUI.DISPLAY_MODES.DOCUMENT);
    this.toggleMarkedUpView(false);
  }

  static loadPdfFile(objectURL) {
    const pdfiframe = $("#pdfiframe");
    pdfiframe.on("load", GUI._onPdfIframeLoaded);
    pdfiframe.prop("src", "web/viewer.html?file=" + objectURL);
    GUI.showPdfView(true);
    this.setDisplayMode(GUI.DISPLAY_MODES.DOCUMENT);
    $(".enabled-if-document").removeClass("ui-state-disabled");
    $(".enabled-if-pdf").removeClass("ui-state-disabled");
    $(".visible-if-pdf").addClass("hidden");
  }

  static removePdfFile() {
    $("pdf-label").html("");
    document.getElementById("pdfiframe").src = 'about:blank';
    zoteroAttachmentFilepath = null;
    GUI.pdfFileName = "";
    $(".enabled-if-pdf").addClass("ui-state-disabled");
    $(".visible-if-pdf").addClass("hidden");
    localStorage.removeItem(Config.LOCAL_STORAGE.LAST_LOAD_URL);
    document.location.href = document.URL.replace(/#.*$/, "#");
    GUI.showPdfView(false);
  }

  static findNextRef(offset = 0) {
    const contentDiv = document.getElementById("text-content");
    let currentRefNode = this.__currentRefNode;
    let nodes = Array.from(contentDiv.getElementsByTagName("span"));
    let index;
    if (!currentRefNode) {
      currentRefNode = nodes.find(node => node.dataset.tag === "ref");
      if (!currentRefNode) {
        return;
      }
      index = 0;
    } else {
      index = nodes.findIndex(node => node === currentRefNode);
      if (index < 0 || index + offset === (offset < 0 ? -1 : nodes.length)) {
        return;
      }
      currentRefNode = nodes[index + offset];
    }
    $("btnfindPrevRef").prop("disabled", index < 1);
    $("btnfindNextRef").prop("disabled", index === nodes.length);
    currentRefNode.scrollIntoView({behavior: 'smooth', block: 'center', inline: 'start'});
    this.__currentRefNode = currentRefNode;
    return currentRefNode;
  }

  /**
   * @param {string} html
   */
  static setHtmlContent(html) {
    let htmlContentNode = $("#text-content")
    htmlContentNode.html(html);
    htmlContentNode.scrollTop(0);
    this.versions = [html];
    // select page in PDF if available
    $("#text-content > .page-marker").on("click", e => {
      if (this.__pdfJsApplication) {
        this.goToPdfPage(parseInt((e.target.dataset.page)))
      }
    });
    this.updateMarkedUpText();
    this.__currentRefNode = null;
    // enable buttons
    $(".view-text-buttons").show();
    $(".enabled-if-text-content").removeClass("ui-state-disabled");
  }

  static addTag(tag_name, wholeLine = false) {
    GUI.saveState();
    let sel = window.getSelection();
    let text = sel.toString();
    if (text.trim() === "") return;
    if (wholeLine) {
      sel.setBaseAndExtent(sel.anchorNode, 0, sel.focusNode, sel.focusNode.length);
    }
    // prevent nesting of tag inside other tag
    let node = sel.focusNode;
    if (!node || !node.parentNode) {
      return
    }
    let tag = node.dataset && node.dataset.tag;
    if (tag) {
      // replace node tag
      node.dataset.tag = tag_name;
    } else {
      // wrap selection in new span
      let newParentNode = document.createElement("span");
      newParentNode.setAttribute("data-tag", tag_name);
      sel.getRangeAt(0).surroundContents(newParentNode);
      // remove all <span>s from selected text
      $(newParentNode).html($(newParentNode).html().replace(Config.REGEX.SPAN, ""));
      // check if grandparent node has a tag and split node if so
      let grandParent = newParentNode.parentNode
      let grandParentTag = grandParent.dataset && grandParent.dataset.tag
      if (grandParentTag) {
        if (grandParentTag === tag_name) {
          // if same tag, simply remove the span
          $(grandParent).html($(grandParent).html().replace(Config.REGEX.SPAN, ""));
        } else {
          // split grandparent via regexes
          let outerHTML = grandParent.outerHTML
          grandParent.outerHTML = outerHTML
            .replace(/(?!^)<span/, "</spxn><span")
            .replace(/<\/span>(?!$)/, `</span><span data-tag="${grandParentTag}">`)
            .replace(/<\/spxn>/, "</span>")
            .replace(/(<span [^>]+>)<br ?\/?>/, "<br>$1")
            .replace(/<span[^>]*><\/span>/g, "");
        }
      }
    }
    GUI.updateMarkedUpText();
  }

  static updateMarkedUpText() {
    let html = $("#text-content").html();
    let markedUpText = this.getAnnotation().loadFromHtml(html)
    $("#markup-content").html(markedUpText);
    switch (this.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT: {
        $("#refs-navigation").toggleClass("hidden", !markedUpText.includes("<ref"));
        $(".enabled-if-refs").toggleClass("ui-state-disabled", !(markedUpText.match(Config.REGEX.TAG)));
        break;
      }
      case GUI.DISPLAY_MODES.REFERENCES: {
        $(".enabled-if-refs").removeClass("ui-state-disabled");
        $(".enabled-if-segmented").toggleClass("ui-state-disabled", !(markedUpText.match(Config.REGEX.TAG)));
        break;
      }
    }
    return markedUpText;
  }

  /**
   * Returns the currently loaded Annotation
   * @returns {Annotation|null}
   */
  static getAnnotation() {
    return this.annotation;
  }

  static getTextToExport() {
    return this.getAnnotation().export()
  }

  static toggleMarkedUpView(state) {
    if (state === undefined) {
      state = this.__markupViewState = !this.__markupViewState;
    } else {
      this.__markupViewState = state;
    }
    $(".view-markup")[state ? "show" : "hide"]();
    document.getElementById("main-container").style.gridTemplateRows = state ? "50% 50%" : "100% 0"
  }

  static showPdfView(state) {
    $(".view-pdf")[state ? "show" : "hide"]();
    document.getElementById("main-container").style.gridTemplateColumns = state ? "50% 50%" : "100% 0"
  }

  static setDisplayMode(nextDisplayMode) {
    if (nextDisplayMode === this.displayMode) {
      return;
    }
    this.displayMode = nextDisplayMode;
    switch (this.displayMode) {
      case GUI.DISPLAY_MODES.DOCUMENT:
        $(".enabled-if-document").removeClass("ui-state-disabled")
        $("#btn-segmentation").removeClass("active");
        $("#btn-identification").addClass("active");
        $("#text-content").addClass("document-view");
        $("#text-content").removeClass("references-view");
        break;
      case GUI.DISPLAY_MODES.REFERENCES:
        $(".enabled-if-document").addClass("ui-state-disabled")
        $("#btn-segmentation").addClass("active");
        $("#btn-identification").removeClass("active");
        $("#text-content").addClass("references-view");
        $("#text-content").removeClass("document-view");
        break;
      default:
        throw new Error("Invalid display mode " + nextDisplayMode);
    }
    localStorage.setItem(Config.LOCAL_STORAGE.DISPLAY_MODE, this.displayMode);
  }

  static _showPopupOnSelect(e) {
    const contextMenu = $("#context-menu");
    const contentLabel = $("#text-content");
    let sel = window.getSelection();
    let node = sel.focusNode;
    let tag;
    while (node && node !== contentLabel) {
      if (node.dataset) {
        tag = node.dataset.tag;
        break;
      }
      node = node.parentNode;
    }
    $(".enabled-when-not-inside-tag").toggleClass("ui-state-disabled", Boolean(tag));
    $(".enabled-when-inside-tag").toggleClass("ui-state-disabled", !Boolean(tag));
    $(".enabled-if-selection").toggleClass("ui-state-disabled", !Boolean(window.getSelection()));
    if (!sel.toString().trim()) {
      contextMenu.hide();
      return;
    }

    // from https://stackoverflow.com/questions/18666601/use-bootstrap-3-dropdown-menu-as-context-menu
    function getMenuPosition(mouse, direction, scrollDir) {
      let win = $(window)[direction]();
      let scroll = $(window)[scrollDir]();
      let menu = $("#context-menu");
      let widthOrHeight = menu[direction]();
      let position = mouse + scroll;
      let children = menu.children();
      let menuOnBottom = false;
      if (mouse + widthOrHeight > win && widthOrHeight < mouse) {
        position -= widthOrHeight;
        if (direction === "height") {
          menuOnBottom = true;
          if (!GUI.__menuIsReversed) {
            menu.append(children.get().reverse());
            GUI.__menuIsReversed = true;
          }
        }
      }
      if (GUI.__menuIsReversed === true && !menuOnBottom) {
        menu.append(children.get().reverse());
        GUI.__menuIsReversed = false;
      }
      return position;
    }

    contextMenu
      .show()
      .css({
        position: "absolute",
        left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
        top: getMenuPosition(e.clientY, 'height', 'scrollTop')
      });
  }

  static _onPdfIframeLoaded() {
    setTimeout(() => {
      GUI.__pdfJsApplication = window.frames[0].PDFViewerApplication;
      GUI.__pdfJsApplication.eventBus.on('pagechanging', GUI._onPdfPageChanging);
    }, 500)
  }

  static _onPdfPageChanging(e) {
    if (e.pageNumber) {
      GUI.goToPage(e.pageNumber)
    }
  }

  static goToPdfPage(page) {
    if (this.__pdfJsApplication) {
      if (page < 0 || page > this.__pdfJsApplication.pagesCount) {
        console.error("PDF page out of bounds: " + page);
        return;
      }
      this.__pdfJsApplication.page = page;
    }
  }

  static goToPage(page) {
    this.__currentPage = page;
    $("#label-page-number").html(page);
    this.goToPdfPage(page);
    let tc = $("#text-content");
    //let tcTop = tc.scrollTop();
    let pageMarker = tc.find(`div[data-page="${page}"]`);
    if (pageMarker && pageMarker.length) {
      pageMarker[0].scrollIntoView({block: "start"});
    }
  }

  static goToPrevPage() {
    if (this.__currentPage > 1) {
      this.goToPage(--this.__currentPage);
    }
  }

  static goToNextPage() {
    if (this.__currentPage < this.__numPages) {
      this.goToPage(++this.__currentPage);
    }
  }

  static replaceSelection(replacementText) {
    this.saveState();
    let sel = window.getSelection();
    if (sel.rangeCount) {
      let range = sel.getRangeAt(0);
      range.deleteContents();
      if (!replacementText) return;
      let textNodes = replacementText.split("\n");
      for (let i = textNodes.length - 1, br = false; i >= 0; i--) {
        if (br) {
          range.insertNode(document.createElement("br"));
        }
        range.insertNode(document.createTextNode(textNodes[i]));
        br = true;
      }
    }
  }

  static saveState() {
    this.versions.push($("#text-content").html());
    $("#btn-undo").removeClass("ui-state-disabled")
  }

  static switchSurnameGivenNames() {
    if (this.displayMode !== GUI.DISPLAY_MODES.REFERENCES) {
      return;
    }
    this.saveState();
    $("#text-content").html($("#text-content").html()
      .replace(/data-tag="surname"/g, 'data-tag2="given-names"')
      .replace(/data-tag="given-names"/g, 'data-tag="surname"')
      .replace(/data-tag2/g, 'data-tag')
    );
  }
}


class Annotation {
  static type;
  static engine;
  static fileExtension;
  static TYPE = {
    FINDER: "finder",
    PARSER: "parser"
  }

  constructor(content, fileName) {
    this.content = content.replace(/\r/g, "");
    this.tags = []
    this.fileName = fileName
  }

  getFileName() {
    return this.fileName;
  }

  getFileExtension() {
    return this.constructor.fileExtension;
  }

  toHtml() {
    throw new Error("Implemented by subclass")
  }


  /**
   * Returns the marked-up text. This is an internal representation, to
   * be able to check the marked up text. To get the correct format
   * suitable to be saved in a file and used by the parser engine, use #export()
   * @returns {string}
   */
  toMarkup() {
    return this.content
  }

  /**
   * Exports the content for saving in a file in the correct format used
   * by the parser engine
   * @returns {string}
   */
  export() {
    return this.toMarkup()
  }

  /**
   * Translates the html code from the editor to the internal markup
   * @param {string} html
   * @return {string}
   */
  loadFromHtml(html) {
    let markedUpText = html
      .replace(Config.REGEX.DIV, "")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")
    // check if translation removed all <span> tags and warn if not
    if (markedUpText.match(Config.REGEX.SPAN)) {
      console.warn("Removing unhandled <span> tags in html text!");
      markedUpText = markedUpText.replace(Config.REGEX.SPAN, "");
    }
    this.content = Annotation._cleanup(markedUpText)
    return this.content
  }

  /**
   * Final cleanup of text
   * @param {string} text
   * @returns {string}
   * @private
   */
  static _cleanup(text) {
    return text
      .replace(/&amp;/g, "&")
      .replace(/&gt;/g, ">")
      .replace(/&lt;/g, "<")
      .replace(/&quot;/g, '"')
      .replace(/&pos;/g, "'")
      .replace(/&nbsp;/g, " ")
      .trim();
  }

  /**
   * Given a text with xml-style markup, return HTML that displays this markup visually
   * also populates `this.tags`
   * @param {string} text
   * @returns {string}
   */
  _markupToHtml(text) {
    let html;
    // translate tag names to data-tag attributes
    let tag_names = [];
    let tag_name;
    for (let match of text.matchAll(/<([^>\/ ]+)>/g)) {
      tag_name = match[1];
      if (!tag_names.includes(tag_name)) {
        tag_names.push(tag_name);
      }
    }
    this.tags = tag_names;
    for (tag_name of tag_names) {
      let regex = new RegExp(`<${tag_name}>(.*?)</${tag_name}>`, 'g');
      let replacement = `<span data-tag="${tag_name}">$1</span>`;
      text = text.replace(regex, replacement);
    }
    // convert line breaks to break nodes
    html = text.replace(/\n/g, "<br>");
    return html
  }

  _htmlToMarkup(html) {
    return html
      .replace(Config.REGEX.DIV, "")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")
  }
}

class ExparserExtractionAnnotation extends Annotation {
  static type = Annotation.TYPE.FINDER;
  static engine = Config.ENGINES.EXPARSER;
  static fileExtension = "csv";

  constructor(content, fileName) {
    while (content.match(/\n\n/)) {
      content = content.replace(/\n\n/g, "\n");
    }
    super(content, fileName);
    this.textContent = [];
    this.layoutInfo = [];
    this.numPages = 0;
    let lines = this.content
      .split('\n')
      .map(line => line.trim());
    let yval = 0;
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i]
      // we have layout info in the file, remove from text to re-add later
      let line_parts = line.split('\t');
      if (line_parts.length >= 7) {
        let layout_info = line_parts.slice(-6);
        let text_content = line_parts.slice(0, -6).join(' ');
        this.layoutInfo[i] = layout_info.join('\t');
        this.textContent[i] = text_content;
        let lineYval = layout_info[1];
        if (yval === 0 || yval - lineYval > 300) {
          this.numPages++;
          line = `<div class="page-marker" data-page="${this.numPages}"></div>` + this.textContent[i];
        }
        yval = lineYval;
      }
      this.textContent[i] = line;
    }
    this.content = this.textContent.join("\n")
  }

  toHtml() {
    return this._markupToHtml(content);
  }

  /**
   * @inheritDoc
   */
  loadFromHtml(html) {
    let markedUpText = super.loadFromHtml(html)
    // remove empty lines and nodes
    while (markedUpText.match(/\n\n/)) {
      markedUpText = markedUpText.replace(/\n\n/g, "\n")
    }
    markedUpText = markedUpText.replace(Config.REGEX.EMPTY_NODE, "")
    this.content = Annotation._cleanup(markedUpText)
    return this.content
  }

  toMarkup() {
    return super.toMarkup();
  }

  export() {
    let markedUpText = this.content;
    if (this.content.split("\n").length !== this.layoutInfo.length) {
      alert("Number of lines in document has changed, cannot export with layout info");
      return this.toMarkup()
    }
    let t1 = markedUpText.split('\n')
    let t2 = [];
    let rowFirstColumn;
    let allFirstColumns = "";
    for (let i = 0; i < t1.length; i++) {
      rowFirstColumn = t1[i];
      allFirstColumns = allFirstColumns + rowFirstColumn;
      if (i === t1.length - 1) {
        // no \n for last line
        if (typeof this.layoutInfo[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + this.layoutInfo[i];
        } else {
          t2[i] = t1[i] + '\n'
        }
      } else {
        if (typeof this.layoutInfo[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + this.layoutInfo[i] + '\n';
        } else {
          t2[i] = t1[i] + '\n'
        }
      }
      markedUpText = t2.join("");
    }
    return markedUpText
  }
}

class ExparserSegmentationAnnotation extends ExparserExtractionAnnotation {
  static type = Annotation.TYPE.PARSER;
  static fileExtension = "xml";

  constructor(content, fileName) {
    while (content.match(/\n\n/)) {
      content = content.replace(/\n\n/g, "\n");
    }
    super(content, fileName);
    this.numRefs = 0
  }

  toHtml() {
    let text = this.content;
    if (text.startsWith("<?xml")) {
      let textLines = text.split("\n");
      // remove root node
      textLines.splice(0, 2);
      textLines.splice(-1, 1);
      // remove enclosing <ref> and <author> tags
      textLines = textLines
        .map(line => line
          .replace(/<\/?author>/g, '')
          .replace(/<\/?ref>/g, ''));
      text = textLines.join("\n");
    }
    this.numRefs = text.split("\n").length
    return this._markupToHtml(text);
  }

  export() {
    let textToExport = this.addAuthorTag(this.content)
      .split("\n")
      .map(line => `<ref>${line}</ref`)
      .join("\n");
    return `<?xml version="1.0" encoding="utf-8"?>\n<seganno>\n${textToExport}\n</seganno>`
  }

  addAuthorTag(markedUpText) {
    let startTag = "<author>";
    let endTag = "</author>";
    let firstStartTagMatch = null;
    let secondStartTagMatch = null;
    let lastEndTagMatch = null;
    let offset = 0;
    let matches = markedUpText.matchAll(/<\/?([^>]+)>/g);
    let pos;
    for (let match of matches) {
      let [tag, tagName] = match;
      if (["surname", "given-names"].includes(tagName)) {
        if (!tag.startsWith("</")) {
          // opening tag
          if (firstStartTagMatch === null) {
            // insert <author> before opening first surname or given-names
            firstStartTagMatch = match;
            pos = match.index + offset;
            markedUpText = markedUpText.substr(0, pos) + startTag + markedUpText.substr(pos);
            offset += startTag.length;
            //console.log({info: "inserting <author> before first tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
            continue;
          }
          if (secondStartTagMatch === null) {
            if (tag !== firstStartTagMatch[0]) {
              // if the second opening tag is not the same as the first, remember it and go on
              secondStartTagMatch = match;
              //console.log({info: "second opening tag not the same as the first", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
              continue;
            }
            // tag repeats
            //console.log("tag repeats")
          }
        } else {
          // closing tag
          lastEndTagMatch = match;
          if (!secondStartTagMatch || tagName !== secondStartTagMatch[1]) {
            //console.log({info: "Closing tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch});
            continue;
          }
        }
        if (lastEndTagMatch) {
          // insert </author> after the last closing tag
          pos = lastEndTagMatch.index + offset + lastEndTagMatch[0].length;
          markedUpText = markedUpText.substr(0, pos) + endTag + markedUpText.substr(pos);
          offset += endTag.length;
        }
        if (!tag.startsWith("</")) {
          // insert new opening tag
          //console.log({info:"Insert new opening tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
          pos = match.index + offset;
          markedUpText = markedUpText.substr(0, pos) + startTag + markedUpText.substr(pos);
          offset += startTag.length;
        }
        // reset matches
        firstStartTagMatch = null;
        secondStartTagMatch = null;
        lastEndTagMatch = null;
      }
    }
    if (lastEndTagMatch) {
      // insert missing closing tag
      pos = lastEndTagMatch.index + offset + lastEndTagMatch[0].length;
      markedUpText = markedUpText.substr(0, pos) + endTag + markedUpText.substr(pos);
    }
    return markedUpText;
  }

}

class AnystyleFinderAnnotation extends Annotation {
  static type = Annotation.TYPE.FINDER;
  static engine = Config.ENGINES.ANYSTYLE;
  static fileExtension = "ttx";

  constructor(text, fileName) {
    super(text, fileName);
    this.numPages = 0
  }

  /**
   * @returns {string}
   */
  toHtml() {
    // text is in "ttx" format,
    // 1) convert it to xml-style tags
    let lines = this.content.split('\n');
    let ttx_curr_tag;
    let ttx_last_tag_before_blank;
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i]
      let pipe_idx = line.indexOf("|");
      let tag;
      if (pipe_idx < 0) {
        pipe_idx = 14
        line = " ".repeat(pipe_idx) + "| " + line
      }
      tag = line.slice(0, pipe_idx).trim()
      line = line.slice(pipe_idx + 1).trim()
      let text = line
      if (line === "") {
        tag = "blank"
      }
      switch (tag) {
        case "blank":
          if (ttx_curr_tag) {
            lines[i - 1] += `</${ttx_curr_tag}>`
          }
          lines[i] = ""
          ttx_last_tag_before_blank = ttx_curr_tag
          continue
        case "":
          tag = ttx_curr_tag || ttx_last_tag_before_blank || "text"
          break
        case "ref":
          tag = "reference"
          break
      }
      ttx_last_tag_before_blank = tag
      if (tag !== ttx_curr_tag) {
        line = ""
        if (ttx_curr_tag) {
          lines[i - 1] += `</${ttx_curr_tag}>`
        }
        if (tag === "pages") {
          this.numPages++;
          line += `<div class="page-marker" data-page="${this.numPages}"></div>`;
        }
        line += `<${tag}>${text}`
        ttx_curr_tag = tag
      }
      if (i === lines.length - 1) {
        if (ttx_curr_tag) {
          line += `</${ttx_curr_tag}>`
        }
      }
      lines[i] = line
    }
    let text = lines.join("\n")
    // 2) now transform xml markup to HTML
    let html = super._markupToHtml(text);
    console.log(html.slice(0,500))
    return html
  }

  loadFromHtml(html) {
    let markedUpText = html
      .replace(Config.REGEX.DIV, "")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")
    let currentTag;
    let xmlLines = markedUpText.split("\n")
    let ttxLines = [];
    let lastTagBeforeBlank;
    for (let xmlLine of xmlLines) {
      // replace tags with prefix
      let ttxLine = xmlLine.replace(
        /^(.*)<([^/>]+)>(.*)$/,
        (m, prefix, tag, suffix) => {
          if (tag === "reference") {
            tag = "ref"
          }
          if (tag === "blank") {
            lastTagBeforeBlank = currentTag
          }
          if (currentTag && tag === currentTag) {
            tag = ""
          } else {
            tag = tag || lastTagBeforeBlank || "text"
            currentTag = tag
            lastTagBeforeBlank = null
          }
          return tag.padEnd(14, " ") + "| " + prefix + suffix
        }
      );
      // no tag found
      if (ttxLine === xmlLine) {
        ttxLine = " ".repeat(14) + "| " + xmlLine
      }
      ttxLine = ttxLine.replace(/<\/?[^>]+>/g, "");
      ttxLines.push(ttxLine)
    }
    markedUpText = ttxLines.join("\n")
    this.content = Annotation._cleanup(markedUpText)
    return markedUpText
  }

  export() {
    return super.export();
  }


}

class AnystyleParserAnnotation extends AnystyleFinderAnnotation {
  static type = Annotation.TYPE.PARSER;
  static fileExtension = "xml";

  constructor(content, fileName) {
    let lines = content.split("\n");
    //remove xml declaration and root node
    lines.splice(0, 2);
    lines.splice(-1, 1);
    content = lines.join(" ");
    // remove enclosing <sequence>tags
    content = content
      .replace(/<sequence>/g, "")
      .replace(/<\/sequence>/g, "\n")
    super(content, fileName);
    this.numRefs = content.split("\n").length
  }

  export() {
    let textToExport = this.content
      .split("\n")
      .map(line => `  <sequence>\n    ${line.replace(/></, ">\n    <")}\n  </sequence`)
      .join("\n");
    return `<?xml version="1.0" encoding="utf-8"?>\n<dataset>\n${textToExport}\n</dataset>`
  }
}

// start
GUI.init();
