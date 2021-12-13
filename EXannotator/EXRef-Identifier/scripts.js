// global vars, ugh
let pdfFileName = "";
let pdfFile = null;
let textFileName = "";
let textFileExt = "";
let cols1text = [];
let cols2numbers = [];
let colorCounter = 0;
const pageMarkerPrefix = "[" + "-".repeat(40);
const pageMarkerSuffix = "-".repeat(40) + "]";

const SERVER_URL = "http://127.0.0.1:8000/cgi-bin/";
const LOCAL_STORAGE = {
  MARKED_UP_TEXT: "marked_up_text",
  TEXT_FILE_NAME: "anno2filename",
  PDF_IFRAME_SRC: "excite_pdf_iframe_source"
}


// array for colors definition
const openSpanValues = [
  '<span data-tag="ref" style="background-color: rgb(255, 255, 153);">',
  '<span data-tag="ref" style="background-color: rgb(252, 201, 108);">',
  '<span data-tag="ref" style="background-color: rgb(236, 184, 249);">',
  '<span data-tag="ref" style="background-color: rgb(152, 230, 249);">',
  '<span data-tag="ref" style="background-color: rgb(135, 245, 168);">',
  '<span data-tag="ref" style="background-color: rgb(244, 132, 112);">',
  '<span data-tag="ref" style="background-color: rgb(111, 252, 226);">'];
const spanColors = [
  "#ffff99",
  "#fcc96c",
  "#ecb8f9",
  "#98e6f9",
  "#87f5a8",
  "#f48470",
  "#6ffce2"
];
const otherSpanValue = `<span data-tag="oth" style="background-color: rgb(162, 165, 165);">`
const otherColor = "#a2a5a5";

class Actions {
  static upload() {
    colorCounter = 0;
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
    const validExts = ["pdf", "txt", "csv"];
    for (let file of uploadBtn.files) {
      let filename = file.name;
      let fileExt = filename.split('.').pop();
      if (!validExts.includes(fileExt)) {
        alert(fileExt + " has an invalid type, valid types are [" + validExts.toString() + "].");
        return;
      }
      if (fileExt === 'pdf') {
        $("#pdf-label").html(filename);
        pdfFileName = filename;
        pdfFile = file;
        let tmppath = URL.createObjectURL(file);
        const pdfiframe = $("#pdfiframe");
        pdfiframe.on("load", GUI._onPdfIframeLoaded);
        pdfiframe.prop("src", "web/viewer.html?file=" + tmppath);
        $("#btndelpdf").show();
        GUI.showPdfView(true);
        $("#btn-exparser").prop("disabled", false)
      } else {
        const fileReader = new FileReader();
        fileReader.onload = (e) => {
          let text = String(e.target.result);
          textFileName = filename;
          textFileExt = fileExt;
          document.getElementById("text-label").innerHTML = textFileName;
          localStorage.setItem(LOCAL_STORAGE.MARKED_UP_TEXT, text);
          localStorage.setItem(LOCAL_STORAGE.TEXT_FILE_NAME, textFileName);
          GUI.setTextContent(text);
        }
        fileReader.readAsText(file, "UTF-8");
      }
    }

    if (textFileName && pdfFileName) {
      let textFileNameWithoutExt = textFileName.split('.').slice(0, -1).join(".");
      if (textFileNameWithoutExt !== pdfFileName.substr(0, textFileNameWithoutExt.length)) {
        let message = "Text file and PDF file seem to belong to different documents."
        alert(message);
      }
    }
  }

  static addTag(tag_name, wholeLine = false) {
    let sel = window.getSelection();
    if (sel.toString() === "") return;
    if (wholeLine) {
      sel.setBaseAndExtent(sel.anchorNode, 0, sel.focusNode, sel.focusNode.length);
    }
    // prevent nesting of tags except <oth> in <ref>
    let node = sel.focusNode;
    do {
      if (node && node.dataset) {
        let tag = node.dataset.tag;
        if (tag && !(tag_name === "oth" && tag === "ref")) {
          return;
        }
      }
      node = node.parentNode;
    } while (node)
    let parentNode = document.createElement("span");
    parentNode.setAttribute("data-tag", tag_name);
    let backgroundColor;
    if (tag_name === 'ref') {
      backgroundColor = spanColors[colorCounter];
      colorCounter = ++colorCounter % 6;
    } else {
      backgroundColor = otherColor;
    }
    parentNode.style.backgroundColor = backgroundColor;
    sel.getRangeAt(0).surroundContents(parentNode);
    GUI.updateMarkedUpText()
  }

  static removeTag() {
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

  static checkResult(result) {
    if (result.error) {
      GUI.hideSpinner();
      alert("Error: " + result.error);
      return false;
    }
    if (!result.success) {
      alert("Invalid response.")
      return false;
    }
    return result
  }

  static async run_exparser() {
    if (!confirm("Do you really want to run exparser to identify references in this document?")) {
      return;
    }
    // 1. file upload
    let formData = new FormData();
    formData.append("file", pdfFile);
    GUI.showSpinner("Uploading file...");
    let result = await (await fetch(`${SERVER_URL}/upload.py`, {
      method: 'post',
      body: formData
    })).json();
    if (!this.checkResult(result)) return;
    // 2. layout
    GUI.showSpinner("Analyzing Layout...");
    let filenameNoExt = pdfFileName.split('.').slice(0, -1).join(".");
    let url = `${SERVER_URL}/excite.py?command=layout&file=${filenameNoExt}`
    result = await (await fetch(url)).json();
    if (!this.checkResult(result)) return;
    let layoutDoc = result.success;
    // 3. reference identification
    GUI.showSpinner("Identifying references, this will take a while...");
    url = `${SERVER_URL}/excite.py?command=exparser&file=${filenameNoExt}`
    result = await (await fetch(url)).json();
    GUI.hideSpinner();
    if (!this.checkResult(result)) return;
    let refs = result.success;

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
          // compare ref word with punctuation removed ...
          let refWord = refWords[i].replace(/\p{P}/gu, "").trim();
          // ... with current word without punctuation and without the layout stuff
          let currWord = words[index + i]
            .replace(/\p{P}/gu, "")
            .replace(/(\t[^\t]+){6}/, "")
            .trim();
          // if word contains hyphen, join with next word if exists
          if (currWord.match(/\p{Pd}/gu) && words[index + i + 1]) {
            currWord = currWord + words[index + i + 1]
              .replace(/\p{P}/gu, "")
              .replace(/(\t[^\t]+){6}/, "")
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
    textFileName = pdfFileName.replace(".pdf", ".csv");
    $("#text-label").text(textFileName);
    textFileExt = "csv";
    layoutDoc = words.join(" ").replace(/~~~CR~~~/g, "\n")
    GUI.setTextContent(layoutDoc);
  }

  static export() {
    if (!textFileName) return;
    Utils.download(GUI.getTextToExport(), textFileName);
  }

  static async save() {
    if (!textFileName) return;
    let data = GUI.getTextToExport();
    if (!data.includes("<ref>")) {
      alert("Text contains no markup.");
      return;
    }
    localStorage.setItem(LOCAL_STORAGE.MARKED_UP_TEXT, data);
    localStorage.setItem(LOCAL_STORAGE.TEXT_FILE_NAME, textFileName);
    GUI.showSpinner(`Saving ${textFileName} to training data.`);
    let body = JSON.stringify({
      filename: textFileName,
      type: "layout",
      data
    }) + "\n\n";
    let result = await (await fetch(`${SERVER_URL}/save.py`, {
      method: 'post',
      body
    })).json();
    GUI.hideSpinner();
    if (result.error) alert(result.error);
  }

  static open_in_seganno() {
    this.saveToLocalStorage();
    window.location.href = "../EXRef-Segmentation/index.html";
  }

  static saveToLocalStorage() {
    let text = GUI.getTextToExport();
    localStorage.setItem(LOCAL_STORAGE.MARKED_UP_TEXT, text);
    localStorage.setItem(LOCAL_STORAGE.TEXT_FILE_NAME, textFileName);
    localStorage.setItem(LOCAL_STORAGE.PDF_IFRAME_SRC, document.getElementById("pdfiframe").src);
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


class GUI {

  static init() {

    this.__numPages = 0;
    this.__currentPage = 1;
    this.__currentRefNode = null;
    this.__xmlViewState = true; // will be toggled to off at startup
    this.__pdfJsApplication = null;

    // on page load
    $(document).ready(function () {
      // force remove PDF because loading saved src doesn't work yet
      //document.getElementById("pdfiframe").src = localStorage.getItem(LOCAL_STORAGE.PDF_IFRAME_SRC ) ||'about:blank';
      $("#pdfiframe").prop('src', 'about:blank');

      // hide optional views
      GUI.showPdfView(false);
      GUI.toggleMarkedUpView();

      // disable buttons (on reload)
      $("#btn-exparser").prop("disabled", true);
      $("#btn-export").prop("disabled", true);
      $("#btn-save").prop("disabled", true);
      $("#btn-seganno").prop("disabled", true);

      // get text from local storage
      let markedUpText = localStorage.getItem(LOCAL_STORAGE.MARKED_UP_TEXT);
      if (markedUpText) {
        textFileName = localStorage.getItem(LOCAL_STORAGE.TEXT_FILE_NAME)
        document.getElementById("text-label").innerHTML = textFileName;
        GUI.setTextContent(markedUpText);
      } else {
        $("#modal-help").show();
      }

      // long-pressing selects span
      $(document).ready(() => {
        let longpress = false;
        $(document).on('click', e => {
          if (!longpress) return;
          let sel = window.getSelection();
          if (sel.toString().length) return; // so that <oth> element can be inserted into selection
          if (!sel.focusNode || !sel.focusNode.parentElement) return;
          let p = sel.focusNode.parentElement;
          if (e.target !== p) return;
          if (p.dataset && p.dataset.tag) {
            sel.removeAllRanges();
            let range = document.createRange();
            range.selectNodeContents(p);
            sel.addRange(range)
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
      });

      // show popup on select
      $(document).ready(() => {
        const contextMenu = $("#contextMenu");
        const contentLabel = $("#text-content");
        contentLabel.on("pointerup", GUI._showPopupOnSelect);
        contextMenu.on("pointerup", () => setTimeout(() => {
          contextMenu.hide();
          window.getSelection().removeAllRanges();
        }, 100));
      })

      // synchronize scroll positions
      $('#text-content').on('scroll', e => {
        $('#markup-content-container').scrollTop(e.currentTarget.scrollTop);
      });

      // save text before leaving the page
      window.onbeforeunload = Actions.saveToLocalStorage;

      // check if we have a backend
       fetch(SERVER_URL + "status.py")
         .then(response => response.json())
         .then(result => {
           if (result.success) {
      $("#btn-exparser").removeClass("hidden");
      $("#btn-save").removeClass("hidden");
         }
      })
    });
  }

  static showSpinner(text) {
    $("#spinner").attr("data-text", text).addClass("is-active");
  }

  static hideSpinner() {
    $("#spinner").removeClass("is-active");
  }


  static removeTextFile() {
    $("#text-label").html("");
    $("#text-content").html("");
    $("#markup-content").html("");
    $(".view-text-buttons").hide();

    textFileName = "";
    cols2numbers = [];
    localStorage.removeItem(LOCAL_STORAGE.TEXT_FILE_NAME);
    localStorage.removeItem(LOCAL_STORAGE.MARKED_UP_TEXT);
    $("#btn-export").prop("disabled", true);
    $("#btn-save").prop("disabled", true);
    $("#btn-seganno").prop("disabled", true);
  }

  static removePdfFile() {
    $("pdf-label").html("");
    $("#btndelpdf").hide();
    document.getElementById("pdfiframe").src = 'about:blank';
    pdfFileName = "";
    $("#btn-exparser").prop("disabled", true);
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

  static setTextContent(text) {
    let text_Lines = text
      .replace(/\r/g, "")
      .replace(/\n\n/g, '\n')
      .replace(/\n\n/g, '\n')
      .split('\n')
      .map(line => line.trim());
    let tagged_text = "";
    let yval = 0;
    this.__numPages = 0;
    for (let i = 0; i < text_Lines.length; i++) {
      if (textFileName.endsWith(".csv")) {
        // we have layout info in the file, remove from text to re-add later
        let line_parts = text_Lines[i].split('\t');
        if (line_parts.length >= 7) {
          let layout_info = line_parts.slice(-6);
          let text_content = line_parts.slice(0, -6).join(' ');
          cols2numbers[i] = layout_info.join('\t');
          cols1text[i] = text_content;
          let lineYval = layout_info[1];
          if (yval === 0 || yval - lineYval > 300) {
            this.__numPages++;
            cols1text[i] = `<div class="page-marker" data-page="${this.__numPages}"></div>\n` + cols1text[i];
          }
          yval = lineYval;
        } else {
          cols1text[i] = text_Lines[i];
        }
      } else {
        cols1text[i] = text_Lines[i];
      }
      if (i === text_Lines.length - 1) {
        tagged_text = tagged_text + cols1text[i];
      } else {
        tagged_text = tagged_text + cols1text[i] + '<br>';
      }
    }
    if (this.__numPages > 0) {
      $("#label-page-number").html("1");
      $("#page-navigation").show();
    } else {
      $("#label-page-number").html("");
      $("#page-navigation").hide();
    }
    let html = tagged_text;
    while (html.indexOf("<ref>") !== -1) {
      html = html.replace("</ref>", "</span>");
      html = html.replace('<ref>', openSpanValues[colorCounter]);
      colorCounter = ++colorCounter % 6;
    }
    while (html.indexOf("<oth>") !== -1) {
      html = html.replace("</oth>", "</span>");
      html = html.replace('<oth>', otherSpanValue);
    }
    $("#text-content").html(html);
    $("#text-content").scrollTop(0);
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
    $("#btn-seganno").prop("disabled", false);
    $("#btn-save").prop("disabled", false);
    $("#btn-export").prop("disabled", false);
  }

  static updateMarkedUpText() {
    let regex1 = /<span data-tag="oth".*?>(.+?)<\/span>/g;
    let regex2 = /<span data-tag="ref".*?>(.+?)<\/span>/g;
    let markedUpText = $("#text-content").html()
      .replace(/<div class="page-marker"[^>]*><\/div>\n/g, "")
      .replace(regex1, "<oth>$1</oth>")
      .replace(regex2, "<ref>$1</ref>")
      .replace(/<br>/g, "\n")
      .replace(/</g, "&lt;");
    $("#markup-content").html(markedUpText)
    return markedUpText;
  }

  static getTextToExport() {
    GUI.updateMarkedUpText();
    let markedUpText = $("#markup-content").html();
    let t1 = markedUpText.split('\n')
    let t2 = [];
    let rowFirstColumn = '';
    let allFirstColumns = '';
    let start = '<ref>'
    let suffix = '</ref>'
    let other_suffix = '</oth>'
    for (let i = 0; i < t1.length; i++) {
      rowFirstColumn = t1[i];
      // add one space to the end of line if it is multi line ref and doesn't have hyphen or dash at end
      if (!(rowFirstColumn.substr(-suffix.length) === suffix) || (rowFirstColumn.substr(-other_suffix.length) === other_suffix))
        if (!(rowFirstColumn.substr(-1) === '-'))
          if (!(rowFirstColumn.substr(-1) === '.'))
            rowFirstColumn = rowFirstColumn + ' ';
      allFirstColumns = allFirstColumns + rowFirstColumn;
      // textToWrite2 is all layout with numbers
      if (i === t1.length - 1) {
        // no \n for last line
        if (typeof cols2numbers[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + cols2numbers[i];
        } else {
          t2[i] = t1[i] + '\n'
        }
      } else {
        if (typeof cols2numbers[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + cols2numbers[i] + '\n';
        } else {
          t2[i] = t1[i] + '\n'
        }
      }
    }
    // clean up
    t2 = t2.join("")
      .replace(/&amp;/g, "&")
      .replace(/&gt;/g, ">")
      .replace(/&lt;/g, "<")
      .replace(/&quot;/g, '"')
      .replace(/&pos;/g, "'")
      .replace(/&nbsp;/g, " ")
      .trim();
    // return sanitized text
    return t2;
  }

  static toggleMarkedUpView() {
    let state = this.__xmlViewState = !this.__xmlViewState;
    $(".view-markup")[state ? "show" : "hide"]();
    document.getElementById("main-container")
      .style.gridTemplateRows = this.__xmlViewState ? "50% 50%" : "100% 0"
  }

  static showPdfView(state) {
    $(".view-pdf")[state ? "show" : "hide"]();
    document.getElementById("main-container")
      .style.gridTemplateColumns = state ? "50% 50%" : "100% 0"
  }

  static _showPopupOnSelect(e) {
    const contextMenu = $("#contextMenu");
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
    $("#btn-ref-part").toggleClass("ui-state-disabled", Boolean(tag));
    $("#btn-ref-line").toggleClass("ui-state-disabled", Boolean(tag));
    $("#btn-oth").toggleClass("ui-state-disabled", !Boolean(tag) || tag === "oth");
    $("#btn-remove-tag").toggleClass("ui-state-disabled", !Boolean(tag));
    if (!sel.toString().trim()) {
      contextMenu.hide();
      return;
    }
    contextMenu
      .show()
      .css({
        position: "absolute",
        left: e.pageX,
        top: e.pageY
      });
  }

  static _onPdfIframeLoaded() {
    setTimeout(() => {
      GUI.__pdfJsApplication = window.frames[0].PDFViewerApplication;
      GUI.__pdfJsApplication.eventBus.on('pagechanging', GUI._onPdfPageChanging);
    }, 100)
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
    if (pageMarker) {
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

}

// start
GUI.init();
