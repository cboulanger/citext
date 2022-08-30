class Actions {

  static COMMANDS = {
    TEXT_EXTRACTION: "extract",
    FIND_REFERENCES: "find",
    PARSE_REFERENCES: "parse",
    AUTO_TAG: "auto-tag",
    TRAIN_MODEL: "train",
    EXPORT_REFERENCES: "export-refs"
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
      res = await fetch(`${Config.URL.LOAD_FROM_URL}?url=${url}`)
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
      State.zotero.attachmentPath = s.slice(s.indexOf("storage") + 1).join("/");
      await this.loadFromUrl("file://zotero-storage/" + State.zotero.attachmentPath, filename)
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
        GUI.loadPdfFile(file);
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

  static async runCommand(command) {
    switch (command) {

      case Actions.COMMANDS.TEXT_EXTRACTION: {
        const msg = `Do you want to extract text from the PDF?`
        if (!confirm(msg)) return
        const pdfFile = GUI.pdfFile
        const url = Config.URL.UPLOAD
        await Utils.upload(pdfFile, url)
        const content = await Actions.runCgiScript("extract.rb", {filename: pdfFile.name})
        const filename = pdfFile.name.replace(".pdf", ".ttx")
        const annoFile = new File([content], filename, {
          lastModified: 1534584790000,
          type: "text/plain; encoding=utf-8"
        });
        Actions.loadFile(annoFile)
        break
      }


      case Actions.COMMANDS.FIND_REFERENCES: {
        const msg = `Do you want to extract text from the PDF and identify the references?`
        if (!confirm(msg)) return
        const pdfFile = GUI.pdfFile
        const url = Config.URL.UPLOAD
        GUI.showSpinner()
        await Utils.upload(pdfFile, url)
        const content = await Actions.runCgiScript("find.rb", {filename: pdfFile.name, model: State.model.name})
        GUI.hideSpinner()
        const filename = pdfFile.name.replace(".pdf", ".ttx")
        const annoFile = new File([content], filename, {
          lastModified: 1534584790000,
          type: "text/plain; encoding=utf-8"
        });
        Actions.loadFile(annoFile)
        break
      }

      case Actions.COMMANDS.PARSE_REFERENCES: {
        const annotation = GUI.getAnnotation()
        if (annotation.getType() !== Annotation.TYPE.PARSER) {
          alert("Can only parse references, not documents")
          return
        }
        const msg = `Do you want to automatically tag the references?`
        if (!confirm(msg)) return
        const params = {
          refs: annotation.getContent().replace(Config.REGEX.TAG, ""),
          model: State.model.name
        }
        GUI.saveState()
        GUI.showSpinner()
        const content = await Actions.runCgiScript("parse.rb", params, "post")
        GUI.hideSpinner()
        annotation.load(content)
        GUI.setHtmlContent(annotation.toHtml())
        break
      }

      case Actions.COMMANDS.AUTO_TAG: {
        // not working
        // const annotation = GUI.getAnnotation()
        // if (annotation.getType() !== Annotation.TYPE.PARSER) {
        //   alert("Only available for list of references")
        //   return
        // }
        // GUI.saveState()
        // let autoTaggedText = annotation.getContent().split("\n")
        //   // citation numbers
        //   .map(line => line.replace(
        //     /^(<(?!cit)[^/>]+>)([0-9]{1,3}\s+)(\S[^>]+<\/[^>]+>)/,
        //     "<citation-number>$2</citation-number>$1$3"))
        //   // signal words
        //   .map(line => Config.SIGNAL_WORDS.forEach(re => line.replace(re, "<signal>$0</signal>")))
        //   .join("\n")
        // annotation.load(autoTaggedText)
        break
      }

      case Actions.COMMANDS.TRAIN_MODEL: {
        GUI.showSpinner()
        await Actions.runCgiScript("train.rb", {model: State.model.name})
        GUI.hideSpinner()
        break
      }

      case Actions.COMMANDS.EXPORT_REFERENCES: {
        GUI.showSpinner()
        const csl = await Actions.runCgiScript("extract-refs-as-csl.rb", {model: State.model.name})
        const file = new File([csl], )
        GUI.hideSpinner()
        break
      }

    }
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
        .replace(Config.REGEX.TAG, "")
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


  /**
   * @deprecated
   * @param name
   * @param params
   * @returns {Promise<Response>}
   */
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

  /**
   * Runs a cgi script on the server
   * @param name
   * @param params
   * @param method
   * @returns {Promise<any>}
   */
  static async runCgiScript(name, params = {}, method = "get") {
    let response;
    try {
      if (method.toLowerCase() === "post") {
        // POST
        const url = `${Config.SERVER_URL}/${name}`
        response = await fetch(url, {
          method: "post",
          body: new URLSearchParams(params),
          headers: {
            "Accept": "application/javascript"
          }
        })
      } else {
        // GET
        const url = `${Config.SERVER_URL}/${name}?${new URLSearchParams(params)}`
        response = await fetch(url, {
          headers: {
            "Accept": "application/javascript"
          }
        })
      }
      let result = await response.json()
      if (result && typeof result === "object" && result.error) {
        alert(error)
        return
      }
      return result
    } catch (e) {
      console.error(e)
      alert(e.message)
    }
  }

  /**
   * @deprecated
   * @param command
   * @returns {Promise<void>}
   */
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
      url = `${Config.SERVER_URL}/excite.py?command=layout&file=${filenameNoExt}&model_name=${State.model.name}`
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
      url = `${Config.SERVER_URL}/excite.py?command=exparser&file=${filenameNoExt}&model_name=${State.model.name}`
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
      url = `${Config.SERVER_URL}/excite.py?command=segmentation&file=${filenameNoExt}&model_name=${State.model.name}`;
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

  static export() {
    const annotation = GUI.getAnnotation()
    if (!annotation) {
      alert("No annotation loaded")
      return
    }
    Utils.download(annotation.export(), annotation.getFileName());
  }

  static async exportToZotero() {
    let annotation = GUI.getAnnotation()
    if (!annotation || annotation.getType() !== Annotation.TYPE.PARSER) {
      alert("You must be in segmentation mode to export references");
      return;
    }
    let refs = annotation.export();
    if (!refs.match(Config.REGEX.TAG)) {
      alert("No references to export");
      return;
    }
    let id = annotation.getFileName().split(".").slice(0, -1).join(".");
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
    const annotation = GUI.getAnnotation()
    if (!annotation) return;
    const filename = annotation.getFileName();
    const type = annotation.getType()
    const engine = annotation.getEngine()
    const data = GUI.getTextToExport();
    if (!confirm(`Save current annotation to model dataset '${State.model.name}?'`)) return
    GUI.showSpinner(`Saving training data.`);
    let body = JSON.stringify({filename, type, engine, data, modelName: State.model.name}) + "\n\n";
    let response = await fetch(`${Config.SERVER_URL}/save.py`, {
      method: 'post', body
    })
    GUI.hideSpinner();
    let result = await response.json()
    if (result.error) alert(result.error);
  }


  static switchToFinder() {
    const annotation = GUI.getAnnotation();
    if (!annotation || annotation.getType() === Annotation.TYPE.FINDER) {
      return
    }
    if (this.__finderAnnotation) {
      if (GUI.versions.length) {
        const msg = "This will discard the current citation segmentation markup and return to the document. Proceed?"
        if (!confirm(msg)) {
          return
        }
      }
    }
    GUI.loadAnnotation(this.__finderAnnotation)
  }


  static switchToParser() {
    const annotation = GUI.getAnnotation();
    if (!annotation || annotation.getType() === Annotation.TYPE.PARSER) {
      return
    }
    // save the state of the finder annotation
    this.__finderAnnotation = annotation
    GUI.loadAnnotation(annotation.toParserAnnotation())
  }

  static changeModel(name) {
    $("#btn-model-" + State.model.name).removeClass("btn-dropdown-radio-selected");
    State.model.name = name;
    $("#btn-model-" + State.model.name).addClass("btn-dropdown-radio-selected");
    localStorage.setItem(Config.LOCAL_STORAGE.LAST_MODEL_NAME, name);
    $("#btn-train").toggleClass("ui-state-disabled", name === "default")
  }
}

