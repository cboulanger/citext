let textLines = [];
let currentLine = 0;
let filename;
let fileExt;

const SERVER_URL = "http://127.0.0.1:8000/cgi-bin/";
const LOCAL_STORAGE = {
  DOCUMENT: "excite_document",
  REFERENCES: "excite_references",
  TEXT_FILE_NAME: "excite_text_file_name",
  LAST_FILE_NAME: "excite_last_file_name"
}
const REGEX = {
  TAG: /<\/?[^>]+>/g,
  SPAN: /<\/?span[^>]*>/ig,
  DIV: /<\/?div[^>]*>/ig,
  BR: /<br[^>]*>/ig,
  PUNCTUATION: /\p{P}/gu,
  LAYOUT: /(\t[^\t]+){6}/g,
  EMPTY_NODE: /<[^>]+><\/[^>]+>/g
};

function emptyParameters() {
  textLines = [];
  currentLine = 0;
  filename = "";
  fileExt = "";
  document.getElementById("txaxml").value = "";
  document.getElementById("lblColoredText").innerHTML = "";
  document.getElementById("demo").innerHTML = "";
}

$(document).ready(loadSession);

// long-pressing selects span
$(document).ready(function () {
  let longpress = false;

  $(document).on('click', e => {
    if (!longpress) return;
    let sel = window.getSelection();
    if (!sel.focusNode || !sel.focusNode.parentElement) return;
    let p = sel.focusNode.parentElement;
    if (e.target !== p) return;
    if (p.dataset && p.dataset.tag) {
      sel.removeAllRanges();
      let range = document.createRange();
      range.selectNodeContents(p);
      sel.addRange(range)
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

//load last saved localstorage
function loadSession() {
  let lastDocument = localStorage.getItem(LOCAL_STORAGE.DOCUMENT);
  let lastReferences = localStorage.getItem(LOCAL_STORAGE.REFERENCES);
  let textFileName = localStorage.getItem(LOCAL_STORAGE.TEXT_FILE_NAME);
  let lastFileName = localStorage.getItem(LOCAL_STORAGE.LAST_FILE_NAME);
  let fileToLoad;
  if (textFileName) {
    let filenparts = textFileName.split(".");
    filename = filenparts.slice(0, -1).join(".");
    fileExt = filenparts.pop();
  }
  // saved xml has priority if filename hasn't changed
  if (lastReferences && (filename === lastFileName || !lastFileName)) {
    fileToLoad = new Blob([lastReferences], {type: 'text/xml'});
  } else if (lastDocument) {
    fileToLoad = new Blob([lastDocument], {type: 'text/csv'});
  }
  if (fileToLoad) {
    loadFile(fileToLoad);
  }
}

//saved the last changes before closeing
window.onbeforeunload = function () {
  savelocalStorage();
}

function showSpinner(text) {
  $("#spinner").attr("data-text", text).addClass("is-active");
}

function hideSpinner() {
  $("#spinner").removeClass("is-active");
}

function savelocalStorage() {
  let xmlText = getXmlText();
  if (xmlText) {
    localStorage.setItem(LOCAL_STORAGE.REFERENCES, xmlText);
  }
}

async function saveToFilesystem() {
  let data = getXmlText();
  if (!data || !filename) return;
  savelocalStorage();
  showSpinner(`Saving ${filename}.xml to training data.`);
  let body = JSON.stringify({
    filename: `${filename}.xml`,
    type: "ref_xml",
    data
  }) + "\n\n";
  let result = await (await fetch(`${SERVER_URL}/save.py`, {
    method: 'post',
    body
  })).json();
  hideSpinner();
  if (result.error) alert(result.error);
}

function goToRefAnno() {
  window.location.href = "../EXRef-Identifier/index.html";
}

function checkfile() {
  const btnLoadFile = document.getElementById("btnUploadfile");
  emptyParameters();
  const fileToLoad = btnLoadFile.files[0];
  filename = fileToLoad.name.split('.').slice(0, -1).join(".");
  fileExt = fileToLoad.name.split('.').pop();
  if (!["xml", "txt", "csv"].includes(fileExt)) {
    alert("Only .xml, csv or .txt files allowed.");
    return false;
  }
  loadFile(fileToLoad);
  return true;
}

function loadFile(fileToLoad) {
  const fileReader = new FileReader();
  fileReader.onload = function (evt) {
    let text = evt.target.result;
    textLines = text
      .replace(/\r/g, "")
      .split('\n')
      .filter(String); // remove empty lines

    if (fileExt === "xml" || text.includes("<author>")) {
      if (textLines[0].includes("<?xml ")) {
        // if standard-compliant xml, remove declaration and top node
        textLines.splice(0, 2);
        textLines.splice(-1, 1);
        // remove enclosing <ref> tags
        textLines = textLines
          .map(line => line
            .replace(/<author>/g, '')
            .replace(/<\/author>/g, '')
            .replace(/<ref>/g, '')
            .replace(/<\/ref>/g, ''));
      }
    } else {
      // csv or txt
      if (fileExt === "csv") {
        // remove cermine layout info if exists
        textLines = textLines.map(line => line.split('\t').shift())
      }
      let tmp = textLines
        .map(line => line.trim().replace(/[-]$/, "~~HYPHEN~~"))
        .join(" ")
        .replace(/~~HYPHEN~~ /g, "")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">");
      textLines = [];
      for (let match of tmp.matchAll(/<ref>(.*?)<\/ref>/g)) {
        textLines.push(match[1]);
      }
    }
    if (textLines.length === 0) {
      alert("No reference content!");
      return;
    }
    // display first reference
    document.getElementById("demo").innerHTML = `${filename}: ${textLines.length} references`;
    document.getElementById("lblColoredText").innerHTML = textLines[0];
    document.getElementById("txaxml").value = textLines[0];
    document.getElementById("count").innerHTML = 1 + "/" + textLines.length;
    updateHtmlText();
    updateMarkedUpText();
    // save current filename
    localStorage.setItem(LOCAL_STORAGE.LAST_FILE_NAME, filename);
  };
  fileReader.readAsText(fileToLoad, "UTF-8");
}

function exportFile() {
  if (document.getElementById("txaxml").value) {
    let fileNameToSaveAs = filename + ".xml";
    let xml = getXmlText();
    download(xml, fileNameToSaveAs);
  }
}

function reset() {
  localStorage.setItem(LOCAL_STORAGE.REFERENCES, null);
  emptyParameters();
  loadSession();
}

function getXmlText() {
  if (!document.getElementById("txaxml").value) {
    return "";
  }
  // save currently edited reference
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  // re-add <author> tag
  for (i = 0; i < textLines.length; i++) {
    if (textLines[i].indexOf('<author>') < 0) {
      textLines[i] = addAuthorTag(textLines[i]);
    }
  }
  // Rejoin the line, adding a <ref> tag, and replace special chars
  let xml = textLines
    .map(line => `<ref>${line}</ref>`)
    .join("\n")
    .replace(/(&amp;)/gm, "&")
    .replace(/(&gt;)/gm, ">")
    .replace(/(&lt;)/gm, "<")
    .replace(/(&quot;)/gm, '"')
    .replace(/(&pos;)/gm, "'");

  // create valid xml
  return `<?xml version="1.0" encoding="utf-8"?>\n<seganno>\n${xml}\n</seganno>`;
}

function download(data, filename1) {
  let file = new Blob([data], {type: 'text/xml'});
  let a = document.createElement("a"),
    url = URL.createObjectURL(file);
  a.href = url;
  a.download = filename1;
  document.body.appendChild(a);
  a.click();
  setTimeout(function () {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 0);
}

//Navigate between Lines/////////////////////////////////////
function goto_firstLine() {
  // Save the current txaxml content into arrayOfLines[currentLine] to keep changes.
  // replace \n at the end of line
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  currentLine = 0;
  updateUI();
}

function goto_prevLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  if (currentLine > 0)
    currentLine = currentLine - 1;
  else
    currentLine = textLines.length - 1;
  updateUI();
}

function goto_lastLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  currentLine = textLines.length - 1;
  updateUI();
}

function goto_nextLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  if (textLines.length - 1 > currentLine)
    currentLine = currentLine + 1;
  else currentLine = 0;
  updateUI();
}

function updateUI() {
  document.getElementById("lblColoredText").innerHTML = textLines[currentLine];
  document.getElementById("txaxml").value = textLines[currentLine];
  document.getElementById("count").innerHTML = (currentLine + 1) + "/" + textLines.length;
  updateHtmlText();
  updateMarkedUpText();
}

document.addEventListener('keydown', function (event) {
  // alert(event.keyCode);
  sel = window.getSelection();
  var selectedtext = sel.toString();
  if (selectedtext === '')
    return;
  if (event.keyCode === 65) {
    // alert('a was pressed');
    addTag('btnauthor');
  } else if (event.keyCode === 69) {
    // alert('e was pressed');
    addTag('btneditor');
  } else if (event.keyCode === 71) {
    // alert('g was pressed');
    addTag('btngiven-names');
  } else if (event.keyCode === 83) {
    // alert('s was pressed');
    addTag('btnsurname');
  } else if (event.keyCode === 86) {
    // alert('v was pressed');
    addTag('btnvolume');
  } else if (event.keyCode === 89) {
    // alert('y was pressed');
    addTag('btnyear');
  } else if (event.keyCode === 84) {
    // alert('t was pressed');
    addTag('btntitle');
  } else if (event.keyCode === 79) {
    // alert('o was pressed');
    addTag('btnsource');
  } else if (event.keyCode === 70) {
    // alert('f was btnfpage');
    addTag('btnfpage');
  } else if (event.keyCode === 76) {
    // alert('l was btnlpage');
    addTag('btnlpage');
  } else if (event.keyCode === 80) {
    // alert('pp was btnpublisher');
    addTag('btnpublisher');
  } else if (event.keyCode === 72) {
    // alert('hh was pressed');
    addTag('btnother');
  } else if (event.keyCode === 68) {
    // alert('dd was pressed');
    addTag('btnidentifier');
  } else if (event.keyCode === 73) {
    // alert('ii was pressed');
    addTag('btnissue');
  } else if (event.keyCode === 85) {
    // alert('uu was pressed');
    addTag('btnurl');
  } else if (event.keyCode === 82) {
    // alert('rr was pressed');
    removeTag();
  }
});

function addTag(sender) {
  let coloredText = document.getElementById("lblColoredText").innerHTML;
  if (coloredText === "") {
    return;
  }
  let tag_name;
  if (sender.value) {
    tag_name = sender.value.replace("btn", "");
  } else {
    tag_name = sender.replace("btn", "");
  }
  let sel = window.getSelection();
  let text = sel.toString();
  if (text.trim() === "") return;
  // prevent nesting of tag inside other tag
  let node = sel.focusNode;
  do {
    if (node && node.dataset) {
      let tag = node.dataset.tag;
      if (tag) {
        // replace node tag
        node.dataset.tag = tag_name;
        updateMarkedUpText();
        return;
      }
    }
    node = node.parentNode;
  } while (node)
  // wrap selection in new span
  let parentNode = document.createElement("span");
  parentNode.setAttribute("data-tag", tag_name);
  sel.getRangeAt(0).surroundContents(parentNode);
  // remove all <span>s from selected text
  $(parentNode).html($(parentNode).html().replace(REGEX.SPAN, ""));
  updateMarkedUpText();
}

function updateMarkedUpText() {
  let coloredText = document.getElementById("lblColoredText").innerHTML;
  let regex2 = /<span data-tag="([^"]+)".*?>(.+?)<\/span>/g;
  let xmlText = coloredText
    .replace(regex2, "<$1>$2</$1>")
  xmlText = addAuthorTag(xmlText);
  document.getElementById("txaxml").value = xmlText;
}

function updateHtmlText() {
  let tmp = document.getElementById("txaxml").value
    .replace(/<author>/g, "")
    .replace(/<\/author>/g, "");
  // translate tag names to data-tag attributes
  let tag_names = [];
  let tag_name;
  for (let match of tmp.matchAll(/<([a-z_\-]+)>/g)) {
    tag_name = match[1];
    if (!tag_names.includes(tag_name)) {
      tag_names.push(tag_name);
    }
  }
  for (tag_name of tag_names) {
    let regex = new RegExp(`<${tag_name}>(.*?)</${tag_name}>`, 'g');
    let replacement = `<span data-tag="${tag_name}">$1</span>`;
    tmp = tmp.replace(regex, replacement);
  }
  document.getElementById("lblColoredText").innerHTML = tmp;
}

function addAuthorTag(markedUpText) {
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
          continue;
        }
        if (secondStartTagMatch === null) {
          if (tag !== firstStartTagMatch[0]) {
            // if the second opening tag is not the same as the first, remember it and go on
            secondStartTagMatch = match;
            continue;
          }
          // tag repeats
        }
      } else {
        // closing tag
        lastEndTagMatch = match;
        if (!secondStartTagMatch || tagName !== secondStartTagMatch[1]) {
          continue;
        }
      }
      // insert </author> after the last closing tag
      pos = lastEndTagMatch.index + offset + lastEndTagMatch[0].length;
      markedUpText = markedUpText.substr(0, pos) + endTag + markedUpText.substr(pos);
      offset += endTag.length;
      if (!tag.startsWith("</")) {
        // insert new opening tag
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

function removeTag() {
  let sel = window.getSelection();
  if (!sel) return;
  let el = sel.focusNode;
  while (el) {
    if (el.dataset && el.dataset.tag) break;
    el = el.parentElement;
  }
  if (!el) return;
  $(el).contents().unwrap();
  updateMarkedUpText();
}

function removeAllTags() {
  document.getElementById("lblColoredText").innerHTML =
    document.getElementById("lblColoredText").innerHTML
      .replace(/<\/?span[^>]*>/g, "");
  updateMarkedUpText();
}

// from https://stackoverflow.com/a/62125595
function fix_selection(range) {
  var selection = window.getSelection();
  var selected = range.toString();
  range = selection.getRangeAt(0);
  let start = selection.anchorOffset;
  let end = selection.focusOffset;
  if (!selection.isCollapsed) {
    if (/\s+$/.test(selected)) { // Removes leading spaces
      if (start > end) {
        range.setEnd(selection.focusNode, --start);
      } else {
        range.setEnd(selection.anchorNode, --end);
      }
    }
    if (/^\s+/.test(selected)) { // Removes trailing spaces
      if (start > end) {
        range.setStart(selection.anchorNode, ++end);
      } else {
        range.setStart(selection.focusNode, ++start);
      }
    }
  }
  return range
}
