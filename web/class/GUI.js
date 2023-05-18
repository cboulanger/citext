class GUI {
  static annotation;
  static versions = [];
  static pdfFile;

  static init() {
    // internal vars
    this.__numPages = 0;
    this.__currentPage = 1;
    this.__currentRefNode = null;
    this.__markupViewState = false;
    this.__pdfJsApplication = null;

    $(() => {
      GUI.toggleMarkedUpView(false);
      this.resetVersions()
      this._setupEventListeners();
      GUI.toggleMarkedUpView(false);

      $('[data-toggle="tooltip"]').tooltip()
    });

    this.initSSE()
  }

  static initSSE() {
    // Display SSE messages
    const channel_id = State.channel_id = Math.random().toString().slice(2)
    const source = new EventSource(`${Config.SERVER_URL}/sse.py?${channel_id}`);
    let toasts = {};
    source.addEventListener("open", () => {
      console.log("Initialized SSE connection with id " + channel_id)
    })
    // end sse process when window closes
    $(window).on('beforeunload', () => {
      source.close()
      navigator.sendBeacon(`${Config.SERVER_URL}/sse-terminate.py?${channel_id}`);
    });

    toastr.options.preventDuplicates = true;
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
        console.log({type, title, text})
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
            timeOut: 30000,
            extendedTimeOut: 30000,
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

  static async loadStyleSheetAndHTMLFromCSV(csvFilePath, parentNodeId) {
    try {
      const response = await fetch(csvFilePath);
      const csvContent = await response.text();
      const lines = csvContent.split('\n');
      const styleSheet = document.styleSheets[0];
      const parentNode = document.getElementById(parentNodeId);

      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line === '') continue;

        const [dataTag, backgroundColor, textContent, title] = line.split(',').map(value => value.trim().replace(/"/g, ''));

        const rule = `[data-tag="${dataTag}"] { background-color: ${backgroundColor}; }`;
        styleSheet.insertRule(rule, styleSheet.cssRules.length);

        const liNode = document.createElement('li');
        const aNode = document.createElement('a');
        aNode.setAttribute('data-tag', dataTag);
        aNode.setAttribute('onclick', 'GUI.addTag(\'' + dataTag + '\');');
        aNode.setAttribute('href', '#');
        aNode.textContent = textContent;
        aNode.title = title;
        liNode.appendChild(aNode);
        parentNode.appendChild(liNode);
      }
    } catch (error) {
      console.error('Failed to load the CSV file:', error);
    }
  }


  static _configureStatus(status) {
    $(".visible-if-backend").toggleClass("hidden", false);
    let model_name = localStorage.getItem(Config.LOCAL_STORAGE.LAST_MODEL_NAME) || "default";
    if (status.model_names.length > 0) {
      $("#btn-model").removeClass("hidden");
      status.model_names
        .reverse()
        .forEach(name => $("#model-names").append($(`<li>` +
          `<a class="dropdown-item" href="#" id="btn-model-${name}" onclick="Actions.setModel('${name}')">${name}</a>` +
          `</li>`)));
    }
    $(".visible-if-webdav").toggleClass("hidden", !status.webdav_storage);
    Actions.setModel(model_name);
  }

  static _setupEventListeners() {
    // show popup on select
    const contextMenu = $("#context-menu");
    const textContent = $("#text-content");
    textContent.keypress(function (event) {
      GUI.saveState()
      var keycode = (event.keyCode ? event.keyCode : event.which);
      if (keycode === 13) {
        // when enter is pressed, work around the problem of inserting a <br> within a tag
        let sel = window.getSelection()
        let focusNode = sel.focusNode
        let focusParent = focusNode.parentNode
        let tag = focusParent && focusParent.getAttribute('data-tag')
        if (tag) {
          event.preventDefault()
          let focusText = focusNode.textContent
          let [t1, t2] = [focusText.slice(0, sel.focusOffset), focusText.slice(sel.focusOffset)]
          focusNode.textContent = t1
          let blankNode = document.createElement("span")
          blankNode.setAttribute('data-tag', "blank")
          let newNode = document.createElement("span")
          newNode.setAttribute('data-tag', tag)
          newNode.setAttribute('data-new', "foo")
          let newText = document.createTextNode(t2)
          newNode.append(newText)
          let sibling = focusNode.nextSibling
          let siblings = []
          while (sibling) {
            siblings.push(sibling)
            sibling = sibling.nextSibling
          }
          if (siblings.length) {
            newNode.append(...siblings)
          }
          let nodes = [
            document.createElement("br"),
            blankNode,
            document.createElement("br"),
            newNode
          ].reverse()
          if (focusParent.nextSibling) {
            nodes.map(n => focusParent.parentNode.insertBefore(n, focusParent.nextSibling))
          } else {
            nodes.map(n => focusParent.parentNode.append(n))
          }
          if (focusParent.innerHTML.endsWith("<br>")) {
            focusParent.innerHTML = focusParent.innerHTML.replace(/<br>$/, '')
          }
          let range = new Range();
          range.setStart(newNode, 0);
          range.setEnd(newNode, 0);
          sel.removeAllRanges();
          sel.addRange(range);
        }
        GUI.updateMarkedUpText()
      }
    });
    textContent.on("keyup", GUI.updateMarkedUpText.bind(GUI))
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

    let startTime, endTime, selectedText, orginalTarget;
    $(document).on('pointerdown', e => {
      startTime = new Date().getTime();
      selectedText = window.getSelection().toString();
      orginalTarget = e.target;
    });

    $(document).on('pointerup', e => {
      endTime = new Date().getTime();
      //console.log([selectedText, window.getSelection().toString(), endTime-startTime])
      let longpress = (endTime - startTime >= 500) &&
        selectedText === window.getSelection().toString();
      if (longpress) {
        selectedText = '';
        let sel = window.getSelection();
        if (!sel.focusNode || !sel.focusNode.parentElement) return;
        let p = sel.focusNode.parentElement;
        //console.log(orginalTarget, p)
        //if (orginalTarget !== p) return;
        if (p.dataset && p.dataset.tag) {
          sel.removeAllRanges();
          let range = document.createRange();
          range.selectNodeContents(p);
          sel.addRange(range);
          GUI._showPopupOnSelect(e);
        }
      }
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


  static updateButtons() {
    const annotation = GUI.getAnnotation()
    if (!annotation) return
    const type = annotation.getType()
    const parserEngine = annotation.getEngine()
    // menu entries
    switch (parserEngine) {
      case Config.ENGINES.EXPARSER:
        $(`li > a.exparser`).removeClass("excluded")
        $(`li > a.anystyle`).addClass("excluded")
        break
      case Config.ENGINES.ANYSTYLE:
        $(`li > a.exparser`).addClass("excluded")
        $(`li > a.anystyle`).removeClass("excluded")
        break
    }
    // visibility of context menu buttons
    // refactor this with .toggleClass and boolean conditions
    switch (type) {
      case Annotation.TYPE.FINDER: {
        switch (parserEngine) {
          case Config.ENGINES.EXPARSER:
            $(".exparser.visible-in-document-mode").removeClass("excluded")
            $(".exparser.visible-in-refs-mode").addClass("excluded")
            $(".anystyle.visible-in-refs-mode").addClass("excluded")
            $(".anystyle.visible-in-document-mode").addClass("excluded")
            break
          case Config.ENGINES.ANYSTYLE:
            $(".anystyle.visible-in-document-mode").removeClass("excluded")
            $(".anystyle.visible-in-refs-mode").addClass("excluded")
            $(".exparser.visible-in-refs-mode").addClass("excluded")
            $(".exparser.visible-in-document-mode").addClass("excluded")
            break
        }
        break
      }
      case Annotation.TYPE.PARSER: {
        switch (parserEngine) {
          case Config.ENGINES.EXPARSER:
            $(".exparser.visible-in-refs-mode").removeClass("excluded")
            $(".exparser.visible-in-document-mode").addClass("excluded")
            $(".anystyle.visible-in-refs-mode").addClass("excluded")
            $(".anystyle.visible-in-document-mode").addClass("excluded")
            break
          case Config.ENGINES.ANYSTYLE:
            $(".anystyle.visible-in-refs-mode").removeClass("excluded")
            $(".anystyle.visible-in-document-mode").addClass("excluded")
            $(".exparser.visible-in-refs-mode").addClass("excluded")
            $(".exparser.visible-in-document-mode").addClass("excluded")
            break
        }
        break
      }
    }
    // enable/disable buttons
    switch (type) {
      case Annotation.TYPE.FINDER:
        $(".enabled-if-document").removeClass("ui-state-disabled")
        $(".enabled-if-refs").addClass("ui-state-disabled")
        //$("#btn-segmentation").removeClass("active");
        //$("#btn-identification").addClass("active");
        //$("#btn-identification").removeClass("ui-state-disabled")
        $("#text-content").addClass("document-view");
        $("#text-content").removeClass("references-view");
        break;
      case Annotation.TYPE.PARSER:
        //$(".enabled-if-document").addClass("ui-state-disabled")
        $(".enabled-if-refs").removeClass("ui-state-disabled")
        //$("#btn-segmentation").addClass("active");
        //$("#btn-identification").removeClass("active");
        $("#text-content").addClass("references-view");
        $("#text-content").removeClass("document-view");
        break;
    }
  }

  static resetVersions() {
    GUI.versions = []
    $("#btn-undo").addClass("ui-state-disabled")
  }


  static undo() {
    if (GUI.versions.length) {
      $("#text-content").html(GUI.versions.pop());
      GUI.updateMarkedUpText();
    }
    if (!GUI.versions.length) {
      GUI.resetVersions()
    }
  }

  static showSpinner(text) {
    console.log(text)
    $("#spinner").attr("data-text", text).addClass("is-active");
  }

  static hideSpinner() {
    $("#spinner").removeClass("is-active");
  }

  static loadAnnotation(annotation) {
    if (!(annotation instanceof Annotation)) {
      throw new Error("Argument must be annotation")
    }
    GUI.showSpinner("Loading annotation")
    this.annotation = annotation;
    this.resetVersions()
    this.update()
    GUI.hideSpinner()
  }

  static update() {
    let annotation = this.getAnnotation()
    this.setHtmlContent(annotation.toHtml())
    this.setTextFileName(annotation.getFileName())
    if (annotation.numPages && annotation.numPages > 0) {
      $("#label-page-number").html("1");
      $(".visible-if-pages").removeClass("hidden").removeClass("excluded");
    } else {
      $("#label-page-number").html("");
      $(".visible-if-pages").addClass("hidden");
    }
  }

  static saveToLocalStorage() {
    const annotation = this.getAnnotation()
    if (!annotation) return
    localStorage.setItem(Config.LOCAL_STORAGE.DOCUMENT, annotation.export());
    localStorage.setItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME, GUI.getAnnotation().getFileName());
  }

  static setModelName(model_name) {

  }

  static setTextFileName(filename) {
    $("#text-label").html(filename);
  }

  static setModel(name, oldName) {
    $("#btn-model-" + oldName).removeClass("btn-dropdown-radio-selected");
    $("#btn-model-" + name).addClass("btn-dropdown-radio-selected");
    $("#model-label").html(name);
    $(".model-training").toggleClass("ui-state-disabled", name === "default")
    $("#btn-save").toggleClass("ui-state-disabled", name === "default")
  }

  static removeTextFile(doConfirm = true) {
    if (doConfirm) {
      if (!confirm("Do you really want to clear the document?")) {
        return;
      }
    }
    $("#text-content").html("");
    $("#markup-content").html("");
    $(".view-text-buttons").hide();
    this.setTextFileName("");
    this.annotation = null
    this.versions = [];
    localStorage.removeItem(Config.LOCAL_STORAGE.TEXT_FILE_NAME);
    localStorage.removeItem(Config.LOCAL_STORAGE.DOCUMENT);
    localStorage.removeItem(Config.LOCAL_STORAGE.LAST_LOAD_URL);
    document.location.href = document.URL.replace(/#.*$/, "#");
    this.toggleMarkedUpView(false);
  }

  static async loadPdfFile(file) {
    return new Promise(async (resolve, reject) => {
      GUI.pdfFile = file;
      let objectURL = URL.createObjectURL(file);
      const pdfiframe = $("#pdfiframe");
      pdfiframe.one("load", () => {
        setTimeout(() => {
          GUI.__pdfJsApplication = window.frames[0].PDFViewerApplication;
          GUI.__pdfJsApplication.eventBus.on('pagechanging', GUI._onPdfPageChanging);
        }, 500)
        GUI.showPdfView(true);
        $("#pdf-label").html(file.name);
        $(".enabled-if-pdf,.enabled-if-document").removeClass("ui-state-disabled");
        $(".visible-if-pdf").addClass("hidden");
        resolve()
      });
      pdfiframe.prop("src", "web/viewer.html?file=" + objectURL);
    })
  }

  static removePdfFile() {
    $("pdf-label").html("");
    document.getElementById("pdfiframe").src = 'about:blank';
    State.zotero.attachmentPath = null;
    $(".enabled-if-pdf").addClass("ui-state-disabled");
    $(".visible-if-pdf").addClass("hidden");
    $("#pdf-label").html("");
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
    // select page in PDF if available
    $("#text-content > .page-marker").on("click", e => {
      if (this.__pdfJsApplication) {
        this.goToPdfPage(parseInt((e.target.dataset.page)))
      }
    });
    this.updateButtons();
    this.updateMarkedUpText()
    this.__currentRefNode = null;
    // enable buttons
    $(".view-text-buttons").show();
    $(".enabled-if-text-content").removeClass("ui-state-disabled");
  }


  static updateMarkedUpText() {
    let html = $("#text-content").html();
    let markedUpText = GUI.getAnnotation()
      .loadFromHtml(html)
      .replace(Config.REGEX.EMPTY_NODE, "")
    $("#markup-content").html(markedUpText.replace(/</g, "&lt;"));
    switch (GUI.getAnnotation()?.getType()) {
      case Annotation.TYPE.FINDER: {
        $("#refs-navigation").toggleClass("hidden", !markedUpText.includes("<ref"));
        $(".enabled-if-refs").toggleClass("ui-state-disabled", !(html.match(Config.REGEX.SPAN)));
        break;
      }
      case Annotation.TYPE.PARSER: {
        $(".enabled-if-refs").removeClass("ui-state-disabled");
        $(".enabled-if-segmented").toggleClass("ui-state-disabled", !(html.match(Config.REGEX.SPAN)));
        break;
      }
    }
    GUI.saveToLocalStorage()
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
    GUI.versions.push($("#text-content").html());
    $("#btn-undo").removeClass("ui-state-disabled")
    this.saveToLocalStorage()
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
            .replace(/<span[^>]*><\/span>/g, "")
            .replace(/(<span[^>]*>) *(.+) *(<\/span>)/g, "$1$2$3")
        }
      }
    }
    GUI.updateMarkedUpText();
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
    el.textContent = ` ${el.textContent}`
    $(el).contents().unwrap();
    GUI.updateMarkedUpText();
  }

  static removeTagsInSelection() {
    GUI.saveState()
    let s, r, a, p, c, t
    s = window.getSelection();
    if (!s || !s.rangeCount) {
      return
    }
    s.setBaseAndExtent(s.anchorNode, 0, s.focusNode, s.focusNode.length)
    r = s.getRangeAt(0)
    a = s.anchorNode
    p = a instanceof Text ? a.parentNode : a
    c = document.createTextNode("")
    p.parentNode.insertBefore(c, p)
    t = []
    r.extractContents().childNodes.forEach(node => {
      t.push(node.textContent)
    })
    c.textContent = " " + t.join(" ") + " "
    c.nextElementSibling.remove()
    c.nextElementSibling.remove()
    GUI.updateMarkedUpText();
  }


  static mergeSelection() {
    GUI.saveState()
    let s, r, a, p, c, t
    s = window.getSelection();
    if (!s || !s.rangeCount) {
      return
    }
    s.setBaseAndExtent(s.anchorNode, 0, s.focusNode, s.focusNode.length)
    r = s.getRangeAt(0)
    a = s.anchorNode
    p = a instanceof Text ? a.parentNode : a
    c = p.cloneNode()
    p.parentNode.insertBefore(c, p)
    t = []
    r.extractContents().childNodes.forEach(node => {
      t.push(node.textContent)
    })
    c.textContent = t.join(" ")
    c.nextElementSibling.remove()
    c.nextElementSibling.remove()
    GUI.updateMarkedUpText();
    r
  }

  // not working
  static removeTagsInLines() {
    let startNode = a instanceof Text ? a.parentNode : a;
    while (startNode.previousSibling && startNode.previousSibling.nodeName !== "BR") {
      startNode = startNode.previousSibling;
    }
    let endNode = f instanceof Text ? f.parentNode : f;
    while (endNode.nextSibling && endNode.nextSibling.nodeName !== "BR") {
      endNode = endNode.nextSibling;
    }
    if (startNode && endNode) {
      s.setBaseAndExtent(startNode, 0, endNode, endNode.length);
    }
    let container = document.createElement("div");
    container.appendChild(r.cloneContents());
    let replacementText = container.innerHTML
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.TAG, "")
    GUI.replaceSelection(replacementText);
  }
}

