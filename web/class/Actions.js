class Actions {

  static init() {
    GUI.init()
    $(() => {
      let hash = (new URL(document.URL)).hash;
      let lastLoadUrl = localStorage.getItem(Config.LOCAL_STORAGE.LAST_LOAD_URL) || false;
      const params = Object.fromEntries(new URLSearchParams(hash.slice(1)))
      let downloadUrl = params.load
      let downloadType = params.type
      let textInLocalStorage = Actions._hasTextInLocalStorage();
      let textLoaded = false
      if (textInLocalStorage /*&& !(downloadUrl !== lastLoadUrl)*/) {
        console.log("Loading document from local storage.");
        Actions._loadTextFromLocalStorage();
        textLoaded = true
      }
      if (lastLoadUrl && (!downloadUrl || downloadUrl === lastLoadUrl)) {
        console.log("Loading document from stored URL: " + lastLoadUrl)
        Actions.loadFromUrl(lastLoadUrl)
      } else if (downloadUrl) {
        console.log("Loading document from URL hash: " + downloadUrl)
        Actions.loadFromUrl(downloadUrl)
        document.location.hash = ""
      } else {
        Actions.switchToFinder()
      }
      if (!textLoaded) {
        $("#modal-help").show();
      }
    })

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
    const channel_id = State.channel_id = Math.random().toString().slice(2)
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
          // const onCloseClick = type === "info" ? () => {
          //   if (confirm("Cancel the current server process?")) {
          //     Actions.runCgiScript("abort.py", {id: channel_id})
          //   }
          // } : undefined;
          toast = toastr[type](text, title, {
            positionClass: "toast-bottom-full-width",
            timeOut: 0,
            extendedTimeOut: 0,
            closeButton: true,
            onCloseClick: undefined
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

  static _hasTextInLocalStorage() {
    return Boolean(localStorage.getItem(Config.LOCAL_STORAGE.DOCUMENT));
  }

  static async _loadTextFromLocalStorage() {
    let filename = localStorage.getItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME);
    let content = localStorage.getItem(Config.LOCAL_STORAGE.DOCUMENT);
    if (filename && content) {
      let type = filename.endsWith(".xml") ? "text/xml" : "text/plain"
      let file = new File([content], filename, {
        lastModified: 1534584790000,
        type: `${type};charset=utf8`
      });
      try {
        await Actions.loadFile(file)
      } catch (e) {
        alert(e.message)
      }
      return true;
    }
  }

  static async load() {
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
    GUI.showSpinner()
    try {
      for (let file of uploadBtn.files) {
        await this.loadFile(file);
      }
    } catch (e) {
      alert(e.message)
    } finally {
      GUI.hideSpinner()
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
    GUI.showSpinner()
    try {
      await this.loadFile(file);
      GUI.hideSpinner()
    } catch (e) {
      alert(e.message)
      GUI.hideSpinner()
    }
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

  static async loadFile(file) {
    return new Promise((resolve, reject) => {
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
        return reject(new Error("Cannot determine file type for " + fileName));
      }
      console.log(`Loading ${fileName} of type ${fileType}`)
      let annotation;
      switch (fileType) {
        case "pdf":
        case "application/pdf":
          return resolve(GUI.loadPdfFile(file));
        case "xml":
        case "application/xml":
        case "txt":
        case "text/plain":
        case "csv":
        case "text/csv":
        case "ttx":
          break;
        default:
          reject(new Error("Invalid file extension: " + fileExt));
          return;
      }
      // load file and determine type of Annotation
      const fileReader = new FileReader();
      fileReader.onload = e => {
        console.log("File received.")
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
              reject(new Error("Unknown XML format"))
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
            return reject(new Error("Unknown file type: " + fileType));
        }
        GUI.loadAnnotation(annotation);
        resolve(annotation)
      }
      fileReader.readAsText(file, "UTF-8");
    })
  }

  static async extractTextFromPdf() {
    const msg = `Do you want to extract text from the PDF?`
    if (!confirm(msg)) return
    const pdfFile = GUI.pdfFile
    const url = Config.URL.UPLOAD
    await Utils.upload(pdfFile, url)
    GUI.showSpinner("Extracting reference lines...")
    const content = await Actions.runCgiScript("extract.rb", {filename: pdfFile.name})
    GUI.hideSpinner()
    const filename = pdfFile.name.replace(".pdf", ".ttx")
    const annoFile = new File([content], filename, {
      lastModified: 1534584790000,
      type: "text/plain; encoding=utf-8"
    });
    try {
      await Actions.loadFile(annoFile)
    } catch (e) {
      alert(e.message)
    } finally {
      GUI.hideSpinner()
    }
  }

  static async findRefsInText() {
    const annotation = GUI.getAnnotation()
    if (annotation.getType() !== Annotation.TYPE.FINDER) {
      alert("works only in finder mode")
      return
    }
    const msg = `Do you want to identify the references in the current text? This will discard any manual changes.`
    if (!confirm(msg)) return
    let content = annotation.getContent()
        .split("\n")
        .map(line => line.replace(/^[^|]+\| ?/g, ""))
        .join("\n")
    let filename = annotation.getFileName()
    GUI.showSpinner("Indentifying references, please wait...")
    try {
      const annoFile1 = new File([content], filename, {
        lastModified: 1534584790000,
        type: "text/plain; encoding=utf-8"
      });
      await Utils.upload(annoFile1, Config.URL.UPLOAD)
      content = await Actions.runCgiScript("find.rb", {filename, model: State.model.name})
      filename = filename.replace(/(\.pdf)/,"").replace(/\.txt/,".ttx")
      const annoFile2 = new File([content], filename, {
        lastModified: 1534584790000,
        type: "text/plain; encoding=utf-8"
      });
      await Actions.loadFile(annoFile2)
    } catch (e) {
      alert(e.message)
    } finally {
      GUI.hideSpinner()
    }
  }

  static async findRefsInPdf() {
    const msg = `Do you want to extract text from the PDF and identify the references?`
    if (!confirm(msg)) return
    GUI.removeTextFile(false)
    const pdfFile = GUI.pdfFile
    GUI.showSpinner("Indentifying references, please wait...")
    try {
      await Utils.upload(pdfFile, Config.URL.UPLOAD)
      const content = await Actions.runCgiScript("find.rb", {filename: pdfFile.name, model: State.model.name})
      const filename = pdfFile.name.replace(".pdf", ".ttx")
      const annoFile = new File([content], filename, {
        lastModified: 1534584790000,
        type: "text/plain; encoding=utf-8"
      });
      await Actions.loadFile(annoFile)
    } catch (e) {
      alert(e.message)
    } finally {
      GUI.hideSpinner()
    }
  }

  static async parseReferences() {
    const annotation = GUI.getAnnotation()
    if (annotation.getType() !== Annotation.TYPE.PARSER) {
      alert("Can only parse references, not documents")
      return
    }
    const msg = `Do you want to automatically tag the references?`
    if (!confirm(msg)) return
    const refs = annotation.getContent()
      .replace(Config.REGEX.TAG_OPEN, "")
      .replace(Config.REGEX.TAG_CLOSE, " ")
      .replace(/&amp;/g, "&")
      .trim()
    const params = {
      refs,
      model: State.model.name
    }
    GUI.saveState()
    GUI.showSpinner("Parsing references")
    const content = await Actions.runCgiScript("parse.rb", params, "post")
    GUI.hideSpinner()
    annotation.load(content)
    GUI.update()
  }

  static async autoTagReferences() {
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
  }

  static async separateReferencesInFootnotes() {
    const annotation = GUI.getAnnotation()
    let content = annotation.getContent()
  }

  static async trainModel(target = "both") {
    await Actions.runCgiScript("train.rb", {
      model: State.model.name,
      target,
      channel_id: State.channel_id
    })
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
      // very naive and basic error handling
      if (result && typeof result === "object" && result.error) {
        alert(result.error)
      }
      return result
    } catch (e) {
      console.error(e)
      alert(e.message)
      return {
        error: e.message
      }
    }
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
    const type = annotation.getMimeType() + ';charset=utf-8;'
    Utils.download(annotation.export(), annotation.getFileName(), type);
  }

  static async exportToZotero() {
    let annotation = GUI.getAnnotation()
    if (!annotation || annotation.getType() !== Annotation.TYPE.PARSER) {
      alert("You must be in segmentation mode to export references");
      return;
    }
    let dataset_xml = annotation.export();
    if (!dataset_xml.match(Config.REGEX.TAG)) {
      alert("No references to export");
      return;
    }
    let csl_data = await Actions.runCgiScript("parse-csl.rb", {
      model: State.model.name,
      seq: dataset_xml
    }, "post")
    GUI.hideSpinner()
    // check results
    let unknown_types = csl_data.filter(item => !item.type)
    if (unknown_types.length > 0) {
      let question = `Extracted reference data contains ${unknown_types.length} unrecognized item types. 
      Do you want to skip them during import (OK) or correct the markup (cancel)?`.replace(/\n */g, " ")
      if (!confirm(question)) {
        return;
      }
    }
    csl_data = csl_data.filter(item => item.type)
    let item_name = annotation.getFileName().split(".").slice(0, -1).join(".");
    if (item_name.match(/10\.[0-9]+_/)) {
      // work around DOIs in filenames where the illegal "/" has been replaced by underscore
      item_name = item_name.replace("_", "/"); // only replaces first occurrence
    }
    // query for identifying target item
    let query = {}
    let identfier_name;
    for (let identifier of Config.KNOWN_IDENTIFIERS) {
      let matched = item_name.match(identifier.match)
      if (matched) {
        identfier_name = identifier.name;
        for (let [field, value] of Object.entries(matched.groups)) {
          query[field] = [field === "date" ? "is" : "contains", value]
        }
        break;
      }
    }
    let msg;
    // abort requests on escape key  press
    const abortFunc = e => e.key === "Escape" && Zotero.controller.abort();
    $(document).on('keydown', abortFunc);
    try {
      GUI.showSpinner("Connecting to Zotero...");
      // selection
      let zSelection = await Zotero.getSelection();
      let libraryID = zSelection.libraryID;
      if (!libraryID) {
        throw new Error("Please select an item in Zotero to determine the library used.");
      }
      let targetItem = zSelection.selectedItems.length ? zSelection.selectedItems[0] : null;
      // query based on file name
      if (Object.keys(query).length) {
        GUI.showSpinner(`Searching Zotero for ${item_name}`);
        console.log(query)
        let items;
        if (identfier_name === "key") {
          items = await Zotero.items(libraryID, [item_name])
        } else {
          items = await Zotero.search(libraryID, query);
        }
        if (items.length === 0) {
          throw new Error(`'${item_name}' cannot be found in the library.`);
        } else if (items.length > 1) {
          throw new Error(`'${item_name}' exists twice - please merge items manually first.`);
        }
        targetItem = items[0];
      } else if (!targetItem) {
        throw new Error("No identifier or selected item can be determined.");
      }
      if (targetItem.parentItem) {
        targetItem = (await Zotero.items(libraryID, [targetItem.parentItem]))[0]
      }
      GUI.showSpinner(`Retrieving citations...`);
      const citations = await Zotero.listCitations(libraryID, targetItem.key);
      msg = `Do you want to export ${csl_data.length} references to "${targetItem.title}"?`;
      if (!confirm(msg)) return;
      let total = csl_data.length;
      // loop through all the cited references
      for (let [count, cslItem] of csl_data.entries()) {
        let msg = `item ${count + 1} of ${total} cited references. Press the Escape key to abort.`;
        GUI.showSpinner("Identifying " + msg);
        console.log(cslItem)
        const item = Zotero.itemFromCSLJSON(cslItem)
        console.log(item)
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
              GUI.showSpinner("Updating " + msg);
              console.log(item);
              await Zotero.updateItems(libraryID, [newItem]);
            }
            itemKey = foundItem.key;
          }
        }
        // create new item
        if (!itemKey) {
          GUI.showSpinner("Creating " + msg);
          ([itemKey] = await Zotero.createItems(libraryID, [item]));
        }
        if (citations.find(citation => citation.zotero === itemKey)) {
          console.log("Citation already linked.");
          continue;
        }
        GUI.showSpinner("Linking " + msg);
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
    let annotation = GUI.getAnnotation();
    if (!annotation) {
      // create empty annotation for manual entry
      annotation = new AnystyleFinderAnnotation("")
    } else if (annotation.getType() === Annotation.TYPE.FINDER) {
      // already in finder editor
      return
    } else if (this.__finderAnnotation) {
      if (GUI.versions.length) {
        const msg = "This will discard all your changes. Proceed?"
        if (!confirm(msg)) {
          return
        }
      }
      annotation = this.__finderAnnotation
    } else {
      return
    }
    GUI.loadAnnotation(annotation)
  }


  static switchToParser() {
    let annotation = GUI.getAnnotation();
    if (!annotation) {
      // create empty annotation for manual entry
      annotation = new AnystyleParserAnnotation("")
    } else if (annotation.getType() === Annotation.TYPE.PARSER) {
      // already in parser editor
      return
    } else {
      // save the state of the finder annotation and convert it to parser annotation
      this.__finderAnnotation = annotation
      annotation = annotation.toParserAnnotation()
    }
    GUI.loadAnnotation(annotation)
  }

  static setModel(name) {
    $("#btn-model-" + State.model.name).removeClass("btn-dropdown-radio-selected");
    State.model.name = name;
    $("#btn-model-" + State.model.name).addClass("btn-dropdown-radio-selected");
    localStorage.setItem(Config.LOCAL_STORAGE.LAST_MODEL_NAME, name);
    $(".model-training").toggleClass("ui-state-disabled", name === "default")
    $("#btn-save").toggleClass("ui-state-disabled", name === "default")
  }

  static async exportCsl() {
    const annotation = GUI.getAnnotation()
    if (annotation.getType() !== Annotation.TYPE.PARSER) {
      alert("Can only parse references, not documents")
      return
    }
    GUI.showSpinner("Retrieving citation data")
    const csl = await Actions.runCgiScript("parse-csl.rb", {
      model: State.model.name,
      seq: annotation.export()
    }, "post")
    GUI.hideSpinner()
    let filename = annotation.getFileName().split(".").slice(0, -1).join(".") + ".csl.json";
    Utils.download(JSON.stringify(csl, null, 2), filename, "text/plain;encoding=utf-8")
  }

  static preprocessFootnotes() {
    let annotation = GUI.getAnnotation()
    if (!annotation) return
    GUI.saveState()
    let refs = annotation.getContent().split("\n")
    let fnCounter = 0
    const separator = "<sep></sep>"
    const handleFootnotes = line => {
      // footnote numbers
      let m = line.match(Config.REGEX.FOOTNOTE_NUMBER_AT_LINE_START)
      if (m) {
        let fnNumber = Number(m[1].trim())
        let fnLine = m[2].trim()
        // heuristic to avoid false positives: number shouldn't jump by more than 30
        if (fnNumber > fnCounter && (fnNumber - fnCounter) <= 30 && fnLine.length > 70) {
          fnCounter = fnNumber
          line = separator + line
        }
      }
      return line
    }
    refs = refs
      .map(line => line.trim() ? line : separator)
      .map(handleFootnotes)
      .join(" ")
      .replace(new RegExp(separator, "g"), "\n")
    // don't leave citation number on own line
    refs = refs.replace(/(\n[\d]{1,3}\s+)\n/gm, "$1")
    // remove empty lines
    while (refs.match(/\n *\n/)) {
      refs = refs.replace(/\n *\n/, "\n")
    }
    annotation.setContent(refs)
    GUI.update()
  }

  static removeIgnoreTags() {
    GUI.saveState()
    let content = GUI.getAnnotation().getContent()
    content = content.replace(/<ignore>[^<]*<\/ignore>/g, "")
    content = content.replace(/<text>[^<]*<\/text>/g, "")
    // remove empty lines
    while (content.match(/\n *\n/)) {
      content = content.replace(/\n *\n/, "\n")
    }
    GUI.getAnnotation().setContent(content)
    GUI.update()
  }

  static ignore2text() {
    GUI.saveState()
    let content = GUI.getAnnotation().getContent()
    content = content.replace(/<ignore>([^<]+)<\/ignore>/gm, "<text>$1</text>")
    content = content.replace(/<\/text>([^<]+)\n/gm, "</text><ref>$1</ref>\n")
    content = content.replace(/\n([^<]+)<text>/gm, "\n<ref>$1</ref><text>")
    //content = content.replace(/\n([^<]+)\n/gm, "\n<ref>$1</ref>\n\n")
    // remove empty lines
    while (content.match(/\n *\n/)) {
      content = content.replace(/\n *\n/, "\n")
    }
    GUI.getAnnotation().setContent(content)
    GUI.update()
  }
}

